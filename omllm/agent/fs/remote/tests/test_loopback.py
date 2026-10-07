"""The remote filesystem's two halves speaking to each other in process, over memory streams."""
import contextlib
import os
import typing as ta

import pytest

from .....core.rpc.channels import AsyncioStreamRpcChannel
from .....core.rpc.errors import RpcRemoteError
from .....core.rpc.handlers import RpcMethodHandler
from .....core.rpc.peers import RpcPeer
from .....core.rpc.tests.support import memory_rpc_stream_pair
from ...common import FsFileChangedError
from ...common import fs_file_digest
from ..client import RemoteFsOps
from ..server import RemoteFsService


##


@contextlib.asynccontextmanager
async def _loopback_fs() -> ta.AsyncIterator[RemoteFsOps]:
    (client_reader, client_writer), (server_reader, server_writer) = memory_rpc_stream_pair()

    server = RpcPeer(
        AsyncioStreamRpcChannel(server_reader, server_writer),
        handler=RpcMethodHandler(RemoteFsService().methods()),
    )
    client = RpcPeer(AsyncioStreamRpcChannel(client_reader, client_writer))

    await server.start()
    await client.start()
    try:
        yield RemoteFsOps(client)
    finally:
        await client.aclose()
        await server.aclose()


@pytest.mark.asyncs('asyncio')
async def test_remote_fs_loopback(tmp_path):
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'file.txt')

    async with _loopback_fs() as fs:
        assert await fs.resolve_path(os.path.join(root, '.', 'file.txt')) == path

        created = await fs.write_file(path, b'one')
        assert created.created

        first = await fs.read_file(path)
        assert first.data == b'one'
        assert first.digest == fs_file_digest(b'one')

        st = await fs.stat(path)
        assert st.is_file
        assert not st.is_dir
        assert st.size == 3

        # Errors come back as what they were: the builtins by their types, the shared fs error by its name.
        with pytest.raises(FileExistsError):
            await fs.write_file(path, b'two')
        with pytest.raises(FileNotFoundError):
            await fs.read_file(os.path.join(root, 'missing.txt'))

        replaced = await fs.write_file(path, b'two', overwrite=True, expected_digest=first.digest)
        assert not replaced.created
        with pytest.raises(FsFileChangedError):
            await fs.write_file(path, b'three', overwrite=True, expected_digest=first.digest)
        assert (await fs.read_file(path)).data == b'two'

        entries = await fs.list_dir(root)
        assert [(e.name, e.path, e.is_file) for e in entries] == [('file.txt', path, True)]

        globbed = await fs.glob(os.path.join(root, '*.txt'), root=root)
        assert [e.path for e in globbed.entries] == [path]
        assert not globbed.has_more

        # Only builtins with the same meaning on both sides are translated; anything else stays a remote error.
        with pytest.raises(RpcRemoteError, match='outside permitted root'):
            await fs.glob(os.path.join(root, '..', '*.txt'), root=root)
