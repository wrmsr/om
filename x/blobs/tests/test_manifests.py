import pytest

from ..caps import BlobCapability
from ..dicts import DictBlobStore
from ..errors import BlobIndeterminateError
from ..errors import UnsupportedBlobOperationError
from ..manifests import ManifestConflictError
from ..manifests import ManifestStore


class _TimeoutBlobStore(DictBlobStore):
    """
    The first put reports indeterminate. `landed` says what actually happened server-side: our write, a rival's write
    that beat ours, or nothing.
    """

    def __init__(self, landed):
        super().__init__()
        self._landed = landed

    def put(self, key, data, *, cond=None):
        if (landed := self._landed) is None:
            return super().put(key, data, cond=cond)
        self._landed = None
        if landed == 'ours':
            super().put(key, data, cond=cond)
        elif landed == 'theirs':
            super().put(key, b'rival', cond=cond)
        raise BlobIndeterminateError(key)


def test_commit_and_find():
    ms = ManifestStore(DictBlobStore(), prefix='db/manifest')
    assert ms.find_latest() is None
    ms.commit(1, b'w1:1')
    ms.commit(2, b'w1:2')
    with pytest.raises(ManifestConflictError):
        ms.commit(2, b'w2:2')
    assert ms.find_latest() == 2
    assert ms.find_latest(after=2) == 2
    assert ms.read(2) == b'w1:2'


@pytest.mark.parametrize('landed', ['ours', 'nothing'])
def test_timeout_resolves_to_success(landed):
    ms = ManifestStore(_TimeoutBlobStore(landed), prefix='m')
    ms.commit(1, b'w1:1')
    assert ms.read(1) == b'w1:1'


def test_timeout_resolves_to_conflict():
    ms = ManifestStore(_TimeoutBlobStore('theirs'), prefix='m')
    with pytest.raises(ManifestConflictError):
        ms.commit(1, b'w1:1')
    assert ms.read(1) == b'rival'


def test_requires_put_if_absent():
    with pytest.raises(UnsupportedBlobOperationError):
        ManifestStore(DictBlobStore(capabilities=BlobCapability(0)), prefix='m')
