"""The service driven directly: its handle bookkeeping, and the split between its own work and the local ops'."""
import os

import pytest

from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from ...common import fs_file_digest
from ...local import LocalFsOps
from ..protocol import RemoteFsEntry
from ..protocol import RemoteFsGlobParams
from ..protocol import RemoteFsGlobResult
from ..protocol import RemoteFsHandleParams
from ..protocol import RemoteFsHandleResult
from ..protocol import RemoteFsPathParams
from ..protocol import RemoteFsReadChunkParams
from ..protocol import RemoteFsReadChunkResult
from ..protocol import RemoteFsReadFileParams
from ..protocol import RemoteFsReadFileResult
from ..protocol import RemoteFsWriteChunkParams
from ..protocol import RemoteFsWriteCommitParams
from ..protocol import RemoteFsWriteFileParams
from ..protocol import RemoteFsWriteFileResult
from ..server import RemoteFsService


##


class _RecordingLocalFsOps(LocalFsOps):
    def __init__(self):
        super().__init__()

        self.calls = []

    async def resolve_path(self, path):
        self.calls.append('resolve_path')
        return await super().resolve_path(path)

    async def stat(self, path):
        self.calls.append('stat')
        return await super().stat(path)

    async def read_file(self, path):
        self.calls.append('read_file')
        return await super().read_file(path)

    async def write_file(self, path, content, **kwargs):
        self.calls.append('write_file')
        return await super().write_file(path, content, **kwargs)

    async def list_dir(self, path):
        self.calls.append('list_dir')
        return await super().list_dir(path)

    async def glob(self, pattern, **kwargs):
        self.calls.append('glob')
        return await super().glob(pattern, **kwargs)


@pytest.mark.asyncs('asyncio')
async def test_local_ops_serve_what_is_the_same_on_either_side(tmp_path):
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'file.bin')
    chunk = 10

    local_ops = _RecordingLocalFsOps()
    service = RemoteFsService(local_ops=local_ops, max_chunk_bytes=chunk)

    # Paths, metadata, and a write which fits one chunk are the local ops' calls.
    small = b'small'
    written: RemoteFsWriteFileResult = unmarshal_obj(
        await service.write_file(marshal_obj(RemoteFsWriteFileParams(
            path=path,
            content=small,
            overwrite=False,
            expected_digest=None,
        ))),
        RemoteFsWriteFileResult,
    )
    assert written.created

    resolved: str = unmarshal_obj(
        await service.resolve_path(marshal_obj(RemoteFsPathParams(os.path.join(root, '.', 'file.bin')))),
        str,
    )
    assert resolved == path

    st: RemoteFsEntry = unmarshal_obj(
        await service.stat(marshal_obj(RemoteFsPathParams(path))),
        RemoteFsEntry,
    )
    assert (st.path, st.size, st.is_file, st.is_dir, st.is_symlink) == (path, len(small), True, False, False)

    entries: list = unmarshal_obj(
        await service.list_dir(marshal_obj(RemoteFsPathParams(root))),
        list[RemoteFsEntry],
    )
    assert [(e.path, e.is_file) for e in entries] == [(path, True)]

    globbed: RemoteFsGlobResult = unmarshal_obj(
        await service.glob(marshal_obj(RemoteFsGlobParams(
            pattern=os.path.join(root, '*.bin'),
            max_results=None,
        ))),
        RemoteFsGlobResult,
    )
    assert [e.path for e in globbed.entries] == [path]
    assert not globbed.has_more

    assert local_ops.calls == ['write_file', 'resolve_path', 'stat', 'list_dir', 'glob']

    # Reads of any size, and writes of more than one chunk, are the service's own: through a handle, and a stage.
    local_ops.calls.clear()

    read: RemoteFsReadFileResult = unmarshal_obj(
        await service.read_file(marshal_obj(RemoteFsReadFileParams(path=path, max_bytes=chunk))),
        RemoteFsReadFileResult,
    )
    assert (read.data, read.digest, read.handle) == (small, fs_file_digest(small), None)

    big = os.urandom(chunk * 2 + 5)
    begun: RemoteFsHandleResult = unmarshal_obj(
        await service.write_begin(marshal_obj(RemoteFsPathParams(path))),
        RemoteFsHandleResult,
    )
    for offset in range(0, len(big), chunk):
        await service.write_chunk(marshal_obj(RemoteFsWriteChunkParams(
            handle=begun.handle,
            data=big[offset:offset + chunk],
        )))
    committed: RemoteFsWriteFileResult = unmarshal_obj(
        await service.write_commit(marshal_obj(RemoteFsWriteCommitParams(
            handle=begun.handle,
            overwrite=True,
            expected_digest=read.digest,
        ))),
        RemoteFsWriteFileResult,
    )
    assert not committed.created

    first: RemoteFsReadFileResult = unmarshal_obj(
        await service.read_file(marshal_obj(RemoteFsReadFileParams(path=path, max_bytes=chunk))),
        RemoteFsReadFileResult,
    )
    assert first.handle is not None
    parts = [first.data]
    while True:
        more: RemoteFsReadChunkResult = unmarshal_obj(
            await service.read_chunk(marshal_obj(RemoteFsReadChunkParams(handle=first.handle, max_bytes=chunk))),
            RemoteFsReadChunkResult,
        )
        parts.append(more.data)
        if more.digest is not None:
            break
    assert b''.join(parts) == big
    assert more.digest == fs_file_digest(big)

    assert local_ops.calls == []
    assert service.num_open_handles == 0
    assert os.listdir(root) == ['file.bin']


@pytest.mark.asyncs('asyncio')
async def test_abandoned_reads_and_writes_are_released(tmp_path):
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'file.bin')
    with open(path, 'wb') as f:  # noqa
        f.write(os.urandom(100))

    service = RemoteFsService()

    # A read the host gives up on.
    first: RemoteFsReadFileResult = unmarshal_obj(
        await service.read_file(marshal_obj(RemoteFsReadFileParams(path=path, max_bytes=10))),
        RemoteFsReadFileResult,
    )
    handle = first.handle
    assert handle is not None
    assert len(first.data) == 10
    assert service.num_open_handles == 1

    await service.read_abort(marshal_obj(RemoteFsHandleParams(handle)))
    assert service.num_open_handles == 0
    with pytest.raises(ValueError, match='No such remote filesystem read'):
        await service.read_chunk(marshal_obj(RemoteFsReadChunkParams(handle=handle, max_bytes=10)))

    # Aborting again, or a handle that already went with its last chunk, is harmless.
    await service.read_abort(marshal_obj(RemoteFsHandleParams(handle)))

    # A write the host gives up on, and one it never finishes: both are discarded with their staging.
    begun: RemoteFsHandleResult = unmarshal_obj(
        await service.write_begin(marshal_obj(RemoteFsPathParams(os.path.join(root, 'new.bin')))),
        RemoteFsHandleResult,
    )
    await service.write_chunk(marshal_obj(RemoteFsWriteChunkParams(handle=begun.handle, data=b'partial')))
    assert service.num_open_handles == 1
    assert len(os.listdir(root)) == 2  # the file and the staging directory

    await service.write_abort(marshal_obj(RemoteFsHandleParams(begun.handle)))
    assert service.num_open_handles == 0
    assert os.listdir(root) == ['file.bin']

    forgotten: RemoteFsHandleResult = unmarshal_obj(
        await service.write_begin(marshal_obj(RemoteFsPathParams(os.path.join(root, 'new.bin')))),
        RemoteFsHandleResult,
    )
    assert forgotten.handle != begun.handle
    await service.aclose()
    assert service.num_open_handles == 0
    assert os.listdir(root) == ['file.bin']

    with pytest.raises(RuntimeError, match='closed'):
        await service.write_begin(marshal_obj(RemoteFsPathParams(os.path.join(root, 'late.bin'))))
