"""The service's handle bookkeeping, driven directly."""
import os

import pytest

from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from ..protocol import RemoteFsHandleParams
from ..protocol import RemoteFsHandleResult
from ..protocol import RemoteFsPathParams
from ..protocol import RemoteFsReadChunkParams
from ..protocol import RemoteFsReadFileParams
from ..protocol import RemoteFsReadFileResult
from ..protocol import RemoteFsWriteChunkParams
from ..server import RemoteFsService


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
