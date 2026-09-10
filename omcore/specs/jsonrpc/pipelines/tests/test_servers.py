import asyncio
import os
import tempfile

import pytest

from .....sockets.endpoints import TcpSocketEndpoint
from .....sockets.endpoints import UnixSocketEndpoint
from ...dispatch import AsyncDictJsonrpcDispatcher
from ...errors import JsonrpcRemoteError
from ..asyncio import AsyncioJsonrpcConnection
from ..asyncio import AsyncioJsonrpcConnections
from ..configs import JsonrpcPipelineConfig
from ..servers import AsyncioJsonrpcServer
from ..servers import AsyncioJsonrpcServerConfig
from .echoserver import build_dispatcher


TIMEOUT_S = 20.


def run(coro):
    async def with_timeout():
        async with asyncio.timeout(TIMEOUT_S):
            await coro
    asyncio.run(with_timeout())


def test_tcp_server():
    async def go():
        server = AsyncioJsonrpcServer(
            AsyncioJsonrpcServerConfig(endpoint=TcpSocketEndpoint(host='127.0.0.1', port=0)),
            dispatcher=build_dispatcher(),
        )
        async with server:
            ep = server.bound_endpoint
            assert isinstance(ep, TcpSocketEndpoint)
            assert ep.port > 0

            client_d = AsyncDictJsonrpcDispatcher({'double': lambda value: value * 2})
            conns = [
                await AsyncioJsonrpcConnections.connect_tcp(ep.host, ep.port, dispatcher=client_d)
                for _ in range(3)
            ]
            for c in conns:
                await c.start()
            try:
                results = await asyncio.gather(*[c.request('add', [i, 1]) for i, c in enumerate(conns)])
                assert results == [1, 2, 3]

                # Server calls back into the client from within a handler.
                assert await conns[0].request('callback', {'value': 5}) == 10

                assert len(server.connections) == 3
            finally:
                for c in conns:
                    await c.close()

            # Connections go away once closed.
            for _ in range(50):
                if not server.connections:
                    break
                await asyncio.sleep(.02)
            assert not server.connections

    run(go())


def test_unix_server_with_hook():
    async def go():
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'sock')
            greeted: list[bool] = []

            async def on_connection(conn: AsyncioJsonrpcConnection) -> None:
                # Server-initiated request at connection start.
                greeted.append(await conn.request('double', {'value': 2}) == 4)

            server = AsyncioJsonrpcServer(
                AsyncioJsonrpcServerConfig(endpoint=UnixSocketEndpoint(path=path)),
                dispatcher=build_dispatcher(),
                on_connection=on_connection,
            )
            async with server:
                assert os.path.exists(path)

                conn = await AsyncioJsonrpcConnections.connect_unix(
                    path,
                    dispatcher=AsyncDictJsonrpcDispatcher({'double': lambda value: value * 2}),
                )
                async with conn:
                    assert await conn.request('add', [2, 2]) == 4
                    for _ in range(50):
                        if greeted:
                            break
                        await asyncio.sleep(.02)
                    assert greeted == [True]

            assert not os.path.exists(path)

    run(go())


def test_max_connections():
    async def go():
        server = AsyncioJsonrpcServer(
            AsyncioJsonrpcServerConfig(endpoint=TcpSocketEndpoint(host='127.0.0.1', port=0), max_connections=1),
            dispatcher=build_dispatcher(),
        )
        async with server:
            ep = server.bound_endpoint
            assert isinstance(ep, TcpSocketEndpoint)

            c1 = await AsyncioJsonrpcConnections.connect_tcp(ep.host, ep.port)
            async with c1:
                assert await c1.request('add', [1, 1]) == 2

                c2 = await AsyncioJsonrpcConnections.connect_tcp(ep.host, ep.port)
                async with c2:
                    # Refused connections are closed by the server; the request fails rather than hanging.
                    with pytest.raises(Exception):  # noqa
                        await c2.request('add', [1, 1], timeout_s=2.)

    run(go())


def test_server_close_drains_inflight():
    async def go():
        server = AsyncioJsonrpcServer(
            AsyncioJsonrpcServerConfig(
                endpoint=TcpSocketEndpoint(host='127.0.0.1', port=0),
                drain_timeout_s=5.,
                pipeline=JsonrpcPipelineConfig(close_drain_timeout_s=5.),
            ),
            dispatcher=build_dispatcher(),
        )
        await server.start()
        ep = server.bound_endpoint
        assert isinstance(ep, TcpSocketEndpoint)

        conn = await AsyncioJsonrpcConnections.connect_tcp(ep.host, ep.port)
        await conn.start()
        t = asyncio.create_task(conn.request('sleep', [.3]))
        await asyncio.sleep(.05)

        await server.close()
        assert await t == 'slept'
        await conn.close()

    run(go())


def test_server_abortive_close():
    async def go():
        server = AsyncioJsonrpcServer(
            AsyncioJsonrpcServerConfig(endpoint=TcpSocketEndpoint(host='127.0.0.1', port=0)),
            dispatcher=build_dispatcher(),
        )
        await server.start()
        ep = server.bound_endpoint
        assert isinstance(ep, TcpSocketEndpoint)

        conn = await AsyncioJsonrpcConnections.connect_tcp(ep.host, ep.port)
        await conn.start()
        t = asyncio.create_task(conn.request('sleep', [5.]))
        await asyncio.sleep(.05)

        await server.close(graceful=False)
        with pytest.raises(JsonrpcRemoteError):
            await t
        await conn.close(graceful=False)

    run(go())
