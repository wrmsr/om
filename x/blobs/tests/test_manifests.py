import pytest

from omcore import lang

from ..adapters import SyncToAsyncBlobStore
from ..caps import BlobCapability
from ..dicts import DictBlobStore
from ..errors import InvalidBlobKeyError
from ..errors import UnsupportedBlobOperationError
from ..manifests import ManifestConflictError
from ..manifests import ManifestStore
from .faults import BlobFault
from .faults import FaultInjectingBlobStore


def _faulting_store(landed):
    async def rival(s):
        await s.put('m/00000000000000000001', b'rival')

    return FaultInjectingBlobStore(SyncToAsyncBlobStore(DictBlobStore()), [BlobFault(
        op='put',
        after=landed == 'ours',
        side_effect=rival if landed == 'theirs' else None,
    )])


def test_commit_and_find():
    async def inner():
        ms = ManifestStore(SyncToAsyncBlobStore(DictBlobStore()), prefix='db/manifest')
        assert await ms.find_latest() is None
        await ms.commit(1, b'w1:1')
        await ms.commit(2, b'w1:2')
        with pytest.raises(ManifestConflictError):
            await ms.commit(2, b'w2:2')
        assert await ms.find_latest() == 2
        assert await ms.find_latest(after=2) == 2
        assert await ms.find_latest(after=1) == 2
        assert await ms.read(2) == b'w1:2'
        assert await lang.async_list(ms.iter_ids()) == [1, 2]
        await ms.delete_ids([1])
        assert await lang.async_list(ms.iter_ids()) == [2]

    lang.sync_await(inner())


def test_ignores_foreign_keys():
    async def inner():
        s = SyncToAsyncBlobStore(DictBlobStore())
        ms = ManifestStore(s, prefix='m')
        await ms.commit(3, b'x')
        for k in ['m/3', 'm/0000000000000000000x', 'm/00000000000000000004/y', 'm/\uff10' * 1]:
            await s.put(k, b'')
        assert await lang.async_list(ms.iter_ids()) == [3]

    lang.sync_await(inner())


@pytest.mark.parametrize('landed', ['ours', 'nothing'])
def test_timeout_resolves_to_success(landed):
    async def inner():
        ms = ManifestStore(_faulting_store(landed), prefix='m')
        await ms.commit(1, b'w1:1')
        assert await ms.read(1) == b'w1:1'

    lang.sync_await(inner())


def test_timeout_resolves_to_conflict():
    async def inner():
        ms = ManifestStore(_faulting_store('theirs'), prefix='m')
        with pytest.raises(ManifestConflictError):
            await ms.commit(1, b'w1:1')
        assert await ms.read(1) == b'rival'

    lang.sync_await(inner())


def test_requires_put_if_absent():
    with pytest.raises(UnsupportedBlobOperationError):
        ManifestStore(SyncToAsyncBlobStore(DictBlobStore(capabilities=BlobCapability(0))), prefix='m')


def test_validates_prefix():
    with pytest.raises(InvalidBlobKeyError):
        ManifestStore(SyncToAsyncBlobStore(DictBlobStore()), prefix='a//b')
