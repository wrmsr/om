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
from .interfaces import ContainerKind
from .interfaces import DataKind
from .interfaces import Factory
from .interfaces import Implementation


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

try:
    from ...stl import _stl as _stl_cext  # type: ignore
except ImportError:
    _stl_cext = None


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


def _stl_factory(cls_name: str, *dtypes: str) -> Factory:
    if _stl_cext is None:
        def unavailable(items: ta.Iterable[ta.Any]) -> ta.Any:
            raise RuntimeError('stl extension is unavailable')

        return unavailable

    cls = getattr(_stl_cext, cls_name)

    def make(items: ta.Iterable[ta.Any]) -> ta.Any:
        return cls(*dtypes, items)

    return make


_STL_AVAILABLE = _stl_cext is not None
_STL_UNAVAILABLE_REASON = 'stl extension is not built'


_STL_DATA_KINDS: ta.Mapping[str, DataKind] = {
    'int64': DataKind.INT,
    'object': DataKind.OBJECT,
}


def _stl_set_implementation(cls_name: str, name: str, suites: tuple[str, ...], dtype: str) -> Implementation:
    return Implementation(
        f'om/{name}/{dtype}',
        suites,
        ContainerKind.SET,
        _stl_factory(cls_name, dtype),
        key_kind=_STL_DATA_KINDS[dtype],
        available=_STL_AVAILABLE,
        unavailable_reason=_STL_UNAVAILABLE_REASON,
    )


def _stl_map_implementation(cls_name: str, name: str, suites: tuple[str, ...], kd: str, vd: str) -> Implementation:
    return Implementation(
        f'om/{name}/{kd}-{vd}',
        suites,
        ContainerKind.MAPPING,
        _stl_factory(cls_name, kd, vd),
        key_kind=_STL_DATA_KINDS[kd],
        value_kind=_STL_DATA_KINDS[vd],
        available=_STL_AVAILABLE,
        unavailable_reason=_STL_UNAVAILABLE_REASON,
    )


# The stl containers are dtype-specialized, so each dtype combination is registered as its own implementation with
# matching key / value data kinds - the 'object' variants store (and compare) real python objects, while the 'int64'
# variants exercise the unboxed storage. The object-dtype Vector still receives ints (the sequence workloads are
# arithmetic), measuring its boxed storage against the specialized variant on identical data.
def _stl_implementations() -> tuple[Implementation, ...]:
    return (
        *[
            _stl_set_implementation('Set', 'stl-set', ('set', 'sorted_collection'), dtype)
            for dtype in ('int64', 'object')
        ],
        *[
            _stl_set_implementation('UnorderedSet', 'stl-unordered-set', ('set',), dtype)
            for dtype in ('int64', 'object')
        ],
        *[
            _stl_map_implementation('Map', 'stl-map', ('sorted_mutable_mapping',), kd, vd)
            for kd in ('int64', 'object')
            for vd in ('int64', 'object')
        ],
        *[
            _stl_map_implementation('UnorderedMap', 'stl-unordered-map', ('mutable_mapping',), kd, vd)
            for kd in ('int64', 'object')
            for vd in ('int64', 'object')
        ],
        Implementation(
            'om/stl-vector/int64',
            ('mutable_sequence',),
            ContainerKind.SEQUENCE,
            _stl_factory('Vector', 'int64'),
            available=_STL_AVAILABLE,
            unavailable_reason=_STL_UNAVAILABLE_REASON,
        ),
        Implementation(
            'om/stl-vector/object',
            ('mutable_sequence',),
            ContainerKind.SEQUENCE,
            _stl_factory('Vector', 'object'),
            available=_STL_AVAILABLE,
            unavailable_reason=_STL_UNAVAILABLE_REASON,
        ),
    )


##


IMPLEMENTATIONS: tuple[Implementation, ...] = (
    Implementation(
        'builtin/list',
        ('mutable_sequence',),
        ContainerKind.SEQUENCE,
        list,
    ),
    Implementation(
        'builtin/tuple',
        ('sequence',),
        ContainerKind.SEQUENCE,
        tuple,
    ),
    Implementation(
        'om/frozen-list',
        ('sequence',),
        ContainerKind.SEQUENCE,
        col.frozenlist,
    ),
    Implementation(
        'om/ranked-seq',
        ('sequence',),
        ContainerKind.SEQUENCE,
        col.RankedSeq,
    ),
    Implementation(
        'om/tuple-persistent-seq',
        ('persistent_sequence',),
        ContainerKind.SEQUENCE,
        TuplePersistentSequence,
    ),
    Implementation(
        'om/btree-seq/python',
        ('persistent_sequence',),
        ContainerKind.SEQUENCE,
        _new_py_btree_seq,
    ),
    Implementation(
        'om/btree-seq/cext',
        ('persistent_sequence',),
        ContainerKind.SEQUENCE,
        _new_cext_btree_seq,
        available=_btreeseq_cext is not None,
        unavailable_reason='btreeseq extension is not built',
    ),

    Implementation(
        'builtin/dict',
        ('mutable_mapping',),
        ContainerKind.MAPPING,
        dict,
    ),
    Implementation(
        'stdlib/ordered-dict',
        ('mutable_mapping',),
        ContainerKind.MAPPING,
        collections.OrderedDict,
    ),
    Implementation(
        'stdlib/mapping-proxy',
        ('mapping',),
        ContainerKind.MAPPING,
        _new_mapping_proxy,
    ),
    Implementation(
        'stdlib/weak-key-dictionary',
        ('mutable_mapping',),
        ContainerKind.MAPPING,
        weakref.WeakKeyDictionary,
        key_kind=DataKind.OBJECT,
    ),
    Implementation(
        'om/frozen-dict',
        ('mapping',),
        ContainerKind.MAPPING,
        col.frozendict,
    ),
    Implementation(
        'om/fixed-map/python',
        ('mapping',),
        ContainerKind.MAPPING,
        _new_py_fixed_map,
    ),
    Implementation(
        'om/fixed-map/cext',
        ('mapping',),
        ContainerKind.MAPPING,
        _new_cext_fixed_map,
        available=_fixedmap_cext is not None,
        unavailable_reason='fixedmap extension is not built',
    ),
    Implementation(
        'om/bi-map',
        ('mapping',),
        ContainerKind.MAPPING,
        col.make_bi_map,
    ),
    Implementation(
        'om/mutable-bi-map',
        ('mutable_mapping',),
        ContainerKind.MAPPING,
        col.make_mutable_bi_map,
    ),
    Implementation(
        'om/identity-key-dict',
        ('mutable_mapping',),
        ContainerKind.MAPPING,
        col.IdentityKeyDict,
        key_kind=DataKind.OBJECT,
    ),
    Implementation(
        'om/identity-weak-key-dict',
        ('mutable_mapping',),
        ContainerKind.MAPPING,
        col.IdentityWeakKeyDictionary,
        key_kind=DataKind.OBJECT,
    ),
    Implementation(
        'om/hash-eq-map',
        ('mutable_mapping',),
        ContainerKind.MAPPING,
        _new_hash_eq_map,
    ),
    Implementation(
        'om/skip-list-dict',
        ('sorted_mutable_mapping',),
        ContainerKind.MAPPING,
        col.SkipListDict,
    ),
    Implementation(
        'om/dict-persistent-map',
        ('persistent_mapping',),
        ContainerKind.MAPPING,
        DictPersistentMapping,
    ),
    Implementation(
        'om/hamt-map',
        ('persistent_mapping',),
        ContainerKind.MAPPING,
        col.new_hamt_map,
        available=col.is_hamt_available(),
        unavailable_reason='hamt extension is not built',
    ),
    Implementation(
        'om/treap-map',
        ('persistent_mapping', 'sorted_mapping'),
        ContainerKind.MAPPING,
        col.new_treap_map,
    ),
    Implementation(
        'om/btree-map/python',
        ('persistent_mapping', 'sorted_mapping'),
        ContainerKind.MAPPING,
        _new_py_btree_map,
    ),
    Implementation(
        'om/btree-map/cext',
        ('persistent_mapping', 'sorted_mapping'),
        ContainerKind.MAPPING,
        _new_cext_btree_map,
        available=_btreemap_cext is not None,
        unavailable_reason='btreemap extension is not built',
    ),

    Implementation(
        'builtin/frozenset',
        ('abstract_set',),
        ContainerKind.SET,
        frozenset,
    ),
    Implementation(
        'builtin/set',
        ('set',),
        ContainerKind.SET,
        set,
    ),
    Implementation(
        'stdlib/weak-set',
        ('set',),
        ContainerKind.SET,
        weakref.WeakSet,
        key_kind=DataKind.OBJECT,
    ),
    Implementation(
        'om/ordered-frozen-set',
        ('abstract_set',),
        ContainerKind.SET,
        col.OrderedFrozenSet,
    ),
    Implementation(
        'om/ordered-set',
        ('set',),
        ContainerKind.SET,
        col.OrderedSet,
    ),
    Implementation(
        'om/identity-set',
        ('set',),
        ContainerKind.SET,
        col.IdentitySet,
        key_kind=DataKind.OBJECT,
    ),
    Implementation(
        'om/identity-weak-set',
        ('set',),
        ContainerKind.SET,
        col.IdentityWeakSet,
        key_kind=DataKind.OBJECT,
    ),

    Implementation(
        'om/skip-list',
        ('sorted_collection',),
        ContainerKind.SET,
        _new_skip_list,
    ),

    *_stl_implementations(),
)
