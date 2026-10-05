"""
The core LSM tests, rerun over S3BlobStore against s3mock. They are imported by name so pytest collects them here, where
the `store` fixture provides a fresh prefix of the s3mock bucket over a sync http client (they drive with sync_await).
The model scenario also runs on a real event loop over the asyncio pipelines client.
"""
import uuid

import pytest

from omcore import lang
from omcore.http import all as http

from ...prefixes import PrefixedBlobStore
from ...tests.lsm.scenarios import run_model_scenario
from ...tests.lsm.tests.test_lsm import test_auto_flush_and_compact  # noqa
from ...tests.lsm.tests.test_lsm import test_crash_between_upload_and_commit  # noqa
from ...tests.lsm.tests.test_lsm import test_fencing  # noqa
from ...tests.lsm.tests.test_lsm import test_indeterminate_commit_lost_to_rival  # noqa
from ...tests.lsm.tests.test_lsm import test_indeterminate_commit_resolves  # noqa
from ...tests.lsm.tests.test_lsm import test_model  # noqa
from ...tests.lsm.tests.test_lsm import test_snapshot_isolation_and_expiry  # noqa
from ...tests.lsm.tests.test_lsm import test_unresolvable_commit_breaks  # noqa
from ...tests.runners import AsyncioScenarioRunner
from .harness import HarnessS3


with lang.auto_proxy_import(globals()):
    from omcore.http.clients.pipelines import asyncio as _pipelines_asyncio
    from omcore.http.clients.pipelines import sync as _pipelines_sync


pytestmark = pytest.mark.integration


@pytest.fixture
def store(harness):
    st = harness[HarnessS3].store(http_client=http.SyncAsyncHttpClient(_pipelines_sync.IoPipelineHttpClient()))
    return PrefixedBlobStore(st, f'{uuid.uuid7().hex}/')


@pytest.mark.parametrize('seed', [101, 102])
def test_model_asyncio(harness, seed):
    st = harness[HarnessS3].store(http_client=_pipelines_asyncio.AsyncioIoPipelineAsyncHttpClient())
    ps = PrefixedBlobStore(st, f'{uuid.uuid7().hex}/')
    stats = AsyncioScenarioRunner().run(lambda: run_model_scenario(ps, seed=seed, ops=200))
    assert stats.flushes + stats.compactions + stats.reopens > 0
