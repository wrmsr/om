import pytest

from ...adapters import SyncToAsyncBlobStore
from ...tests.conformance import BlobStoreConformance
from ..stores import LocalBlobStore


class TestLocalConformance(BlobStoreConformance):
    @pytest.fixture
    def store(self, tmp_path):
        return SyncToAsyncBlobStore(LocalBlobStore(str(tmp_path)))


class TestLocalNoFsyncConformance(BlobStoreConformance):
    @pytest.fixture
    def store(self, tmp_path):
        return SyncToAsyncBlobStore(LocalBlobStore(str(tmp_path), config=LocalBlobStore.Config(no_fsync=True)))
