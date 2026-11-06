import asyncio

import pytest

from omcore.http import asgi

from ..serving import AsgiPipelineServer
from ..serving import bind_web_server_socket
from ..serving import get_web_server_socket_address


##


async def _hello_app(scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
    await asgi.read_body(recv)

    host, port = scope['server']
    body = f'hello {host}:{port}'.encode()

    await asgi.send_response(send, 200, body=body, headers=[(b'connection', b'close')])


@pytest.mark.asyncs('asyncio')
async def test_serves_and_closes_idle_connections():
    sock = bind_web_server_socket('127.0.0.1', 0)
    port = get_web_server_socket_address(sock).port

    async with AsgiPipelineServer(app=_hello_app, sock=sock, request_read_timeout_s=.2):
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        writer.write(b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')
        resp = await asyncio.wait_for(reader.read(), 5.)
        assert resp.startswith(b'HTTP/1.1 200')
        assert resp.endswith(f'hello 127.0.0.1:{port}'.encode())
        writer.close()

        # A connection which never gets around to its request is not kept forever.
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        writer.write(b'GET / HTTP/1.1\r\n')
        assert await asyncio.wait_for(reader.read(), 5.) == b''
        writer.close()
