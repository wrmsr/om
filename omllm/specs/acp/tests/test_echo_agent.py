import asyncio
import os
import sys
import tempfile

import pytest

from omcore.specs import jsonrpc as jr
from omcore.specs.jsonrpc import pipelines as jpl

from .echo_agent import serve_unix


async def _converse(conn: jpl.AsyncioConnection, updates: list) -> None:
    res = await conn.request('initialize', {'protocolVersion': 1})
    assert res['protocolVersion'] == 1

    res = await conn.request('session/new', {'cwd': os.getcwd()})
    session_id = res['sessionId']

    res = await conn.request('session/prompt', {
        'sessionId': session_id,
        'prompt': [{'type': 'text', 'text': 'hello'}, {'type': 'image'}, {'type': 'text', 'text': 'world'}],
    })
    assert res['stopReason'] == 'end_turn'

    # Updates are notifications sent before the prompt response, so they have all arrived by now.
    assert [u['update']['content']['text'] for u in updates] == ['hello', 'world']
    assert all(u['sessionId'] == session_id for u in updates)

    with pytest.raises(jr.JsonrpcRemoteError) as ei:
        await conn.request('session/prompt', {'sessionId': 'nope', 'prompt': []})
    assert ei.value.code == jr.KnownErrors.INVALID_PARAMS.code

    await conn.notify('session/cancel', {'sessionId': session_id})


def test_echo_agent_stdio():
    async def go():
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            '-m', __package__ + '.echo_agent', 'serve', '-t', 'stdio',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        updates: list = []

        async def on_note(conn, note):
            if note.method == 'session/update':
                updates.append(note.params)

        try:
            conn = jpl.AsyncioConnections.of_subprocess(proc, notification_handler=on_note)
            async with conn:
                await _converse(conn, updates)
            await asyncio.wait_for(proc.wait(), 5.)
            assert proc.returncode == 0
        finally:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()

    asyncio.run(asyncio.wait_for(go(), 20.))


def test_echo_agent_unix():
    async def go():
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'acp.sock')
            server_task = asyncio.create_task(serve_unix(path))
            try:
                for _ in range(100):
                    if os.path.exists(path):
                        break
                    await asyncio.sleep(.02)

                updates: list = []

                async def on_note(conn, note):
                    if note.method == 'session/update':
                        updates.append(note.params)

                conn = await jpl.AsyncioConnections.connect_unix(path, notification_handler=on_note)
                async with conn:
                    await _converse(conn, updates)

            finally:
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass

    asyncio.run(asyncio.wait_for(go(), 20.))
