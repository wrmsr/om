from ..frozen import FrozenDict
from ..frozen import FrozenList
from ..frozen import frozendict


def test_frozendict():
    fd: frozendict[int, int] = frozendict([(1, 2), (3, 4)])
    assert fd[3] == 4


def test_frozendict_existing_instance():
    fd: FrozenDict[str, int] = FrozenDict({'a': 1})

    assert FrozenDict(fd) is fd
    assert fd == FrozenDict({'a': 1})


def test_frozendict_does_not_reuse_other_frozen_collections():
    fd: FrozenDict[str, int] = FrozenDict(FrozenList([('a', 1)]))

    assert type(fd) is FrozenDict
    assert fd == FrozenDict({'a': 1})


def test_frozendict_persistent_updates():
    fd: FrozenDict[str, int] = FrozenDict({'a': 1})

    updated = fd.with_('b', 2)
    assert updated == FrozenDict({'a': 1, 'b': 2})
    assert fd == FrozenDict({'a': 1})
    assert updated.without('a') == FrozenDict({'b': 2})
    assert updated.default('b', 3) is updated
    assert updated.default('c', 3) == FrozenDict({'a': 1, 'b': 2, 'c': 3})


def test_frozendict_hash_does_not_require_comparable_keys():
    left: FrozenDict[object, str] = FrozenDict({1: 'a', 'b': 'c'})
    right: FrozenDict[object, str] = FrozenDict({'b': 'c', 1: 'a'})

    assert hash(left) == hash(right)
