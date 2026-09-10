import asyncio
import sys

import pytest

from omcore.specs import jsonrpc as jr

from .. import protocolold as pt
from ..clients import McpServerConnection


def test_client_against_fake_server():
    async def go():
        async with McpServerConnection.open_process([
            sys.executable,
            '-m', __package__ + '.fakeserver',
        ]) as (proc, client):
            res = await client.request(pt.InitializeRequest(
                client_info=pt.Implementation(name='test', version='0'),
            ))
            assert res.server_info.name == 'fake'

            await client.notify(pt.InitializedNotification())

            tools = await client.list_tools()
            assert [t.name for t in tools] == ['alpha', 'beta', 'gamma']
            assert tools[0].description == 'first'

            pages = await client.list_cursor_request(pt.ListToolsRequest())
            assert len(pages) == 2

            # A raw call straight through the underlying connection still works.
            assert await client.connection.request('ping') == {}

            with pytest.raises(jr.JsonrpcRemoteError) as ei:
                await client.connection.request('nope')
            assert ei.value.code == jr.KnownErrors.METHOD_NOT_FOUND.code

        assert proc.returncode == 0

    asyncio.run(asyncio.wait_for(go(), 20.))
