import asyncio
import os.path
import tempfile

import pytest

from ..... import llm
from .....agent.tests.scripted import scripted_backend
from .....agent.tests.scripted import text_message
from .....agent.tests.scripted import tool_call_message
from ...tests.harness import WebTestStreamError
from ...tests.harness import entry_types
from ...tests.harness import web_test_session


##


def _read_file(path: str) -> str:
    with open(path) as f:
        return f.read()


@pytest.mark.asyncs('asyncio')
async def test_page_and_static():
    async with web_test_session(scripted_backend(text_message('hi'))) as ws:
        resp = await ws.client.request('GET', f'/?token={ws.web.token.v}')
        assert resp.status == 200
        assert resp.headers['content-type'].startswith('text/html')
        assert ws.web.token.v.encode() in resp.body
        assert b'__OMLLM_WEB_TOKEN__' not in resp.body
        assert "default-src 'self'" in resp.headers['content-security-policy']

        resp = await ws.client.request('GET', '/static/app.mjs')
        assert resp.status == 200
        assert resp.headers['content-type'].startswith('text/javascript')

        resp = await ws.client.request('GET', '/static/vendor/packages/marked/index.js')
        assert resp.status == 200

        for path in [
            '/static/nope.mjs',
            '/static/../main.py',
            '/static/.pkgdata',
            '/static/__init__.py',
        ]:
            assert (await ws.client.request('GET', path)).status == 404, path


@pytest.mark.asyncs('asyncio')
async def test_guard():
    async with web_test_session(scripted_backend(text_message('hi'))) as ws:
        assert (await ws.client.without_token().request('GET', '/api/info')).status == 403

        resp = await ws.client.request('GET', '/api/info', headers={'host': f'evil.example:{ws.web.address.port}'})
        assert resp.status == 403

        resp = await ws.client.request('GET', '/api/info', headers={'origin': 'http://evil.example'})
        assert resp.status == 403

        resp = await ws.client.request('GET', '/api/info')
        assert resp.status == 200
        info = resp.json()
        assert info['busy'] is False
        assert {'echo', 'quit', 'steer'} <= {c['name'] for c in info['commands']}


@pytest.mark.asyncs('asyncio')
async def test_url_authentication():
    async with web_test_session(scripted_backend()) as ws:
        client = ws.client.without_token()
        assert ws.web.url == f'{ws.web.address.url}?token={ws.web.token.v}'
        for path in [
            '/',
            '/?token=',
            '/?token=wrong',
            '/?token=%FF',
            f'/?token=wrong&token={ws.web.token.v}',
            f'/?token=&token={ws.web.token.v}',
        ]:
            resp = await client.request('GET', path)
            assert resp.status == 403
            assert ws.web.token.v.encode() not in resp.body

        # Knowing the api header is not a substitute for opening the secret URL.
        assert (await ws.client.request('GET', '/')).status == 403
        resp = await client.request('GET', f'/?token={ws.web.token.v}')
        assert resp.status == 200
        assert ws.web.token.v.encode() in resp.body
        assert resp.headers['referrer-policy'] == 'no-referrer'

        # The URL token does not replace the api's cross-origin protection.
        assert (await client.request('GET', f'/api/info?token={ws.web.token.v}')).status == 403
        assert (await client.request('GET', '/static/app.mjs')).status == 200

    async with web_test_session(scripted_backend()) as other:
        assert other.web.token != ws.web.token
        assert (await other.client.request('GET', f'/?token={ws.web.token.v}')).status == 403


@pytest.mark.asyncs('asyncio')
async def test_no_auth():
    async with web_test_session(scripted_backend(), no_auth=True) as ws:
        assert ws.web.url == ws.web.address.url
        resp = await ws.client.without_token().request('GET', '/')
        assert resp.status == 200
        assert ws.web.token.v.encode() in resp.body
        assert (await ws.client.without_token().request('GET', '/api/info')).status == 403
        assert (await ws.client.request('GET', '/api/info')).status == 200
        assert (await ws.client.request('GET', '/', headers={'origin': 'http://evil.example'})).status == 403


@pytest.mark.asyncs('asyncio')
async def test_prompt_streams_through_its_end():
    async with web_test_session(scripted_backend(text_message('Hello there, browser.'), stream=True)) as ws:
        entries = await ws.client.submit('hi')

        types = entry_types(entries)
        assert types[:3] == ['submission_start', 'user_message', 'run_start']
        assert types[-2:] == ['run_end', 'submission_end']
        assert entries[-1]['status'] == 'completed'

        assert ''.join(e['text'] for e in entries if e['type'] == 'ai_text_delta') == 'Hello there, browser.'
        assert [e['text'] for e in entries if e['type'] == 'ai_text_end'] == ['Hello there, browser.']

        assert [e['seq'] for e in entries] == list(range(1, len(entries) + 1))

        # The whole of it is in the feed, for a page loading later.
        resp = await ws.client.request('GET', '/api/feed?after=0')
        assert [e['seq'] for e in resp.json()['entries']] == [e['seq'] for e in entries]

        resp = await ws.client.request('GET', '/api/feed?after=3')
        assert [e['seq'] for e in resp.json()['entries']] == [e['seq'] for e in entries[3:]]


@pytest.mark.asyncs('asyncio')
async def test_commands():
    async with web_test_session(scripted_backend()) as ws:
        entries = await ws.client.submit('/echo "hello, page"')
        assert entry_types(entries) == ['submission_start', 'command_echo', 'text', 'submission_end']
        assert entries[2]['text'] == 'hello, page'
        assert entries[-1]['status'] == 'success'

        entries = await ws.client.submit('/nope', after=entries[-1]['seq'])
        assert entry_types(entries) == ['submission_start', 'command_echo', 'text', 'submission_end']
        assert 'Unknown command' in entries[2]['text']
        assert entries[-1]['status'] == 'failure'


@pytest.mark.asyncs('asyncio')
async def test_bad_requests():
    async with web_test_session(scripted_backend()) as ws:
        assert (await ws.client.request('POST', '/api/submit', {'text': '   '})).status == 400
        assert (await ws.client.request('POST', '/api/submit', {'text': 3})).status == 400
        assert (await ws.client.request('GET', '/api/feed?after=x')).status == 400
        assert (await ws.client.request('POST', '/api/permissions', {'id': '1', 'allow': True})).status == 404


@pytest.mark.asyncs('asyncio')
async def test_busy_is_rejected_but_steer_runs_alongside():
    started = asyncio.Event()
    release = asyncio.Event()

    async def gate(point: llm.BackendScriptGatePoint) -> None:
        if point.emission_index == 1:
            started.set()
            await release.wait()

    backend = scripted_backend(text_message('slow answer'), stream=True, gate=gate)

    async with web_test_session(backend) as ws:
        prompt_task = asyncio.create_task(ws.client.submit('take your time'))
        await started.wait()

        assert (await ws.client.request('GET', '/api/info')).json()['busy'] is True

        with pytest.raises(WebTestStreamError) as ei:
            await ws.client.submit('me too')
        assert ei.value.status == 409

        # Allowed while busy, so it runs - its stream carrying everything up to its own end, and ending there.
        entries = await ws.client.submit('/echo "still here"')
        assert entries[-1]['type'] == 'submission_end'
        assert entries[-1]['status'] == 'success'
        assert {'type': 'text', 'text': 'still here'} in [{k: v for k, v in e.items() if k != 'seq'} for e in entries]

        release.set()
        prompt_entries = await prompt_task
        assert prompt_entries[-1]['status'] == 'completed'

        assert (await ws.client.request('GET', '/api/info')).json()['busy'] is False


@pytest.mark.asyncs('asyncio')
async def test_cancel():
    started = asyncio.Event()

    async def gate(point: llm.BackendScriptGatePoint) -> None:
        if point.emission_index == 1:
            started.set()
            await asyncio.Event().wait()

    backend = scripted_backend(text_message('never finished'), stream=True, gate=gate)

    async with web_test_session(backend) as ws:
        prompt_task = asyncio.create_task(ws.client.submit('go'))
        await started.wait()

        assert (await ws.client.request('POST', '/api/cancel', {})).json() == {'cancelled': True}

        entries = await prompt_task
        assert entries[-1]['type'] == 'submission_end'
        assert entries[-1]['status'] == 'cancelled'
        assert [e['reason'] for e in entries if e['type'] == 'run_end'] == ['cancelled']

        assert (await ws.client.request('POST', '/api/cancel', {})).json() == {'cancelled': False}


@pytest.mark.asyncs('asyncio')
async def test_permission_ask_round_trip():
    with tempfile.TemporaryDirectory() as cwd:
        cwd = os.path.realpath(cwd)
        file_path = os.path.join(cwd, 'new.txt')

        backend = scripted_backend(
            tool_call_message(llm.ToolCall('call-1', 'write', {'file_path': file_path, 'contents': 'hi\n'})),
            text_message('Written.'),
        )

        async with web_test_session(
                backend,
                cwd=cwd,
                fs=True,
                autoexec=[f'/permissions add ask glob_fs \'{{"glob":"{cwd}/**","modes":["w"]}}\''],
        ) as ws:
            seen: list[dict] = []
            async for entry in ws.client.stream('POST', '/api/submit', {'text': 'write it'}):
                seen.append(entry)

                if entry['type'] == 'permission_ask':
                    assert entry['key'] == 'call-1'
                    assert entry['tool'] == 'write'
                    assert entry['preview'] is not None

                    resp = await ws.client.request('POST', '/api/permissions', {'id': entry['id'], 'allow': True})
                    assert resp.status == 200

            types = entry_types(seen)
            assert types.index('tool_start') < types.index('permission_ask') < types.index('permission_answer')
            assert [e['outcome'] for e in seen if e['type'] == 'permission_answer'] == ['allow']
            assert [e['ok'] for e in seen if e['type'] == 'tool_end'] == [True]
            assert seen[-1]['status'] == 'completed'

            assert _read_file(file_path) == 'hi\n'


@pytest.mark.asyncs('asyncio')
async def test_follow():
    async with web_test_session(scripted_backend(text_message('one'), text_message('two'), stream=True)) as ws:
        first = await ws.client.submit('first')

        followed: list[dict] = []
        got_end = asyncio.Event()

        async def follow() -> None:
            async for entry in ws.client.stream('GET', f'/api/feed/stream?after={first[-1]["seq"]}'):
                followed.append(entry)
                if entry['type'] == 'submission_end':
                    got_end.set()
                    return

        follow_task = asyncio.create_task(follow())
        second = await ws.client.submit('second')
        await asyncio.wait_for(got_end.wait(), 10.)
        await follow_task

        assert [e['seq'] for e in followed] == [e['seq'] for e in second]


@pytest.mark.asyncs('asyncio')
async def test_quit():
    async with web_test_session(scripted_backend()) as ws:
        follow_task = asyncio.create_task(ws.client.stream_all('GET', '/api/feed/stream?after=0'))

        entries = await ws.client.submit('/quit')

        # The news reaches the page on the stream of the /quit which asked, which goes on past its own end for it.
        assert entry_types(entries) == ['submission_start', 'command_echo', 'submission_end', 'shutdown']
        assert ws.web.quit_signal.is_set

        # And a stream following the feed ends with it.
        assert entry_types(await asyncio.wait_for(follow_task, 10.))[-1] == 'shutdown'


@pytest.mark.asyncs('asyncio')
async def test_quitting_mid_run_ends_it_before_announcing():
    started = asyncio.Event()

    async def gate(point: llm.BackendScriptGatePoint) -> None:
        if point.emission_index == 1:
            started.set()
            await asyncio.Event().wait()

    async with web_test_session(scripted_backend(text_message('never finished'), stream=True, gate=gate)) as ws:
        follow_task = asyncio.create_task(ws.client.stream_all('GET', '/api/feed/stream?after=0'))
        prompt_task = asyncio.create_task(ws.client.submit('go'))
        await started.wait()

        await ws.web.quit_signal.quit()

        followed = await asyncio.wait_for(follow_task, 10.)
        types = entry_types(followed)
        assert types[-1] == 'shutdown'
        assert types.index('run_end') < types.index('submission_end') < types.index('shutdown')

        # The prompt's own stream goes on past its end, to the announcement.
        assert entry_types(await asyncio.wait_for(prompt_task, 10.))[-2:] == ['submission_end', 'shutdown']


@pytest.mark.asyncs('asyncio')
async def test_cursor_past_the_end():
    async with web_test_session(scripted_backend()) as ws:
        # From a page of an earlier server, say: taken as the end of this one's feed.
        entries = await ws.client.submit('/echo hi', after=1000)
        assert entry_types(entries) == ['submission_start', 'command_echo', 'text', 'submission_end']
