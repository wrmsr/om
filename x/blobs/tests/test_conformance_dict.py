import uuid

import pytest

from ..adapters import AsyncToSyncBlobStore
from ..adapters import SyncToAsyncBlobStore
from ..caps import BlobCapability
from ..dicts import DictBlobStore
from ..prefixes import PrefixedBlobStore
from .conformance import BlobStoreConformance
from .runners import AsyncioScenarioRunner


class TestDictConformance(BlobStoreConformance):
    @pytest.fixture
    def store(self):
        return SyncToAsyncBlobStore(DictBlobStore())


class TestDictNoCapsConformance(BlobStoreConformance):
    @pytest.fixture
    def store(self):
        return SyncToAsyncBlobStore(DictBlobStore(capabilities=BlobCapability(0)))


class TestDictPutIfAbsentOnlyConformance(BlobStoreConformance):
    @pytest.fixture
    def store(self):
        return SyncToAsyncBlobStore(DictBlobStore(capabilities=BlobCapability.PUT_IF_ABSENT))


class TestPrefixedDictConformance(BlobStoreConformance):
    @pytest.fixture
    def store(self):
        d = DictBlobStore()
        d.put('neighbor', b'')
        d.put('zzz/x', b'')
        return PrefixedBlobStore(SyncToAsyncBlobStore(d), f'{uuid.uuid7().hex}/')


class TestDictAdapterRoundTripConformance(BlobStoreConformance):
    @pytest.fixture
    def store(self):
        return SyncToAsyncBlobStore(AsyncToSyncBlobStore(SyncToAsyncBlobStore(DictBlobStore())))


class TestDictAsyncioConformance(BlobStoreConformance):
    @pytest.fixture
    def store(self):
        return SyncToAsyncBlobStore(DictBlobStore())

    @pytest.fixture
    def runner(self):
        return AsyncioScenarioRunner()
