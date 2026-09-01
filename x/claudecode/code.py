"""
llm/backends/anthropic/code/backend.py  (SKETCH)

A stateful backend that drives `claude -p` over stream-json stdio, letting Claude Code run *your* tools (via a
type:"sdk" MCP server routed over the control channel) with zero built-in tools.

Naming below follows the repo:
  - `Stream` / `StreamSink` / `new_stream`       from ...core.streams
  - the SSE-event -> AiStreamEvent machinery     from ...backends/base/sse
  - `Context` / `AiMessage` / `ToolCall` / ...   from ...llm.types
  - MCP JSON-RPC payloads are plain dicts here; each is annotated with the specs.mcp.protocol type it can be marshalled
    to/from once you wire msh in.

Layering note: `llm.Tool` is a *declaration* (no executor); in the normal path your agent `TurnLoop` executes tools.
Claude Code executes tools itself, so the executor has to reach the backend somehow. Rather than pollute `llm.Tool`,
this sketch takes a `ToolHost` callback that the *agent* layer supplies (it closes over `agent.Tool.executor` +
`ToolEnvironment`). The `llm`-level backend stays a pure transport; the agent-level `ClaudeCodeBackendManager` (bottom
of file) is what actually knows how to run tools. This keeps `StreamBackend` usable for the no-tools case with no agent
dependency.
"""
import abc
import asyncio
import os
import typing as ta

from omcore import check
from omcore import lang
from omcore.formats.json import all as json

from omllm.core.http.sse import SseEvent
from omllm.core.streams import StreamSink
from omllm.core.streams import new_stream
from omllm.llm.backends.anthropic.messages.responses import translate_token_usage
from omllm.llm.backends.base.sse import BaseBackendSseEventProcessor
from omllm.llm.tools.jsonschema import build_tool_params_json_schema
from omllm.llm.types.content import TextContent
from omllm.llm.types.context import Context
from omllm.llm.types.messages import AiMessage
from omllm.llm.types.messages import Message
from omllm.llm.types.messages import ToolResultMessage
from omllm.llm.types.messages import UserMessage
from omllm.llm.types.models import Model
from omllm.llm.types.options import Options
from omllm.llm.types.streams import AiStream
from omllm.llm.types.streams import AiStreamEvent
from omllm.llm.types.streams import StreamEndAiStreamEvent
from omllm.llm.types.streams import StreamStartAiStreamEvent
from omllm.llm.types.tools import Tool


##
# the executor seam
#
# The backend needs (a) the tool declarations to advertise via tools/list, and (b) a way to actually run a call. Both
# are handed in as a ToolHost so the llm layer never depends on agent execution.


class ToolHost(lang.Abstract):
    @property
    @abc.abstractmethod
    def tools(self) -> ta.Sequence[Tool]:
        """The llm.Tool *declarations* to advertise as om__<name>."""

        raise NotImplementedError

    @abc.abstractmethod
    async def call_tool(self, name: str, args: ta.Mapping[str, ta.Any]) -> str:
        """Run a tool, return the text result. Raises to signal isError=True."""

        raise NotImplementedError


@ta.final
class NullToolHost(ToolHost):
    """For the pure StreamBackend / no-tools path."""

    @property
    def tools(self) -> ta.Sequence[Tool]:
        return ()

    async def call_tool(self, name: str, args: ta.Mapping[str, ta.Any]) -> str:
        raise RuntimeError(f'no tools configured (call to {name!r})')


##
# output processor
#
# claude wraps the raw Anthropic SSE event in a `stream_event` line, so the hard part (delta parsing -> AiStreamEvent)
# is *already done* in the sibling messages/stream.py SseEventProcessor. We reuse the base and translate each JSONL line
# into a synthetic SseEvent carrying the inner event, so `_feed` from the messages backend can be lifted almost
# verbatim.
#
# To avoid duplicating _feed, the cleanest move is: import the messages SseEventProcessor and feed it
# `SseEvent(event=None, data=json.dumps(inner))`. Below is the thin outer demux that owns the JSONL framing and the
# control channel; it delegates content to that inner processor.


class _CodeStreamProcessor(BaseBackendSseEventProcessor):
    """
    Owns one turn's worth of stdout. Note: this subclasses the *base* processor (not the messages one) only to show the
    shape; in practice delegate to the messages SseEventProcessor for `stream_event` bodies so thinking/tool/text delta
    handling isn't reimplemented.
    """

    def __init__(self, *, pricing=None) -> None:
        super().__init__()

        self._pricing = pricing
        self._done = False

    @property
    def done(self) -> bool:
        return self._done

    # The base class wants a `_feed(SseEvent)`. We instead feed whole JSONL objects; adapt by wrapping the inner API
    # event as an SseEvent so the reused messages `_feed` can consume it unchanged.
    def _feed(self, sse: SseEvent) -> None:  # pragma: no cover - see feed_line
        raise NotImplementedError('use feed_line')

    def feed_line(self, obj: ta.Mapping[str, ta.Any]) -> list[AiStreamEvent]:
        typ = obj.get('type')

        if typ == 'stream_event':
            # obj['event'] is a raw Anthropic Messages SSE event (message_start / content_block_delta / ...). Hand it to
            # the same parser the HTTP messages backend uses.
            inner = check.isinstance(obj['event'], ta.Mapping)
            return self.feed(SseEvent(event=inner.get('type'), data=json.dumps(inner), raw=()))
            # NB: `feed` is BaseBackendSseEventProcessor.feed which calls _feed; bind _feed to the messages
            # implementation (composition, not this subclass) so the delta logic is shared.

        elif typ == 'assistant':
            # Full assistant message. With --include-partial-messages the deltas already built the AiMessage; the
            # terminal `assistant` line is a consistency checkpoint. If you DON'T stream partials, build the AiMessage
            # from here instead.
            # TODO(verify): decide which is source of truth; simplest is partials-authoritative +
            # ignore this.
            return []

        elif typ == 'result':
            # Final line of the turn: usage, cost, session_id, subtype.
            self._done = True
            if (u := obj.get('usage')) is not None:
                self._message.token_usage = translate_token_usage(check.isinstance(u, ta.Mapping))
            # stop_reason: claude reports subtype ("success"/error kinds), not the raw API stop_reason on this line; map
            # deliberately.
            # TODO(verify): pull stop_reason from the last `assistant` line's message.stop_reason rather than the result
            #   subtype.
            return self.finish()

        elif typ == 'system':
            # subtype in {init, status, compact_boundary, api_retry, ...}. init carries capabilities[] + the tool/mcp
            # roster; capture it.
            return []

        else:
            # user (tool_result echo), control_request (handled elsewhere), stream_event stop, etc.
            return []


##
# the session


CLI_PATH = os.environ.get('OM_CLAUDE_CLI', 'claude')


def _build_argv(
        *,
        model: Model | None,
        system_prompt: str | None,
        has_tools: bool,
) -> list[str]:
    argv = [
        CLI_PATH,
        '--print',
        '--output-format', 'stream-json',
        '--input-format', 'stream-json',
        '--verbose',
        '--include-partial-messages',
        '--bare',                      # no hooks/skills/commands/CLAUDE.md/mcp discovery
        '--tools', '',                 # zero built-in tools
        '--strict-mcp-config',
        '--no-session-persistence',
        '--permission-mode', 'bypassPermissions',
        # Replace the entire prompt; we own it. Empty string == "no system prompt" (the SDK passes exactly this in the
        # no-prompt case).
        '--system-prompt', system_prompt or '',
    ]
    if model is not None:
        argv += ['--model', model.name]  # TODO(verify): map om Model -> claude model id/alias
    if has_tools:
        argv += [
            '--mcp-config',
            json.dumps({
                'mcpServers': {
                    'om': {
                        'type': 'sdk',
                        'name': 'om',
                    },
                },
            }),
            '--allowedTools', 'mcp__om__*',
        ]
    return argv


class ClaudeCodeSession(lang.Abstract):
    @abc.abstractmethod
    def send(self, message: Message) -> ta.Awaitable[AiStream]:
        raise NotImplementedError

    @abc.abstractmethod
    async def aclose(self) -> None:
        raise NotImplementedError

    async def __aenter__(self) -> 'ClaudeCodeSession':
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()


@ta.final
class _SubprocessClaudeCodeSession(ClaudeCodeSession):
    def __init__(
            self,
            *,
            model: Model | None,
            context: Context,
            tool_host: ToolHost,
    ) -> None:
        super().__init__()

        self._model = model
        self._context = context
        self._tool_host = tool_host

        self._proc: asyncio.subprocess.Process | None = None
        self._stdout_lines: asyncio.Queue[ta.Mapping[str, ta.Any] | None] = asyncio.Queue()
        self._reader_task: asyncio.Task | None = None
        self._req_ctr = 0
        self._initialized = asyncio.Event()
        self._capabilities: frozenset[str] = frozenset()
        # Route for the current turn's content lines. Control lines (mcp_message, can_use_tool) are dispatched
        # regardless of turn.
        self._turn_lines: asyncio.Queue[ta.Mapping[str, ta.Any]] | None = None

    # lifecycle

    async def start(self) -> None:
        argv = _build_argv(
            model=self._model,
            system_prompt=self._context.system_prompt,
            has_tools=bool(self._tool_host.tools),
        )

        env = {
            **os.environ,
            'ENABLE_TOOL_SEARCH': 'false',  # don't defer our sdk tools behind ToolSearch
            'CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK': '1',
            'CLAUDE_CODE_ENTRYPOINT': 'om-sdk',
        }

        # TODO: swap asyncio.create_subprocess_exec for core.processes.asyncio so remote docker/ssh targets and your
        #   spool plumbing come for free.
        self._proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=(self._tool_host_cwd()),
        )
        self._reader_task = asyncio.create_task(self._read_stdout())

        # 1) initialize handshake

        await self._write({
            'type': 'control_request',
            'request_id': self._next_req_id(),
            'request': {'subtype': 'initialize', 'hooks': None},
        })
        await self._initialized.wait()

        # 2) seed prior history (if any) as replay frames that do NOT query

        await self._replay_history(self._context.messages or ())

    def _tool_host_cwd(self) -> str | None:
        return None  # agent layer can thread ToolEnvironment.cwd through the host

    async def aclose(self) -> None:
        if (p := self._proc) is not None:
            try:
                if p.stdin is not None and not p.stdin.is_closing():
                    p.stdin.close()
                p.terminate()
            except ProcessLookupError:
                pass
            await p.wait()
        if (t := self._reader_task) is not None:
            t.cancel()

    # stdin

    def _next_req_id(self) -> str:
        self._req_ctr += 1
        return f'om_{self._req_ctr}_{os.urandom(3).hex()}'

    async def _write(self, obj: ta.Mapping[str, ta.Any]) -> None:
        p = check.not_none(self._proc)
        line = json.dumps(obj) + '\n'
        check.not_none(p.stdin).write(line.encode('utf-8'))
        await check.not_none(p.stdin).drain()

    # history replay
    #
    # Emits each historical message as an assistant/user frame with a fresh message.id and shouldQuery:false, so the CLI
    # folds it into the transcript without triggering a turn. The final real turn is sent via send().
    #
    # TODO(verify): Confirm against your pinned CLI with the probe script before trusting for multi-turn.

    async def _replay_history(self, messages: ta.Sequence[Message]) -> None:
        for m in messages:
            frame = self._message_to_replay_frame(m)
            if frame is not None:
                await self._write(frame)

    def _message_to_replay_frame(self, m: Message) -> ta.Mapping[str, ta.Any] | None:
        if isinstance(m, UserMessage):
            return {
                'type': 'user',
                'message': {'role': 'user', 'content': self._user_content(m.content)},
                'parent_tool_use_id': None,
                'session_id': 'default',
                'shouldQuery': False,
            }

        elif isinstance(m, AiMessage):
            content = []

            for c in m.content:
                if isinstance(c, TextContent):
                    content.append({'type': 'text', 'text': c.text})

                elif type(c).__name__ == 'ToolCall':
                    content.append({
                        'type': 'tool_use',
                        'id': c.id,
                        'name': f'mcp__om__{c.name}',  # TODO(verify): does replay want the mcp-prefixed name?
                        'input': c.args,
                    })

                elif type(c).__name__ == 'ThinkingContent':
                    # TODO: signed thinking blocks won't round-trip cleanly on replay. Prefer --resume of a real session
                    #   over manual replay when interleaving extended thinking. Drop for now.
                    continue

            return {
                'type': 'assistant',
                # Minting our own id per frame is what the changelog fix enables; without a distinct id the CLI merges
                # them into the first.
                'message': {
                    'role': 'assistant',
                    'content': content,
                    'id': f'msg_replay_{os.urandom(6).hex()}',
                },
                'parent_tool_use_id': None,
                'session_id': 'default',
            }

        elif isinstance(m, ToolResultMessage):
            return {
                'type': 'user',
                'message': {
                    'role': 'user',
                    'content': [{
                        'type': 'tool_result',
                        'tool_use_id': m.tool_call_id,
                        'content': [
                            {
                                'type': 'text',
                                'text': t.text
                            } for t in m.content
                        ],
                    }],
                },
                'parent_tool_use_id': None,
                'session_id': 'default',
                'shouldQuery': False,
            }

        else:
            raise TypeError(m)

    @staticmethod
    def _user_content(content) -> ta.Any:
        if isinstance(content, str):
            return content
        return [{'type': 'text', 'text': content.text}]  # TextContent

    # send a turn

    async def send(self, message: Message) -> AiStream:
        # Real user turn: no shouldQuery, so this fires the model.
        um = check.isinstance(message, UserMessage)
        await self._write({
            'type': 'user',
            'message': {
                'role': 'user',
                'content': self._user_content(um.content),
            },
            'parent_tool_use_id': None,
            'session_id': 'default',
        })

        proc = _CodeStreamProcessor()
        turn_q: asyncio.Queue[ta.Mapping[str, ta.Any]] = asyncio.Queue()
        self._turn_lines = turn_q

        async def inner(sink: StreamSink[AiStreamEvent]) -> AiMessage:
            await sink.emit(StreamStartAiStreamEvent())
            while True:
                obj = await turn_q.get()
                for ev in proc.feed_line(obj):
                    await sink.emit(ev)
                if proc.done:
                    break
            await sink.emit(StreamEndAiStreamEvent())
            self._turn_lines = None
            return proc.build_message()

        return await new_stream(inner)

    # stdout demux

    async def _read_stdout(self) -> None:
        p = check.not_none(self._proc)
        stdout = check.not_none(p.stdout)
        while True:
            raw = await stdout.readline()
            if not raw:
                break
            try:
                obj = json.loads(raw)
            except json.DecodeError:
                continue  # partial/blank line; claude tolerates CRLF noise

            typ = obj.get('type')

            if typ == 'control_request':
                # tool calls (mcp_message) and permission prompts arrive here, mid-turn, independent of the content
                # stream.
                asyncio.create_task(self._handle_control_request(obj))
                continue

            if typ == 'control_response':
                self._handle_control_response(obj)
                continue

            if typ == 'system' and obj.get('subtype') == 'init':
                caps = obj.get('capabilities') or []
                self._capabilities = frozenset(caps)
                # init also lists mcp_servers/tools rosters; assert om is there.
                continue

            # content lines belong to the active turn
            if (q := self._turn_lines) is not None:
                await q.put(obj)

    # control channel: serve OUR tools

    def _handle_control_response(self, obj: ta.Mapping[str, ta.Any]) -> None:
        # Resolve pending initialize/interrupt requests.
        resp = obj.get('response', {})
        if resp.get('subtype') != 'error':
            self._initialized.set()  # coarse; a real impl keys by request_id
        # TODO: match request_id -> future; handle error subtype.

    async def _handle_control_request(self, obj: ta.Mapping[str, ta.Any]) -> None:
        request_id = obj['request_id']
        req = obj['request']
        subtype = req.get('subtype')

        response_data: ta.Any

        try:
            if subtype == 'mcp_message':
                # req.server_name == "om"; req.message is a JSON-RPC request (initialize / notifications/initialized /
                # tools/list / tools/call / ping). We answer as the MCP server.
                mcp_resp = await self._handle_mcp(req['message'])
                if mcp_resp is not None:
                    response_data: ta.Any = {
                        'mcp_response': mcp_resp,
                    }
                else:
                    response_data = {
                        'mcp_response': {
                            'jsonrpc': '2.0',
                            'result': {},
                        },
                    }

            elif subtype == 'can_use_tool':
                # Only reached if you used --permission-prompt-tool stdio instead of bypassPermissions. Auto-allow om
                # tools.
                response_data = {
                    'behavior': 'allow',
                    'updatedInput': req.get('input', {}),
                }

            else:
                raise RuntimeError(f'unsupported control subtype: {subtype}')

            await self._write({
                'type': 'control_response',
                'response': {
                    'subtype': 'success',
                    'request_id': request_id,
                    'response': response_data,
                },
            })

        except Exception as e:  # noqa
            await self._write({
                'type': 'control_response',
                'response': {
                    'subtype': 'error',
                    'request_id': request_id,
                    'error': str(e),
                },
            })

    async def _handle_mcp(self, msg: ta.Mapping[str, ta.Any]) -> ta.Mapping[str, ta.Any] | None:
        """
        Minimal MCP server over JSON-RPC. Each branch's dict can be replaced by marshalling a specs.mcp.protocol type
        (InitializeResult, ListToolsResult, CallToolResult) via omcore.marshal instead of a hand-built dict.
        """

        method = msg.get('method')
        msg_id = msg.get('id')

        # notifications (no id) get no reply
        if msg_id is None:
            return None

        if method == 'initialize':
            # -> specs.mcp.protocol.InitializeResult
            return {
                'jsonrpc': '2.0',
                'id': msg_id,
                'result': {
                    'protocolVersion': msg.get('params', {}).get('protocolVersion', '2025-06-18'),
                    'capabilities': {'tools': {}},
                    'serverInfo': {'name': 'om', 'version': '0.0.0'},
                },
            }

        if method == 'tools/list':
            # -> specs.mcp.protocol.ListToolsResult; note MCP wants inputSchema (the params object), which is exactly
            # build_tool_params_json_schema.
            tools = [
                {
                    'name': t.name,
                    **({'description': t.description} if t.description is not None else {}),
                    'inputSchema': build_tool_params_json_schema(t),
                }
                for t in self._tool_host.tools
            ]
            return {
                'jsonrpc': '2.0',
                'id': msg_id,
                'result': {
                    'tools': tools,
                },
            }

        if method == 'tools/call':
            params = msg.get('params', {})
            name = params['name']
            args = params.get('arguments', {})
            try:
                text = await self._tool_host.call_tool(name, args)
                # -> specs.mcp.protocol.CallToolResult
                return {
                    'jsonrpc': '2.0',
                    'id': msg_id,
                    'result': {
                        'content': [{
                            'type': 'text',
                            'text': text,
                        }],
                    },
                }
            except Exception as e:  # noqa
                return {
                    'jsonrpc': '2.0',
                    'id': msg_id,
                    'result': {
                        'content': [{
                            'type': 'text',
                            'text': str(e),
                        }],
                        'isError': True,
                    },
                }

        if method == 'ping':
            return {'jsonrpc': '2.0', 'id': msg_id, 'result': {}}

        # method-not-found
        return {
            'jsonrpc': '2.0',
            'id': msg_id,
            'error': {
                'code': -32601,
                'message': f'{method} not supported',
            },
        }


##
# the backends
#
# Two facades over the same session:
#   1. ClaudeCodeStreamBackend  -> satisfies llm.StreamBackend for the NO-TOOLS case: one process per call, no history
#      reconciliation. Fits the existing contract exactly.
#   2. ClaudeCodeSessionBackend -> the new stateful concept: hand it a ToolHost + Context, get a live session you send()
#      into repeatedly.


class ClaudeCodeStreamBackend(lang.Abstract):
    """
    Degenerate one-shot: open a session with NullToolHost, replay the context's history, send the last user message,
    close. Implements StreamBackend.stream. Kept abstract here to avoid importing the real StreamBackend base in the
    sketch; in the tree, `class ClaudeCodeStreamBackend(StreamBackend)`.
    """

    def __init__(self, model: Model) -> None:
        super().__init__()

        self._model = model

    @property
    def model(self) -> Model:
        return self._model

    async def stream(self, context: Context, options: Options | None = None) -> AiStream:
        *history, last = list(context.messages or [])
        seed_ctx = Context(
            system_prompt=context.system_prompt,
            messages=history,
            tools=context.tools,
        )
        session = _SubprocessClaudeCodeSession(
            model=self._model,
            context=seed_ctx,
            tool_host=NullToolHost(),
        )
        await session.start()
        # NB: session must outlive the stream; wrap so aclose fires on stream exit. Simplest: tie into your core.streams
        # resource manager so the AsyncResourceManaged closes the session. Sketch omits that wiring.
        return await session.send(check.isinstance(last, UserMessage))


##
# agent-layer glue (lives under agent/, not llm/)
#
# This is where executors actually come from. An agent.ToolSet -> ToolHost adapter closes over each agent.Tool.executor
# and a ToolEnvironment.


class AgentToolHost(ToolHost):
    """
    Construct from an agent.types.tools.ToolSet + ToolEnvironment. Imports live in agent/, shown here inline for the
    sketch.
    """

    def __init__(self, tool_set, env) -> None:  # agent.ToolSet, agent.ToolEnvironment
        super().__init__()

        self._tool_set = tool_set
        self._env = env

    @property
    def tools(self) -> ta.Sequence[Tool]:
        return [t.llm_tool for t in self._tool_set]

    async def call_tool(self, name: str, args: ta.Mapping[str, ta.Any]) -> str:
        # agent tool names are bare; claude sends mcp__om__<name>.
        bare = name.removeprefix('mcp__om__')
        tool = self._tool_set[bare]

        # Import kept local to avoid llm->agent dependency at module load.
        from omllm.agent.types.tools import ToolContext

        ctx = ToolContext(
            tool=tool,
            args=args,
            env=self._env,
        )

        result = await tool.executor(ctx)
        if result.error is not None:
            raise result.error

        return result.content.text
