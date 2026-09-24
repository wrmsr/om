"""
Serving: an OpenAI chat-completions endpoint over `Qwen35.generate` and `PrefixCache`.

`Engine` owns the model, its compiled steps, the prefix cache and one worker thread; requests queue up (a small bounded
queue is all the admission control one user needs) and run one at a time. Each request renders the conversation with
`chat.render_chat` (tools, tool results, reasoning kept in every turn so the rendered history -- and with it the prefix
cache -- stays stable), tokenises it, resumes from the longest cached prefix, and streams tokens back through a
`chat.StreamParser` as reasoning / content / tool-call deltas.

Two details that make the prefix cache actually hit across turns: the ids of every answer this server produced are
memoised under the exact assistant-turn string it renders to, and substituted when that turn comes back in a later
request's history (BPE re-tokenisation of generated text is not guaranteed to reproduce the generated ids); and answers
are rendered the same way in every position (`preserve_thinking`).

Cancellation: a streaming client that goes away is noticed on the next write, the job is flagged, and `generate` stops
at its next round (or prefill chunk) through `should_stop`. Non-streaming clients cannot be observed until the final
write.

`ChatServer` is the HTTP side on the standard library: POST /v1/chat/completions (streaming as SSE), GET /v1/models, GET
/health. The dialect is OpenAI's, with `reasoning_content` on messages and deltas, `top_k` and `chat_template_kwargs:
{enable_thinking}` as extensions, and `usage.prompt_tokens_reused` reporting the cache.
"""
import http.server
import json
import queue
import select
import socket
import sys
import threading
import time
import typing as ta
import uuid

from omcore import dataclasses as dc

from .chat import StreamParser
from .chat import parse_output
from .chat import render_assistant_turn
from .chat import render_chat
from .model import Cancelled
from .model import Qwen35
from .model import Sampler
from .prefixcache import PrefixCache
from .tokenizer import Tokenizer


##


@dc.dataclass()
class SamplingDefaults:
    temperature: float = 1.0
    top_k: int = 20
    top_p: float = 0.95
    min_p: float = 0.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    max_tokens: int = 4096


@dc.dataclass()
class Request:
    messages: list[dict]
    tools: list[dict] | None
    stream: bool
    max_tokens: int
    temperature: float
    top_k: int
    top_p: float
    min_p: float
    presence_penalty: float
    frequency_penalty: float
    seed: int | None
    stop: list[str]
    enable_thinking: bool
    model: str | None = None

    @classmethod
    def from_json(cls, body: dict, defaults: SamplingDefaults, enable_thinking: bool) -> Request:
        msgs = body.get('messages')
        if not isinstance(msgs, list) or not msgs:
            raise ValueError('messages must be a non-empty list')
        stop = body.get('stop') or []
        if isinstance(stop, str):
            stop = [stop]
        kw = body.get('chat_template_kwargs') or {}
        think = body.get('enable_thinking', kw.get('enable_thinking', enable_thinking))
        mt = body.get('max_completion_tokens', body.get('max_tokens', defaults.max_tokens))
        return cls(
            messages=msgs,
            tools=body.get('tools') or None,
            stream=bool(body.get('stream', False)),
            max_tokens=max(1, int(mt)),
            temperature=float(body.get('temperature', defaults.temperature)),
            top_k=int(body.get('top_k', defaults.top_k)),
            top_p=float(body.get('top_p', defaults.top_p)),
            min_p=float(body.get('min_p', defaults.min_p)),
            presence_penalty=float(body.get('presence_penalty', defaults.presence_penalty)),
            frequency_penalty=float(body.get('frequency_penalty', defaults.frequency_penalty)),
            seed=None if body.get('seed') is None else int(body['seed']),
            stop=[str(s) for s in stop],
            enable_thinking=bool(think),
            model=body.get('model'),
        )


@dc.dataclass()
class Result:
    text: str
    ids: list[int]
    content: str
    reasoning: str | None
    tool_calls: list[dict]
    finish_reason: str
    prompt_tokens: int
    prompt_reused: int
    completion_tokens: int
    prefill_s: float
    total_s: float
    spec_rounds: int
    spec_accepted: int


class Job:
    """One request in flight: the engine pushes events into `events`; a handler drains them."""

    def __init__(self, req: Request) -> None:
        self.req = req
        self.id = 'chatcmpl-' + uuid.uuid4().hex[:24]
        self.created = int(time.time())
        self.events: queue.Queue = queue.Queue()  # ('delta', kind, payload) | ('done', Result) | ('error', str)
        self.cancelled = False
        self.result: Result | None = None
        self.error: str | None = None

    def cancel(self) -> None:
        self.cancelled = True


class Busy(Exception):  # noqa
    pass


class Engine:
    def __init__(
            self,
            model: Qwen35,
            tok: Tokenizer,
            *,
            spec: int = 0,
            draft_vocab: int = 0,
            capacity: int | None = None,
            prefix_cache: PrefixCache | None = None,
            defaults: SamplingDefaults | None = None,
            enable_thinking: bool = True,
            preserve_thinking: bool = True,
            max_queue: int = 4,
            prefill_chunk: int = 4096,
            model_name: str = 'qwen',
            log: ta.Callable[[str], None] | None = print,
    ) -> None:
        self.model = model
        self.tok = tok
        self.spec = spec
        self.draft_vocab = draft_vocab
        self.capacity = capacity
        self.prefix_cache = prefix_cache
        self.defaults = defaults or SamplingDefaults()
        self.enable_thinking = enable_thinking
        self.preserve_thinking = preserve_thinking
        self.prefill_chunk = prefill_chunk
        self.model_name = model_name
        self.log = log
        self.eos = {
            i
            for i in (
                tok.eos_id,
                tok.special.get('<|im_end|>'),
                tok.special.get('<|endoftext|>'),
            )
            if i is not None
        }
        self.im_end = tok.special.get('<|im_end|>')
        self.queue: queue.Queue = queue.Queue(maxsize=max_queue)
        self.answer_ids: dict[str, list[int]] = {}  # rendered assistant turn -> the ids that produced it
        self.answer_order: list[str] = []
        self.n_requests = 0
        self.n_cancelled = 0
        self.n_errors = 0
        self.running: Job | None = None
        self.thread = threading.Thread(target=self._worker, name='qwen-engine', daemon=True)
        self.thread.start()

    # prompts

    def render(self, req: Request) -> str:
        return render_chat(
            req.messages,
            req.tools,
            add_generation_prompt=True,
            enable_thinking=req.enable_thinking,
            preserve_thinking=self.preserve_thinking,
        )

    def encode_prompt(self, text: str) -> list[int]:
        """
        Tokenise a rendered prompt, substituting the memoised ids of assistant turns this server produced. Turns are
        delimited by special tokens, across which BPE never merges, so encoding the pieces separately equals encoding
        the whole; the substitution is what keeps a later request's ids an exact extension of the earlier request's ids
        + its answer's ids.
        """

        ids: list[int] = []
        rest = text
        while rest:
            best: tuple[int, str] | None = None
            for seg in self.answer_ids:
                at = rest.find(seg)
                if at >= 0 and (best is None or at < best[0]):
                    best = (at, seg)
            if best is None:
                ids.extend(self.tok.encode(rest))
                break
            at, seg = best
            if at:
                ids.extend(self.tok.encode(rest[:at]))
            ids.extend(self.answer_ids[seg])
            rest = rest[at + len(seg):]
        return ids

    def _remember_answer(self, gen_prompt_ids: list[int], out_ids: list[int], msg: dict) -> None:
        seg = render_assistant_turn(msg, with_reasoning=True if self.preserve_thinking else None)
        ids = list(gen_prompt_ids) + list(out_ids)
        if self.im_end is not None and (not ids or ids[-1] != self.im_end):
            ids.append(self.im_end)
        ids.extend(self.tok.encode('\n'))
        if seg in self.answer_ids:
            self.answer_order.remove(seg)
        self.answer_ids[seg] = ids
        self.answer_order.append(seg)
        while len(self.answer_order) > 64:
            del self.answer_ids[self.answer_order.pop(0)]

    # requests

    def submit(self, req: Request) -> Job:
        job = Job(req)
        try:
            self.queue.put_nowait(job)
        except queue.Full:
            raise Busy from None
        return job

    def run_sync(self, req: Request) -> Result:
        """Submit and wait (for tests and the CLI client)."""

        job = self.submit(req)
        while True:
            ev = job.events.get()
            if ev[0] == 'done':
                return ev[1]
            if ev[0] == 'error':
                raise RuntimeError(ev[1])

    def _worker(self) -> None:
        while True:
            job = self.queue.get()
            if job.cancelled:
                job.events.put(('error', 'cancelled'))
                continue
            self.running = job
            try:
                self._run(job)
            except Cancelled:
                self.n_cancelled += 1
                job.events.put(('error', 'cancelled'))
            except Exception as e:  # noqa
                self.n_errors += 1
                job.error = f'{type(e).__name__}: {e}'
                job.events.put(('error', job.error))
                if self.log:
                    import traceback

                    self.log('[serve] request failed:\n' + traceback.format_exc())
            finally:
                self.running = None

    def idle(self) -> bool:
        return self.running is None and self.queue.empty()

    def _run(self, job: Job) -> None:
        req = job.req
        model = self.model
        tok = self.tok
        self.n_requests += 1
        t0 = time.time()
        text = self.render(req)
        ids = self.encode_prompt(text)
        # the generation prompt's own ids (the tail after the last '<|im_start|>assistant'), for the answer memo
        tail_text = text[text.rfind('<|im_start|>assistant'):]
        gen_prompt_ids = tok.encode(tail_text)

        sampler = Sampler(
            temperature=req.temperature,
            top_k=req.top_k,
            top_p=req.top_p,
            min_p=req.min_p,
            presence_penalty=req.presence_penalty,
            frequency_penalty=req.frequency_penalty,
            seed=req.seed if req.seed is not None else int(time.time_ns() % (1 << 31)),
        )
        streamer = Tokenizer.Streamer(tok)
        parser = StreamParser()
        out_ids: list[int] = []
        pieces: list[str] = []
        first_token: list[float] = []
        stopped_at: list[int] = []  # text length at which a stop sequence completed

        def deliver(events: list[tuple[str, ta.Any]]) -> None:
            for kind, payload in events:
                job.events.put(('delta', kind, payload))

        def on_token(i: int) -> None:
            if job.cancelled:
                raise Cancelled
            if not first_token:
                first_token.append(time.time() - t0)
            out_ids.append(i)
            piece = streamer.push(i)
            if piece:
                pieces.append(piece)
                if req.stop:
                    whole = ''.join(pieces)
                    for s in req.stop:
                        at = whole.find(s, max(0, len(whole) - len(piece) - len(s)))
                        if at >= 0:
                            stopped_at.append(at)
                            deliver(parser.feed(piece[:max(0, len(piece) - (len(whole) - at))]))
                            raise Cancelled
                if req.stream:
                    deliver(parser.feed(piece))

        try:
            model.generate(
                ids,
                max_new_tokens=req.max_tokens,
                eos_ids=self.eos,
                on_token=on_token,
                sampler=sampler,
                spec=self.spec,
                capacity=self.capacity,
                draft_vocab=self.draft_vocab,
                prefix_cache=self.prefix_cache,
                prefill_chunk=self.prefill_chunk,
                should_stop=lambda: job.cancelled,
            )
        except Cancelled:
            if not stopped_at:
                raise
        piece = streamer.flush()
        if piece:
            pieces.append(piece)
            if req.stream:
                deliver(parser.feed(piece))
        full = ''.join(pieces)
        if stopped_at:
            full = full[:stopped_at[0]]
        parsed = parse_output(full)
        if req.stream:
            deliver(parser.finish())
        if parsed.tool_calls:
            finish = 'tool_calls'
        elif stopped_at or (out_ids and out_ids[-1] in self.eos):
            finish = 'stop'
        else:
            finish = 'length'
        matched, total = model.last_prefix
        sd = model.last_spec if self.spec else None
        res = Result(
            text=full,
            ids=out_ids,
            content=parsed.content,
            reasoning=parsed.reasoning,
            tool_calls=parsed.tool_calls,
            finish_reason=finish,
            prompt_tokens=len(ids),
            prompt_reused=matched,
            completion_tokens=len(out_ids),
            prefill_s=first_token[0] if first_token else time.time() - t0,
            total_s=time.time() - t0,
            spec_rounds=sd.rounds if sd is not None else 0,
            spec_accepted=sd.accepted if sd is not None else 0,
        )
        if not stopped_at:  # (a stop-truncated answer's ids would carry text the rendered turn does not)
            msg = {
                'role': 'assistant',
                'content': parsed.content,
                'reasoning_content': parsed.reasoning or '',
            }
            if parsed.tool_calls:
                msg['tool_calls'] = parsed.tool_calls  # type: ignore[assignment]
            self._remember_answer(gen_prompt_ids, out_ids, msg)
        job.result = res
        job.events.put(('done', res))
        if self.log:
            rate = res.completion_tokens / max(1e-9, res.total_s - res.prefill_s)
            spec = ''
            if sd is not None and sd.rounds:
                spec = f', spec {sd.accepted / (sd.rounds * self.spec):.0%}'
            pc = f'; cache {self.prefix_cache.stats()}' if self.prefix_cache is not None else ''
            self.log(
                f'[serve] {job.id}: {res.prompt_tokens} prompt ({res.prompt_reused} reused), '
                f'{res.completion_tokens} generated, prefill {res.prefill_s:.2f}s, {rate:.1f} tok/s, '
                f'{res.finish_reason}{spec}{pc}',
            )

    # openai shapes

    def message_json(self, res: Result) -> dict:
        m: dict = {
            'role': 'assistant',
            'content': res.content or None,
        }
        if res.reasoning:
            m['reasoning_content'] = res.reasoning
        if res.tool_calls:
            m['tool_calls'] = res.tool_calls
        return m

    def completion_json(self, job: Job, res: Result) -> dict:
        return {
            'id': job.id,
            'object': 'chat.completion',
            'created': job.created,
            'model': self.model_name,
            'choices': [{
                'index': 0,
                'message': self.message_json(res),
                'finish_reason': res.finish_reason,
            }],
            'usage': {
                'prompt_tokens': res.prompt_tokens,
                'completion_tokens': res.completion_tokens,
                'total_tokens': res.prompt_tokens + res.completion_tokens,
                'prompt_tokens_reused': res.prompt_reused,
            },
        }

    def chunk_json(
            self,
            job: Job,
            delta: dict,
            finish: str | None = None,
            usage: dict | None = None,
    ) -> dict:
        d: dict = {
            'id': job.id,
            'object': 'chat.completion.chunk',
            'created': job.created,
            'model': self.model_name,
            'choices': [{
                'index': 0,
                'delta': delta,
                'finish_reason': finish,
            }],
        }
        if usage is not None:
            d['usage'] = usage
        return d


##


class ChatServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr: tuple[str, int], engine: Engine) -> None:
        super().__init__(addr, Handler)
        self.engine = engine


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):  # quiet
        pass

    @property
    def engine(self) -> Engine:
        return self.server.engine  # type: ignore[attr-defined]

    def _json(self, code: int, obj: ta.Any) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        eng = self.engine
        if self.path.startswith('/v1/models'):
            self._json(200, {
                'object': 'list',
                'data': [{
                    'id': eng.model_name,
                    'object': 'model',
                    'owned_by': 'local',
                }],
            })
        elif self.path.startswith('/health'):
            self._json(200, {
                'status': 'ok',
                'requests': eng.n_requests,
                'cancelled': eng.n_cancelled,
                'errors': eng.n_errors,
                'queued': eng.queue.qsize(),
                'running': eng.running is not None,
                'prefix_cache': eng.prefix_cache.stats() if eng.prefix_cache is not None else None,
            })
        else:
            self._json(404, {'error': {'message': 'not found'}})

    def do_POST(self) -> None:
        if not self.path.startswith('/v1/chat/completions'):
            self._json(404, {'error': {'message': 'not found'}})
            return
        eng = self.engine
        try:
            n = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(n) or b'{}')
            req = Request.from_json(body, eng.defaults, eng.enable_thinking)
        except (ValueError, TypeError) as e:
            self._json(400, {'error': {'message': str(e), 'type': 'invalid_request_error'}})
            return
        try:
            job = eng.submit(req)
        except Busy:
            self._json(503, {'error': {'message': 'server busy', 'type': 'server_error'}})
            return
        if not req.stream:
            while True:
                ev = job.events.get()
                if ev[0] == 'done':
                    self._json(200, eng.completion_json(job, ev[1]))
                    return
                if ev[0] == 'error':
                    self._json(500, {'error': {'message': ev[1], 'type': 'server_error'}})
                    return
            return  # type: ignore[unreachable,unused-ignore]
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'close')
        self.end_headers()

        def gone() -> bool:
            # a closed peer shows up as readable with nothing to read; writes alone can succeed for a while
            try:
                r, _, _ = select.select([self.connection], [], [], 0)
                if r and not self.connection.recv(1, socket.MSG_PEEK):
                    return True
            except OSError:
                return True
            return False

        def send(obj: ta.Any) -> bool:
            if gone():
                job.cancel()
                return False
            try:
                self.wfile.write(b'data: ' + json.dumps(obj).encode() + b'\n\n')
                self.wfile.flush()
                return True
            except (BrokenPipeError, ConnectionResetError, OSError):
                job.cancel()
                return False

        if not send(eng.chunk_json(job, {'role': 'assistant', 'content': ''})):
            return
        while True:
            ev = job.events.get()
            if ev[0] == 'delta':
                kind = ev[1]
                if kind == 'content':
                    ok = send(eng.chunk_json(job, {'content': ev[2]}))
                elif kind == 'reasoning':
                    ok = send(eng.chunk_json(job, {'reasoning_content': ev[2]}))
                else:
                    tc = dict(ev[2])
                    tc['index'] = tc.get('index', 0)
                    ok = send(eng.chunk_json(job, {'tool_calls': [tc]}))
                if not ok:
                    return
            elif ev[0] == 'done':
                res: Result = ev[1]
                usage = {
                    'prompt_tokens': res.prompt_tokens,
                    'completion_tokens': res.completion_tokens,
                    'total_tokens': res.prompt_tokens + res.completion_tokens,
                    'prompt_tokens_reused': res.prompt_reused,
                }
                send(eng.chunk_json(job, {}, finish=res.finish_reason, usage=usage))
                try:
                    self.wfile.write(b'data: [DONE]\n\n')
                    self.wfile.flush()
                except OSError:
                    pass
                return
            else:
                send({'error': {'message': ev[1], 'type': 'server_error'}})
                return


def serve(engine: Engine, host: str = '127.0.0.1', port: int = 8000) -> ChatServer:
    """Start the HTTP server in a daemon thread; returns it (call .shutdown() to stop)."""

    srv = ChatServer((host, port), engine)
    threading.Thread(target=srv.serve_forever, name='qwen-http', daemon=True).start()
    if engine.log:
        engine.log(f'[serve] listening on http://{host}:{srv.server_address[1]}/v1/chat/completions')
    return srv


def client(
        url: str,
        messages: list[dict],
        stream: bool = True,
        write: ta.Callable[[str], None] = sys.stdout.write,  # type: ignore[assignment]
        **params: ta.Any,
) -> dict:
    """A minimal client (urllib) for smoke tests: streams content to `write`, returns the final message / usage."""

    import urllib.request

    body = {'messages': messages, 'stream': stream, **params}
    req = urllib.request.Request(  # noqa
        url.rstrip('/') + '/v1/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req) as resp:  # noqa
        if not stream:
            return json.loads(resp.read())
        content: list[str] = []
        reasoning: list[str] = []
        tool_calls: list[dict] = []
        finish = None
        usage = None
        for raw in resp:
            line = raw.decode().strip()
            if not line.startswith('data: '):
                continue
            data = line[len('data: '):]
            if data == '[DONE]':
                break
            obj = json.loads(data)
            if 'error' in obj:
                raise RuntimeError(obj['error'])
            ch = obj['choices'][0]
            d = ch.get('delta') or {}
            if d.get('reasoning_content'):
                reasoning.append(d['reasoning_content'])
                write(d['reasoning_content'])
            if d.get('content'):
                content.append(d['content'])
                write(d['content'])
            if d.get('tool_calls'):
                tool_calls.extend(d['tool_calls'])
            if ch.get('finish_reason'):
                finish = ch['finish_reason']
            if obj.get('usage'):
                usage = obj['usage']
        return {
            'message': {
                'role': 'assistant',
                'content': ''.join(content),
                'reasoning_content': ''.join(reasoning),
                'tool_calls': tool_calls,
            },
            'finish_reason': finish,
            'usage': usage,
        }
