import uuid

import pytest

from omcore import dataclasses as dc
from omcore import lang
from omcore.http import all as http

from ...adapters import AsyncToSyncBlobStore
from ...adapters import SyncToAsyncBlobStore
from ...prefixes import PrefixedBlobStore
from ...tests.conformance import BlobStoreConformance
from ...tests.runners import SyncAwaitScenarioRunner
from ..stores import S3_MOCK_CONFIG
from .clients import S3_TEST_CLIENTS
from .clients import has_httpx
from .harness import HarnessS3


with lang.auto_proxy_import(globals()):
    from omcore.http.clients.pipelines import sync as _pipelines_sync


pytestmark = pytest.mark.integration


MIB = 1024 * 1024

S3MOCK_TEST_CONFIG = dc.replace(
    S3_MOCK_CONFIG,
    part_size=5 * MIB,  # the minimum s3mock enforces, like AWS
    list_page_size=7,
    delete_batch_size=4,
)


class TestS3MockConformance(BlobStoreConformance):
    large_size = 11 * MIB
    xfail_astral_ordering = True  # s3mock sorts listings by UTF-16 code units
    xfail_conditional_races = True  # s3mock checks preconditions non-atomically: racing writers can both win

    @pytest.fixture(params=S3_TEST_CLIENTS, ids=lambda c: c.id)
    def s3_client(self, request):
        c = request.param
        if c.needs_httpx and not has_httpx():
            pytest.skip('httpx not available')
        return c

    @pytest.fixture
    def store(self, harness, s3_client):
        st = harness[HarnessS3].store(config=S3MOCK_TEST_CONFIG, http_client=s3_client.make())
        return PrefixedBlobStore(st, f'{uuid.uuid7().hex}/')

    @pytest.fixture
    def runner(self, s3_client):
        return s3_client.make_runner()


class TestS3MockAdapterRoundTripConformance(BlobStoreConformance):
    """The sync facade: an async S3 store over a sync http client, driven through AsyncToSyncBlobStore."""

    large_size = 11 * MIB
    xfail_astral_ordering = True
    xfail_conditional_races = True

    @pytest.fixture
    def store(self, harness):
        st = harness[HarnessS3].store(
            config=S3MOCK_TEST_CONFIG,
            http_client=http.SyncAsyncHttpClient(_pipelines_sync.IoPipelineHttpClient()),
        )
        return SyncToAsyncBlobStore(AsyncToSyncBlobStore(PrefixedBlobStore(st, f'{uuid.uuid7().hex}/')))

    @pytest.fixture
    def runner(self):
        return SyncAwaitScenarioRunner()
