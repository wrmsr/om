import pytest

from ...adapters import SyncToAsyncBlobStore
from ...tests.conformance import BlobStoreConformance
from ..stores import LocalBlobStore


class TestLocalConformance(BlobStoreConformance):
    LONG_KEYS_LENGTH = 160

    @pytest.fixture
    def store(self, tmp_path):
        return SyncToAsyncBlobStore(LocalBlobStore(str(tmp_path)))


class TestLocalNoFsyncConformance(BlobStoreConformance):
    LONG_KEYS_LENGTH = 160

    @pytest.fixture
    def store(self, tmp_path):
        return SyncToAsyncBlobStore(LocalBlobStore(str(tmp_path), config=LocalBlobStore.Config(no_fsync=True)))
