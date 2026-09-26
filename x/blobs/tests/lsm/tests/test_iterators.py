import pytest

from omcore import lang

from ..iterators import drop_tombstones
from ..iterators import merge_newest_wins
from ..memtables import iter_records
from ..records import LsmRecord


def _r(k, v):
    return LsmRecord(k.encode(), v.encode() if v is not None else None)


def _merge(*srcs, tombstones=True):
    it = merge_newest_wins([iter_records(s) for s in srcs])
    if not tombstones:
        it = drop_tombstones(it)
    return [(r.key.decode(), r.value.decode() if r.value is not None else None) for r in lang.sync_async_list(it)]


def test_newest_wins():
    newest = [_r('a', '1'), _r('c', None)]
    middle = [_r('a', '0'), _r('b', '2'), _r('c', '3')]
    oldest = [_r('b', 'x'), _r('d', '4')]
    assert _merge(newest, middle, oldest) == [('a', '1'), ('b', '2'), ('c', None), ('d', '4')]
    assert _merge(newest, middle, oldest, tombstones=False) == [('a', '1'), ('b', '2'), ('d', '4')]


def test_empty_sources():
    assert _merge() == []
    assert _merge([], []) == []
    assert _merge([], [_r('a', '1')]) == [('a', '1')]


def test_unsorted_source():
    with pytest.raises(ValueError):  # noqa
        _merge([_r('b', '1'), _r('a', '2')])
