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
from ..client import DEFAULT_REMOTE_FS_CHUNK_BYTES
from ..client import RemoteFsOps
from ..server import RemoteFsService


##


@contextlib.asynccontextmanager
async def _loopback_fs(
        *,
        chunk_bytes: int = DEFAULT_REMOTE_FS_CHUNK_BYTES,
        service: RemoteFsService | None = None,
) -> ta.AsyncIterator[tuple[RemoteFsOps, RemoteFsService]]:
    if service is None:
        service = RemoteFsService()

    (client_reader, client_writer), (server_reader, server_writer) = memory_rpc_stream_pair()

    server = RpcPeer(
        AsyncioStreamRpcChannel(server_reader, server_writer),
        handler=RpcMethodHandler(service.methods()),
    )
    client = RpcPeer(AsyncioStreamRpcChannel(client_reader, client_writer))

    await server.start()
    await client.start()
    try:
        yield RemoteFsOps(client, chunk_bytes=chunk_bytes), service
    finally:
        await client.aclose()
        await server.aclose()
        await service.aclose()


def _names(root: str) -> list[str]:
    return sorted(os.listdir(root))


@pytest.mark.asyncs('asyncio')
async def test_remote_fs_loopback(tmp_path):
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'file.txt')

    async with _loopback_fs() as (fs, service):
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

        assert service.num_open_handles == 0


@pytest.mark.asyncs('asyncio')
async def test_remote_fs_chunked_content(tmp_path):
    # Content around and well past the chunk size crosses whole and unchanged, in either direction, and leaves nothing
    # open or staged behind it.
    root = os.path.realpath(tmp_path)
    chunk = 1000

    async with _loopback_fs(chunk_bytes=chunk) as (fs, service):
        for n, size in enumerate([chunk - 1, chunk, chunk + 1, chunk * 5 + 555]):
            path = os.path.join(root, f'file{n}.bin')
            content = os.urandom(size)

            assert (await fs.write_file(path, content)).created
            assert service.num_open_handles == 0

            read = await fs.read_file(path)
            assert read.data == content
            assert read.digest == fs_file_digest(content)
            assert service.num_open_handles == 0

            assert (await fs.stat(path)).size == size

        assert _names(root) == [f'file{n}.bin' for n in range(4)]


@pytest.mark.asyncs('asyncio')
async def test_remote_fs_chunked_write_keeps_the_single_calls_semantics(tmp_path):
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'file.bin')
    chunk = 1000

    async with _loopback_fs(chunk_bytes=chunk) as (fs, service):
        small = b'small'
        assert (await fs.write_file(path, small)).created
        first = await fs.read_file(path)

        # A staged replacement honors the digest it was read with, and preserves the replaced file's permissions.
        os.chmod(path, 0o640)
        big = os.urandom(chunk * 3 + 3)
        assert not (await fs.write_file(path, big, overwrite=True, expected_digest=first.digest)).created
        assert (await fs.read_file(path)).data == big
        assert (os.stat(path).st_mode & 0o777) == 0o640

        # A stale digest fails the commit, leaving the file as it was and no stage behind.
        with pytest.raises(FsFileChangedError):
            await fs.write_file(path, os.urandom(chunk * 2 + 2), overwrite=True, expected_digest=first.digest)
        assert (await fs.read_file(path)).data == big

        # So does refusing to overwrite.
        with pytest.raises(FileExistsError):
            await fs.write_file(path, os.urandom(chunk * 2 + 2))
        assert (await fs.read_file(path)).data == big

        assert service.num_open_handles == 0
        assert _names(root) == ['file.bin']


@pytest.mark.asyncs('asyncio')
async def test_remote_fs_service_bounds_chunks(tmp_path):
    # The service never serves more than its own chunk bound, whatever a client asks for, and refuses to take more.
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'file.bin')
    content = os.urandom(5000)

    async with _loopback_fs(chunk_bytes=1000, service=RemoteFsService(max_chunk_bytes=100)) as (fs, service):
        with pytest.raises(RpcRemoteError):
            await fs.write_file(path, content)
        assert service.num_open_handles == 0
        assert _names(root) == []

        with open(path, 'wb') as f:  # noqa
            f.write(content)

        read = await fs.read_file(path)
        assert read.data == content
        assert read.digest == fs_file_digest(content)
        assert service.num_open_handles == 0
