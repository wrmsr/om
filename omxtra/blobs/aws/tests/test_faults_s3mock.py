import random
import re
import uuid

import pytest

from omcore import lang
from omcore.asyncs.asynclite import all as asl
from omcore.http import all as http

from .... import blobs
from ...manifests import ManifestStore
from ..retries import SimpleS3RetryPolicy
from .faults import FaultInjectingAsyncHttpClient
from .faults import HttpFault
from .faults import RaiseAfter
from .faults import RecordingAsyncHttpClient
from .faults import Respond
from .faults import refuse
from .harness import HarnessS3


with lang.auto_proxy_import(globals()):
    from omcore.http.clients.pipelines import sync as _pipelines_sync


pytestmark = pytest.mark.integration


class NoSleeps(asl.Sleeps):
    async def sleep(self, delay):
        pass


def _policy():
    return SimpleS3RetryPolicy(NoSleeps(), rng=random.Random(0))


class _Rig:
    def __init__(self, harness, *, policy=None):
        self.rec = RecordingAsyncHttpClient(http.SyncAsyncHttpClient(_pipelines_sync.IoPipelineHttpClient()))
        self.faults = FaultInjectingAsyncHttpClient(self.rec)
        self.store = harness[HarnessS3].store(http_client=self.faults, retry_policy=policy)
        self.plain = harness[HarnessS3].store(
            http_client=http.SyncAsyncHttpClient(_pipelines_sync.IoPipelineHttpClient()),
        )
        self.prefix = f'{uuid.uuid7().hex}/'

    def key(self, name):
        return self.prefix + name

    def path(self, name):
        return re.compile(r'.*/' + re.escape(self.key(name)))

    def sent(self, method, name):
        return [r for r in self.rec.requests() if r.method == method and r.path.endswith(self.key(name))]


def run(aw):
    return lang.sync_await(aw)


def test_read_raise_after(harness):
    r = _Rig(harness)
    run(r.plain.put(r.key('k'), b'v'))
    r.faults.add(HttpFault(method='GET', path=r.path('k'), action=RaiseAfter()))
    with pytest.raises(blobs.BlobTransportError):
        run(r.store.get(r.key('k')))

    r = _Rig(harness, policy=_policy())
    run(r.plain.put(r.key('k'), b'v'))
    r.faults.add(HttpFault(method='GET', path=r.path('k'), action=RaiseAfter()))
    assert run(r.store.get(r.key('k'))).data == b'v'
    assert len(r.sent('GET', 'k')) == 2


def test_conditional_put_raise_after_is_indeterminate(harness):
    r = _Rig(harness, policy=_policy())
    r.faults.add(HttpFault(method='PUT', path=r.path('k'), action=RaiseAfter()))
    with pytest.raises(blobs.BlobIndeterminateError):
        run(r.store.put(r.key('k'), b'mine', cond=blobs.IfAbsent()))
    assert len(r.sent('PUT', 'k')) == 1  # never retried
    assert run(r.plain.get(r.key('k'))).data == b'mine'  # but it did land


def test_conflict(harness):
    r = _Rig(harness)
    r.faults.add(HttpFault(method='PUT', path=r.path('k'), action=Respond(409, 'ConditionalRequestConflict')))
    with pytest.raises(blobs.BlobConflictError):
        run(r.store.put(r.key('k'), b'v', cond=blobs.IfAbsent()))

    r = _Rig(harness, policy=_policy())
    r.faults.add(HttpFault(method='PUT', path=r.path('k'), action=Respond(409, 'ConditionalRequestConflict')))
    run(r.store.put(r.key('k'), b'v', cond=blobs.IfAbsent()))
    assert run(r.plain.get(r.key('k'))).data == b'v'


def test_throttled(harness):
    r = _Rig(harness)
    r.faults.add(HttpFault(method='PUT', path=r.path('k'), action=Respond(503, 'SlowDown')))
    with pytest.raises(blobs.BlobThrottledError):
        run(r.store.put(r.key('k'), b'v'))

    r = _Rig(harness, policy=_policy())
    r.faults.add(HttpFault(method='PUT', path=r.path('k'), action=Respond(503, 'SlowDown')))
    run(r.store.put(r.key('k'), b'v', cond=blobs.IfAbsent()))
    assert run(r.plain.get(r.key('k'))).data == b'v'


def test_refused_is_retried_for_conditional_writes(harness):
    r = _Rig(harness, policy=_policy())
    r.faults.add(HttpFault(method='PUT', path=r.path('k'), action=refuse()))
    run(r.store.put(r.key('k'), b'v', cond=blobs.IfAbsent()))
    assert len(r.sent('PUT', 'k')) == 1


def test_manifest_commit_resolves_through_read_back(harness):
    r = _Rig(harness)
    ms = ManifestStore(r.store, prefix=r.key('m'))
    r.faults.add(HttpFault(method='PUT', path=re.compile(r'.*/m/\d+'), action=RaiseAfter()))
    run(ms.commit(1, b'w1:1'))
    assert run(ms.read(1)) == b'w1:1'
    assert run(ms.find_latest()) == 1


def test_complete_error_200(harness):
    r = _Rig(harness, policy=_policy())
    r.faults.add(HttpFault(method='POST', path=r.path('big'), query='uploadId', action=Respond(500, 'InternalError')))
    data = b'z' * (6 * 1024 * 1024)

    async def inner():
        async with r.store.open_writer(r.key('big')) as w:
            await w.write(data)
            await w.commit()

    run(inner())
    assert run(r.plain.get(r.key('big'))).data == data
