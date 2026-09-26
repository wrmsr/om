import random

import pytest

from omcore import lang

from ..adapters import SyncToAsyncBlobStore
from ..dicts import DictBlobStore
from ..errors import BlobPreconditionFailedError
from ..plans import BlobPlanError
from ..plans import finish_parallel_get
from ..plans import get_part
from ..plans import plan_parallel_get


DATA = bytes(i % 251 for i in range(10_000))


def _run_plan(store, key, part_size, *, seed=0):
    info = lang.sync_await(store.head(key))
    plan = plan_parallel_get(info, part_size=part_size)
    parts = list(plan.parts)
    random.Random(seed).shuffle(parts)
    got = {p.index: lang.sync_await(get_part(store, plan, p)) for p in parts}
    return plan, finish_parallel_get(plan, got)


@pytest.mark.parametrize('part_size', [1, 999, 1000, 3333, 10_000, 20_000])
def test_round_trip(part_size):
    d = DictBlobStore()
    d.put('k', DATA)
    plan, data = _run_plan(SyncToAsyncBlobStore(d), 'k', part_size)
    assert data == DATA
    assert len(plan.parts) == -(-len(DATA) // part_size)


def test_empty():
    d = DictBlobStore()
    d.put('e', b'')
    plan, data = _run_plan(SyncToAsyncBlobStore(d), 'e', 100)
    assert (plan.parts, data) == ([], b'')


def test_replaced_mid_plan():
    d = DictBlobStore()
    d.put('k', DATA)
    s = SyncToAsyncBlobStore(d)
    plan = plan_parallel_get(lang.sync_await(s.head('k')), part_size=1000)
    lang.sync_await(get_part(s, plan, plan.parts[0]))
    d.put('k', DATA[::-1])
    with pytest.raises(BlobPreconditionFailedError):
        lang.sync_await(get_part(s, plan, plan.parts[1]))


def test_incomplete():
    d = DictBlobStore()
    d.put('k', DATA)
    s = SyncToAsyncBlobStore(d)
    plan = plan_parallel_get(lang.sync_await(s.head('k')), part_size=4000)
    got = {p.index: lang.sync_await(get_part(s, plan, p)) for p in plan.parts[:-1]}
    with pytest.raises(BlobPlanError):
        finish_parallel_get(plan, got)
