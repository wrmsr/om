import collections
import operator
import types
import typing as ta
import weakref

from .... import collections as col
from ...btreemap import _btreemap_py
from ...btreeseq import _btreeseq_py
from ...fixedmap import _fixedmap_py
from ...persistent import DictPersistentMapping
from ...persistent import TuplePersistentSequence
from .interfaces import DataKind
from .interfaces import Implementation
from .interfaces import KeyKind


try:
    from ...btreemap import _btreemap as _btreemap_cext  # type: ignore
except ImportError:
    _btreemap_cext = None

try:
    from ...btreeseq import _btreeseq as _btreeseq_cext  # type: ignore
except ImportError:
    _btreeseq_cext = None

try:
    from ...fixedmap import _fixedmap as _fixedmap_cext  # type: ignore
except ImportError:
    _fixedmap_cext = None


##


class _PyBtreeMap(col.BtreeMap):
    _backend = _btreemap_py


class _CextBtreeMap(col.BtreeMap):
    _backend = _btreemap_cext


class _PyBtreeSeq(col.BtreeSeq):
    _backend = _btreeseq_py


class _CextBtreeSeq(col.BtreeSeq):
    _backend = _btreeseq_cext


def _new_btree_map(
        cls: type[col.BtreeMap],
        items: ta.Iterable[tuple[ta.Any, ta.Any]],
) -> col.BtreeMap:
    result = cls(_root=None, _cmp=None)
    for key, value in items:
        result = result.with_(key, value)
    return result


def _new_py_btree_map(items: ta.Iterable[tuple[ta.Any, ta.Any]]) -> col.BtreeMap:
    return _new_btree_map(_PyBtreeMap, items)


def _new_cext_btree_map(items: ta.Iterable[tuple[ta.Any, ta.Any]]) -> col.BtreeMap:
    return _new_btree_map(_CextBtreeMap, items)


def _new_py_btree_seq(items: ta.Iterable[ta.Any]) -> col.BtreeSeq:
    return _PyBtreeSeq(_root=_btreeseq_py.from_iterable(items))


def _new_cext_btree_seq(items: ta.Iterable[ta.Any]) -> col.BtreeSeq:
    if _btreeseq_cext is None:
        raise RuntimeError('btreeseq extension is unavailable')
    return _CextBtreeSeq(_root=_btreeseq_cext.from_iterable(items))


def _new_fixed_map(backend: ta.Any, items: ta.Iterable[tuple[ta.Any, ta.Any]]) -> ta.Mapping:
    pairs = tuple(items)
    return backend.FixedMap(
        backend.FixedMapKeys([key for key, _ in pairs]),
        [value for _, value in pairs],
    )


def _new_py_fixed_map(items: ta.Iterable[tuple[ta.Any, ta.Any]]) -> ta.Mapping:
    return _new_fixed_map(_fixedmap_py, items)


def _new_cext_fixed_map(items: ta.Iterable[tuple[ta.Any, ta.Any]]) -> ta.Mapping:
    if _fixedmap_cext is None:
        raise RuntimeError('fixedmap extension is unavailable')
    return _new_fixed_map(_fixedmap_cext, items)


##


def _new_mapping_proxy(items: ta.Iterable[tuple[ta.Any, ta.Any]]) -> ta.Mapping:
    return types.MappingProxyType(dict(items))


def _new_hash_eq_map(items: ta.Iterable[tuple[ta.Any, ta.Any]]) -> col.HashEqMap:
    return col.HashEqMap(col.hash_eq(hash, operator.eq), items)


def _new_skip_list(items: ta.Iterable[ta.Any]) -> col.SkipList:
    result: col.SkipList[ta.Any] = col.SkipList()
    for item in items:
        result.add(item)
    return result


##


IMPLEMENTATIONS: tuple[Implementation, ...] = (
    Implementation('builtin/list', ('mutable_sequence',), DataKind.SEQUENCE, list),
    Implementation('builtin/tuple', ('sequence',), DataKind.SEQUENCE, tuple),
    Implementation('om/frozen-list', ('sequence',), DataKind.SEQUENCE, col.frozenlist),
    Implementation('om/ranked-seq', ('sequence',), DataKind.SEQUENCE, col.RankedSeq),
    Implementation('om/tuple-persistent-seq', ('persistent_sequence',), DataKind.SEQUENCE, TuplePersistentSequence),
    Implementation('om/btree-seq/python', ('persistent_sequence',), DataKind.SEQUENCE, _new_py_btree_seq),
    Implementation(
        'om/btree-seq/cext',
        ('persistent_sequence',),
        DataKind.SEQUENCE,
        _new_cext_btree_seq,
        available=_btreeseq_cext is not None,
        unavailable_reason='btreeseq extension is not built',
    ),

    Implementation('builtin/dict', ('mutable_mapping',), DataKind.MAPPING, dict),
    Implementation('stdlib/ordered-dict', ('mutable_mapping',), DataKind.MAPPING, collections.OrderedDict),
    Implementation('stdlib/mapping-proxy', ('mapping',), DataKind.MAPPING, _new_mapping_proxy),
    Implementation(
        'stdlib/weak-key-dictionary',
        ('mutable_mapping',),
        DataKind.MAPPING,
        weakref.WeakKeyDictionary,
        KeyKind.OBJECT,
    ),
    Implementation('om/frozen-dict', ('mapping',), DataKind.MAPPING, col.frozendict),
    Implementation('om/fixed-map/python', ('mapping',), DataKind.MAPPING, _new_py_fixed_map),
    Implementation(
        'om/fixed-map/cext',
        ('mapping',),
        DataKind.MAPPING,
        _new_cext_fixed_map,
        available=_fixedmap_cext is not None,
        unavailable_reason='fixedmap extension is not built',
    ),
    Implementation('om/bi-map', ('mapping',), DataKind.MAPPING, col.make_bi_map),
    Implementation('om/mutable-bi-map', ('mutable_mapping',), DataKind.MAPPING, col.make_mutable_bi_map),
    Implementation(
        'om/identity-key-dict',
        ('mutable_mapping',),
        DataKind.MAPPING,
        col.IdentityKeyDict,
        KeyKind.OBJECT,
    ),
    Implementation(
        'om/identity-weak-key-dict',
        ('mutable_mapping',),
        DataKind.MAPPING,
        col.IdentityWeakKeyDictionary,
        KeyKind.OBJECT,
    ),
    Implementation('om/hash-eq-map', ('mutable_mapping',), DataKind.MAPPING, _new_hash_eq_map),
    Implementation('om/skip-list-dict', ('sorted_mutable_mapping',), DataKind.MAPPING, col.SkipListDict),
    Implementation('om/dict-persistent-map', ('persistent_mapping',), DataKind.MAPPING, DictPersistentMapping),
    Implementation(
        'om/hamt-map',
        ('persistent_mapping',),
        DataKind.MAPPING,
        col.new_hamt_map,
        available=col.is_hamt_available(),
        unavailable_reason='hamt extension is not built',
    ),
    Implementation(
        'om/treap-map',
        ('persistent_mapping', 'sorted_mapping'),
        DataKind.MAPPING,
        col.new_treap_map,
    ),
    Implementation(
        'om/btree-map/python',
        ('persistent_mapping', 'sorted_mapping'),
        DataKind.MAPPING,
        _new_py_btree_map,
    ),
    Implementation(
        'om/btree-map/cext',
        ('persistent_mapping', 'sorted_mapping'),
        DataKind.MAPPING,
        _new_cext_btree_map,
        available=_btreemap_cext is not None,
        unavailable_reason='btreemap extension is not built',
    ),

    Implementation('builtin/frozenset', ('abstract_set',), DataKind.SET, frozenset),
    Implementation('builtin/set', ('set',), DataKind.SET, set),
    Implementation(
        'stdlib/weak-set',
        ('set',),
        DataKind.SET,
        weakref.WeakSet,
        KeyKind.OBJECT,
    ),
    Implementation('om/ordered-frozen-set', ('abstract_set',), DataKind.SET, col.OrderedFrozenSet),
    Implementation('om/ordered-set', ('set',), DataKind.SET, col.OrderedSet),
    Implementation(
        'om/identity-set',
        ('set',),
        DataKind.SET,
        col.IdentitySet,
        KeyKind.OBJECT,
    ),
    Implementation(
        'om/identity-weak-set',
        ('set',),
        DataKind.SET,
        col.IdentityWeakSet,
        KeyKind.OBJECT,
    ),

    Implementation('om/skip-list', ('sorted_collection',), DataKind.SET, _new_skip_list),
)
