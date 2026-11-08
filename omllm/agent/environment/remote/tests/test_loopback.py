"""The remote environment's two halves speaking to each other in process, over a socketpair."""
import asyncio
import contextlib
import dataclasses as dc
import os
import socket
import typing as ta

import pytest

from omcore.rpc.asyncio import AsyncioRpcConnections
from omcore.rpc.dispatch import RpcMethodTableHandler

from ...local import LocalEnvironmentOps
from ..client import RemoteEnvironmentOps
from ..server import RemoteEnvironmentService


##


@contextlib.asynccontextmanager
async def _loopback_environment() -> ta.AsyncIterator[RemoteEnvironmentOps]:
    client_sock, server_sock = socket.socketpair()
    client_reader, client_writer = await asyncio.open_connection(sock=client_sock)
    server_reader, server_writer = await asyncio.open_connection(sock=server_sock)

    server = AsyncioRpcConnections.of_streams(
        server_reader,
        server_writer,
        handler=RpcMethodTableHandler(RemoteEnvironmentService().methods()),
    )
    client = AsyncioRpcConnections.of_streams(client_reader, client_writer)

    await server.start()
    await client.start()
    try:
        yield RemoteEnvironmentOps(client)
    finally:
        await client.close()
        await server.close()


@pytest.mark.asyncs('asyncio')
async def test_remote_environment_loopback(tmp_path):
    root = os.path.realpath(tmp_path)

    async with _loopback_environment() as environment:
        local = await LocalEnvironmentOps().get_info()

        # The same facts, told from the far side: the one thing added is that it is the far side.
        info = await environment.get_info()
        assert info.remote
        assert not local.remote
        assert dc.replace(info, remote=False) == local

        assert (await environment.get_info(cwd=os.path.join(root, '.'))).cwd == root

        # Errors come back as what they were.
        with pytest.raises(FileNotFoundError):
            await environment.get_info(cwd=os.path.join(root, 'missing'))
