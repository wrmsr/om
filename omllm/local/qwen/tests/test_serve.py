"""
serving.py end to end on the synthetic model: non-streaming and streaming chat completions over HTTP, a follow-up
turn reusing the prefix cache, tool rendering, stop sequences, cancellation of a streaming client, and the queue
limit. torch CPU (static-input protocol) with speculative decoding.

Run:  python -m pytest omllm/local/qwen/tests/test_serve.py -q      or      python -m omllm.local.qwen.tests.test_serve
"""
import json
import socket
import threading
import time
import urllib.error
import urllib.request

import pytest

from ..model import Qwen35
from ..prefixcache import PrefixCache
from ..serving import Engine
from ..serving import Request
from ..serving import SamplingDefaults
from ..serving import client
from ..serving import serve
from ..tokenizer import Tokenizer
from .test_parity import synthetic_source


##


def _post(url: str, body: dict) -> tuple[int, dict]:
    req = urllib.request.Request(  # noqa
        url,
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req) as resp:  # noqa
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')


# FIXME: broken in ci, no 503 from queue rejection
@pytest.mark.skip_unless_alone
def test_serve():
    try:
        from ..backends.torch import TorchOps
    except ImportError:
        print('torch not installed; skipping')
        return
    cfg, hf, src = synthetic_source()
    ops = TorchOps('cpu', capture_mode='static')
    model = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True)
    tok = Tokenizer.from_spec(src.tokenizer_spec)
    logs: list[str] = []
    engine = Engine(
        model,
        tok,
        spec=2,
        capacity=256,
        prefix_cache=PrefixCache(ops, 1 << 30, 1 << 30),
        defaults=SamplingDefaults(
            temperature=0.0,
            top_k=0,
            top_p=1.0,
            max_tokens=12,
        ),
        max_queue=1,
        model_name='tiny',
        log=logs.append,
    )
    srv = serve(engine, '127.0.0.1', 0)
    port = srv.server_address[1]
    base = f'http://127.0.0.1:{port}'
    try:
        # models / health
        with urllib.request.urlopen(base + '/v1/models') as r:  # noqa
            assert json.loads(r.read())['data'][0]['id'] == 'tiny'

        # 1. non-streaming, greedy
        code, res = _post(base + '/v1/chat/completions', {'messages': [{'role': 'user', 'content': 'hello'}]})
        assert code == 200 and res['object'] == 'chat.completion', res
        msg = res['choices'][0]['message']
        assert msg['role'] == 'assistant'
        assert res['usage']['completion_tokens'] == 12 and res['choices'][0]['finish_reason'] in ('length', 'stop')
        assert res['usage']['prompt_tokens_reused'] == 0

        # 2. the same request streamed gives the same text (greedy), as deltas
        got = client(base, [{'role': 'user', 'content': 'hello'}], stream=True, write=lambda s: None)
        assert got['usage']['completion_tokens'] == 12 and got['finish_reason'] == res['choices'][0]['finish_reason']
        assert got['usage']['prompt_tokens_reused'] == res['usage']['prompt_tokens']  # the whole prompt matched
        joined = (got['message']['reasoning_content'] or '') + got['message']['content']
        joined_ref = (msg.get('reasoning_content') or '') + (msg['content'] or '')
        assert joined.replace('\n', '') == joined_ref.replace('\n', ''), (joined, joined_ref)

        # 3. a follow-up turn resumes from the generation-end snapshot: the earlier prompt + its answer are reused
        history = [
            {'role': 'user', 'content': 'hello'},
            {'role': 'assistant', **{k: v for k, v in msg.items() if k != 'role'}},
            {'role': 'user', 'content': 'and?'},
        ]
        code, res2 = _post(base + '/v1/chat/completions', {'messages': history})
        assert code == 200, res2
        assert res2['usage']['prompt_tokens_reused'] >= res['usage']['prompt_tokens'] + 12 - 1, res2['usage']

        # 4. tools render into the system turn; stop sequences truncate
        tool = {'type': 'function', 'function': {'name': 'f', 'parameters': {'type': 'object', 'properties': {}}}}
        text = engine.render(Request.from_json(
            {'messages': [{'role': 'user', 'content': 'x'}], 'tools': [tool]}, engine.defaults, True,
        ))
        assert '<tools>' in text and '"name": "f"' in text
        code, res3 = _post(base + '/v1/chat/completions', {
            'messages': [{'role': 'user', 'content': 'hello'}],
            'stop': [joined_ref[3:6]] if len(joined_ref) > 6 else ['zzz'],
        })
        assert code == 200 and res3['choices'][0]['finish_reason'] in ('stop', 'length')

        # 5. cancellation: a job cancelled while it runs ends as 'cancelled' and the engine moves on (the synthetic
        # model's byte soup rarely forms complete UTF-8, so the text streamer holds deltas back; time it instead)
        n_before = engine.n_requests
        job = engine.submit(Request.from_json(
            {'messages': [{'role': 'user', 'content': 'slow'}], 'stream': True, 'max_tokens': 400},
            engine.defaults,
            True,
        ))
        while engine.n_requests == n_before:
            time.sleep(0.01)
        time.sleep(0.1)
        job.cancel()
        ev = job.events.get()
        while ev[0] == 'delta':
            ev = job.events.get()
        assert ev == ('error', 'cancelled') and engine.n_cancelled == 1, (ev[0], engine.n_cancelled)
        # ... and a streaming HTTP client that disconnects is noticed on the next write (best effort: the tiny model may
        # finish first)
        s = socket.create_connection(('127.0.0.1', port))
        body = json.dumps({
            'messages': [{'role': 'user', 'content': 'slow2'}],
            'stream': True,
            'max_tokens': 400,
        }).encode()
        s.sendall(
            b'POST /v1/chat/completions HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n'
            b'Content-Length: ' + str(len(body)).encode() + b'\r\n\r\n' + body,
        )
        s.recv(4096)
        s.close()
        t0 = time.time()
        while not engine.idle() and time.time() - t0 < 60:
            time.sleep(0.02)
        code, res4 = _post(
            base + '/v1/chat/completions',
            {'messages': [{'role': 'user', 'content': 'after'}], 'max_tokens': 3},
        )
        assert code == 200 and res4['usage']['completion_tokens'] == 3

        # 6. queue limit: with one slot, a third concurrent request is refused with 503
        results: list[tuple[int, dict]] = []

        def slow():
            results.append(_post(
                base + '/v1/chat/completions',
                {'messages': [{'role': 'user', 'content': 'q'}], 'max_tokens': 40},
            ))

        threads = [threading.Thread(target=slow) for _ in range(2)]
        for t in threads:
            t.start()
        time.sleep(0.3)
        code, _ = _post(
            base + '/v1/chat/completions',
            {'messages': [{'role': 'user', 'content': 'q'}], 'max_tokens': 1},
        )
        for t in threads:
            t.join()
        codes = sorted([code] + [c for c, _ in results])
        assert codes == [200, 200, 503], codes  # one running, one queued, one refused
    finally:
        srv.shutdown()
    print(
        f'serve OK: {engine.n_requests} requests, '
        f'{engine.n_cancelled} cancelled; '
        f'{engine.prefix_cache.stats()}',  # type: ignore
    )


if __name__ == '__main__':
    test_serve()
