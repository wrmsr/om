import asyncio
import uuid

import pytest

from ...prefixes import PrefixedBlobStore
from ...tests.conformance import BlobStoreConformance
from ..subprocesses import remote_blob_store_subprocess
from .support import REMOTE_BLOBS_TEST_PYTHON
from .support import REMOTE_BLOBS_TEST_STORE_KWARGS
from .support import InProcessRemoteBlobStore
from .support import LoopScenarioRunner


##


class TestRemoteInProcessConformance(BlobStoreConformance):
    LONG_KEYS_LENGTH = 160

    @pytest.fixture
    def target(self, tmp_path):
        t = InProcessRemoteBlobStore(str(tmp_path), **REMOTE_BLOBS_TEST_STORE_KWARGS)
        try:
            yield t
        finally:
            t.close()

    @pytest.fixture
    def runner(self, target):
        return LoopScenarioRunner(target.loop)

    @pytest.fixture
    def store(self, target):
        return target.store


@pytest.fixture(scope='class')
def subprocess_target(tmp_path_factory):
    """One target process for the class, under the Python 3.8 venv when there is one; each test takes a prefix."""

    loop = asyncio.new_event_loop()
    try:
        cm = remote_blob_store_subprocess(
            str(tmp_path_factory.mktemp('remote-blobs')),
            python=REMOTE_BLOBS_TEST_PYTHON,
            no_fsync=True,
            **REMOTE_BLOBS_TEST_STORE_KWARGS,
        )
        store = loop.run_until_complete(cm.__aenter__())  # noqa
        try:
            yield loop, store
        finally:
            loop.run_until_complete(cm.__aexit__(None, None, None))  # noqa
    finally:
        loop.close()


class TestRemoteSubprocessConformance(BlobStoreConformance):
    LONG_KEYS_LENGTH = 160

    @pytest.fixture
    def runner(self, subprocess_target):
        return LoopScenarioRunner(subprocess_target[0])

    @pytest.fixture
    def store(self, subprocess_target):
        return PrefixedBlobStore(subprocess_target[1], f'{uuid.uuid4().hex}/')
