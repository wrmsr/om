import collections.abc as cabc
import gc
import random
import sys
import threading
import weakref

import pytest

from .. import _stl as fc  # type: ignore


##


INT_DTYPES = [
    'int64-raise',
    'int64-clamp',
    'int64-wrap',
    'uint64-raise',
    'uint64-clamp',
    'uint64-wrap',
]

ALL_DTYPES = ['object', 'float64', *INT_DTYPES]

SET_CLASSES = [fc.Set, fc.UnorderedSet]
MAP_CLASSES = [fc.Map, fc.UnorderedMap]

INT64_MIN = -2 ** 63
INT64_MAX = 2 ** 63 - 1
UINT64_MAX = 2 ** 64 - 1


def sample_keys(dtype, n=40, seed=0):
    rnd = random.Random(seed)
    if dtype == 'object':
        return [rnd.choice(['a', 'b', 'c', 'dd', 'ee', 'f']) + str(rnd.randrange(10)) for _ in range(n)]
    if dtype == 'float64':
        return [round(rnd.uniform(-50.0, 50.0), 2) for _ in range(n)]
    return [rnd.randrange(0, 200) for _ in range(n)]


##
# dtypes


def test_dtypes_tuple():
    assert fc.DTYPES == (
        'object',
        'int64-raise',
        'int64-clamp',
        'int64-wrap',
        'uint64-raise',
        'uint64-clamp',
        'uint64-wrap',
        'float64',
    )


@pytest.mark.parametrize(('alias', 'canon'), [
    ('int64', 'int64-raise'),
    ('uint64', 'uint64-raise'),
    ('object', 'object'),
    ('float64', 'float64'),
])
def test_dtype_aliases(alias, canon):
    assert fc.Set(alias).dtype == canon
    assert fc.Vector(alias).dtype == canon
    m = fc.Map(alias, alias)
    assert m.key_type == canon
    assert m.value_type == canon


@pytest.mark.parametrize('bad', ['int32', 'Object', 'object ', '', 'float', 'object\x00junk', 'int64\x00'])
def test_bad_dtype(bad):
    with pytest.raises(ValueError):  # noqa
        fc.Set(bad)


##
# sets


@pytest.mark.parametrize('cls', SET_CLASSES)
@pytest.mark.parametrize('dtype', ALL_DTYPES)
def test_set_basic_vs_model(cls, dtype):
    ks = sample_keys(dtype)
    s = cls(dtype)
    model = set()
    for k in ks:
        s.add(k)
        model.add(k)
        assert k in s
        assert len(s) == len(model)
    assert sorted(s, key=repr) == sorted(model, key=repr)
    for k in ks[::3]:
        s.discard(k)
        model.discard(k)
    assert set(s) == model
    with pytest.raises(KeyError):
        s.remove(ks[0]) if ks[0] not in model else None
    while model:
        k = s.pop()
        assert k in model
        model.discard(k)
    assert len(s) == 0
    with pytest.raises(KeyError):
        s.pop()


@pytest.mark.parametrize('dtype', ALL_DTYPES)
def test_sorted_set_iteration_order(dtype):
    ks = sample_keys(dtype, seed=1)
    s = fc.Set(dtype, ks)
    assert list(s) == sorted(set(ks))
    assert list(reversed(s)) == sorted(set(ks))[::-1]


@pytest.mark.parametrize('cls', SET_CLASSES)
def test_set_ops(cls):
    a = cls('int64', [1, 2, 3])
    b = cls('int64', [2, 3, 4])
    assert sorted(a | b) == [1, 2, 3, 4]
    assert sorted(a & b) == [2, 3]
    assert sorted(a - b) == [1]
    assert sorted(b - a) == [4]
    assert sorted(a ^ b) == [1, 4]
    assert sorted(a | {9}) == [1, 2, 3, 9]
    assert sorted({9} | a) == [1, 2, 3, 9]
    assert sorted({1, 5} - a) == [5]
    assert type(a | b) is cls
    for other in ({2}, cls('int64', [2]), frozenset([2])):
        assert sorted(a & other) == [2]
    with pytest.raises(TypeError):
        a | 5


@pytest.mark.parametrize('cls', SET_CLASSES)
def test_set_inplace_ops(cls):
    a = cls('int64', [1, 2, 3])
    orig = a
    a |= [4, 5]
    assert a is orig and sorted(a) == [1, 2, 3, 4, 5]
    a -= [1, 5]
    assert a is orig and sorted(a) == [2, 3, 4]
    a ^= [2, 9]
    assert a is orig and sorted(a) == [3, 4, 9]
    a &= [3, 9, 77]
    assert a is orig and sorted(a) == [3, 9]
    a ^= a
    assert len(a) == 0
    b = cls('int64', [1])
    b -= b
    assert len(b) == 0


@pytest.mark.parametrize('cls', SET_CLASSES)
def test_set_inplace_failed_update_does_not_leak_rhs_iterator(cls):
    w = ['x']
    s = cls('int64', [1])
    base = sys.getrefcount(w)
    for _ in range(10):
        with pytest.raises(TypeError):
            s |= w
        with pytest.raises(TypeError):
            s ^= w
    assert sys.getrefcount(w) == base
    assert sorted(s) == [1]
    with pytest.raises(TypeError):
        s |= 5
    with pytest.raises(TypeError):
        s ^= 5


@pytest.mark.parametrize('cls', SET_CLASSES)
def test_set_comparisons(cls):
    a = cls('int64', [1, 2])
    assert a == {1, 2}
    assert a == cls('int64', [2, 1])
    assert a == fc.Set('object', [1, 2])
    assert a != {1, 3}
    assert a <= {1, 2}
    assert not (a < {1, 2})
    assert a < {1, 2, 3}
    assert a >= {1, 2}
    assert a > {1}
    assert not a.isdisjoint({2, 9})
    assert a.isdisjoint({8, 9})
    assert (a == [1, 2]) is False
    with pytest.raises(TypeError):
        _ = a < [1, 2]
    with pytest.raises(TypeError):
        hash(a)


@pytest.mark.parametrize('cls', SET_CLASSES)
def test_set_update_multi(cls):
    s = cls('int64')
    s.update([1, 2], (3,), cls('int64', [4]))
    assert sorted(s) == [1, 2, 3, 4]


##
# overflow


@pytest.mark.parametrize('make', [
    lambda dt: (fc.Set(dt), lambda c, x: c.add(x), lambda c: list(c)),
    lambda dt: (fc.Vector(dt), lambda c, x: c.append(x), lambda c: list(c)),
    lambda dt: (fc.UnorderedMap(dt, 'object'), lambda c, x: c.__setitem__(x, None), lambda c: sorted(c)),
])
def test_overflow_modes(make):
    c, add, dump = make('int64-raise')
    with pytest.raises(OverflowError):
        add(c, INT64_MAX + 1)
    with pytest.raises(OverflowError):
        add(c, INT64_MIN - 1)
    add(c, INT64_MAX)
    add(c, INT64_MIN)
    assert sorted(dump(c)) == [INT64_MIN, INT64_MAX]

    c, add, dump = make('int64-clamp')
    add(c, 2 ** 100)
    add(c, -2 ** 100)
    assert sorted(dump(c)) == [INT64_MIN, INT64_MAX]

    c, add, dump = make('int64-wrap')
    add(c, INT64_MAX + 1)
    assert dump(c) == [INT64_MIN]

    c, add, dump = make('uint64-raise')
    with pytest.raises(OverflowError):
        add(c, -1)
    with pytest.raises(OverflowError):
        add(c, UINT64_MAX + 1)

    c, add, dump = make('uint64-clamp')
    add(c, -5)
    add(c, 2 ** 70)
    assert sorted(dump(c)) == [0, UINT64_MAX]

    c, add, dump = make('uint64-wrap')
    add(c, -1)
    add(c, 2 ** 64 + 3)
    assert sorted(dump(c)) == [3, UINT64_MAX]


def test_int_coercion():
    s = fc.Set('int64')
    with pytest.raises(TypeError):
        s.add(1.5)
    with pytest.raises(TypeError):
        s.add('1')
    s.add(True)
    assert list(s) == [1]

    class Ix:
        def __index__(self):
            return 7

    s.add(Ix())
    assert list(s) == [1, 7]


def test_float64_coercion():
    s = fc.Set('float64')
    s.add(1)  # int -> float ok
    assert list(s) == [1.0]
    with pytest.raises(TypeError):
        s.add('x')
    with pytest.raises(OverflowError):
        s.add(2 ** 2000)


def test_float64_nan_and_zero_keys():
    nan = float('nan')
    for cls in SET_CLASSES:
        s = cls('float64', [nan, nan, -0.0, 0.0, 1.0])
        assert len(s) == 3
        assert nan in s
        assert 0.0 in s and -0.0 in s
    m = fc.Map('float64', 'object')
    m[nan] = 'a'
    m[float('nan')] = 'b'
    assert len(m) == 1 and m[nan] == 'b'
    v = fc.Vector('float64', [nan, 2.0])
    assert nan in v
    assert v.index(nan) == 0
    assert v.count(nan) == 1


##
# probe semantics


def test_probe_semantics():
    m = fc.Map('int64', 'object')
    assert 'a' not in m
    assert 1.5 not in m
    with pytest.raises(KeyError):
        _ = m['a']
    with pytest.raises(KeyError):
        del m['a']
    assert m.get('a') is None
    assert m.pop('a', 'd') == 'd'
    s = fc.UnorderedSet('uint64', [1])
    assert -1 not in s
    assert 'x' not in s
    s.discard('x')  # no-op, no raise
    with pytest.raises(KeyError):
        s.remove('x')
    v = fc.Vector('int64', [1])
    assert 'x' not in v
    assert v.count('x') == 0
    with pytest.raises(ValueError):  # noqa
        v.index('x')
    # storing still type-checks
    with pytest.raises(TypeError):
        m['a'] = 1
    # object containers propagate from __eq__/__hash__ probes
    mo = fc.UnorderedMap('object', 'object')

    class BadHash:
        def __hash__(self):
            raise ZeroDivisionError

    with pytest.raises(ZeroDivisionError):
        _ = BadHash() in mo


##
# maps


@pytest.mark.parametrize('cls', MAP_CLASSES)
@pytest.mark.parametrize('kd', ALL_DTYPES)
@pytest.mark.parametrize('vd', ['object', 'float64', 'int64-raise', 'uint64-wrap'])
def test_map_basic_vs_model(cls, kd, vd):
    ks = sample_keys(kd, seed=2)
    vs = sample_keys(vd, len(ks), seed=3)
    m = cls(kd, vd)
    model = {}
    for k, v in zip(ks, vs):
        m[k] = v
        model[k] = v
        assert k in m
        assert m[k] == model[k]
        assert len(m) == len(model)
    assert dict(m.items()) == model
    assert set(m.keys()) == set(model)
    assert sorted(m.values(), key=repr) == sorted(model.values(), key=repr)
    for k in ks[::3]:
        if k in model:
            del m[k]
            del model[k]
    assert dict(m.items()) == model
    while model:
        k, v = m.popitem()
        assert model.pop(k) == v
    with pytest.raises(KeyError):
        m.popitem()


def test_sorted_map_iteration_order():
    ks = sample_keys('int64', seed=4)
    m = fc.Map('int64', 'object', [(k, str(k)) for k in ks])
    assert list(m) == sorted(set(ks))
    assert list(reversed(m)) == sorted(set(ks))[::-1]
    assert list(m.keys()) == sorted(set(ks))


def test_map_methods():
    m = fc.Map('int64', 'int64')
    assert m.get(1) is None
    assert m.get(1, 9) == 9
    assert m.setdefault(1, 5) == 5
    assert m.setdefault(1, 9) == 5
    assert m.pop(1) == 5
    with pytest.raises(KeyError):
        m.pop(1)
    assert m.pop(1, 'd') == 'd'
    m.update({3: 3})
    m.update([(4, 4)])

    class KM:
        def keys(self):
            return [10, 11]

        def __getitem__(self, k):
            return k * 2

    m.update(KM())
    assert sorted(m.items()) == [(3, 3), (4, 4), (10, 20), (11, 22)]
    with pytest.raises(TypeError):
        m.update({}, {})
    mo = fc.UnorderedMap('object', 'int64')
    mo.update({'x': 0}, y=1)
    assert sorted(mo.items()) == [('x', 0), ('y', 1)]
    m.clear()
    assert len(m) == 0 and not m


def test_map_init_forms():
    assert dict(fc.Map('int64', 'int64', {1: 2}).items()) == {1: 2}
    assert dict(fc.Map('int64', 'int64', [(1, 2)]).items()) == {1: 2}
    src = fc.UnorderedMap('int64', 'int64', [(1, 2)])
    assert dict(fc.Map('int64', 'int64', src).items()) == {1: 2}


def test_map_comparisons():
    m = fc.Map('int64', 'object', [(1, 'a')])
    assert m == {1: 'a'}
    assert m == fc.UnorderedMap('int64', 'object', [(1, 'a')])
    assert m == fc.Map('object', 'object', [(1, 'a')])
    assert m != {1: 'b'}
    assert m != {1: 'a', 2: 'b'}
    assert m != {2: 'a'}
    assert (m == [(1, 'a')]) is False
    with pytest.raises(TypeError):
        _ = m < {1: 'a'}


def test_map_views():
    m = fc.UnorderedMap('int64', 'object', [(1, 'a'), (2, 'b')])
    kv, vv, iv = m.keys(), m.values(), m.items()
    assert isinstance(kv, cabc.KeysView)
    assert isinstance(vv, cabc.ValuesView)
    assert isinstance(iv, cabc.ItemsView)
    assert 1 in kv and 'a' in vv and (1, 'a') in iv
    assert sorted(kv & {1, 5}) == [1]
    assert sorted(kv | {5}) == [1, 2, 5]
    assert sorted(iv - {(2, 'b')}) == [(1, 'a')]
    assert len(kv) == len(vv) == len(iv) == 2
    m[3] = 'c'  # views are live
    assert 3 in kv and len(kv) == 3


##
# vectors


@pytest.mark.parametrize('dtype', ALL_DTYPES)
def test_vector_basic_vs_model(dtype):
    xs = sample_keys(dtype, seed=5)
    v = fc.Vector(dtype)
    model = []
    for x in xs:
        v.append(x)
        model.append(x)
    assert list(v) == model
    assert len(v) == len(model)
    for i in (-1, 0, len(model) // 2):
        assert v[i] == model[i]
    v[0] = xs[1]
    model[0] = xs[1]
    v.insert(2, xs[3])
    model.insert(2, xs[3])
    v.insert(-1, xs[4])
    model.insert(-1, xs[4])
    v.insert(10 ** 9, xs[5])
    model.insert(10 ** 9, xs[5])
    assert list(v) == model
    assert v.pop() == model.pop()
    assert v.pop(0) == model.pop(0)
    assert v.pop(-2) == model.pop(-2)
    x = model[3]
    v.remove(x)
    model.remove(x)
    assert list(v) == model
    assert v.count(xs[0]) == model.count(xs[0])
    v.reverse()
    model.reverse()
    assert list(v) == model
    if dtype != 'object':
        v.sort()
        model.sort()
        assert list(v) == model
        v.sort(reverse=True)
        model.sort(reverse=True)
        assert list(v) == model
    assert list(reversed(v)) == model[::-1]
    del v[1]
    del model[1]
    assert list(v) == model


def test_vector_object_sort():
    xs = sample_keys('object', seed=6)
    v = fc.Vector('object', xs)
    v.sort()
    assert list(v) == sorted(xs)
    v.sort(reverse=True)
    assert list(v) == sorted(xs, reverse=True)


def test_vector_object_sort_inconsistent_comparator_is_memory_safe():
    # Regression: a __lt__ that is not a strict weak order fed into std::sort is undefined behavior (observed as a
    # hard segfault via out-of-bounds accesses in libstdc++'s introsort). The sort must stay memory-safe and keep the
    # same elements, however garbage the order.
    class AlwaysLess:
        def __lt__(self, o):
            return True

    class Coin:
        def __lt__(self, o):
            return random.random() < 0.5

    for i in range(50):
        v = fc.Vector('object', [AlwaysLess() for _ in range(100)])
        before = sorted(map(id, v))
        v.sort()
        assert sorted(map(id, v)) == before
        v2 = fc.Vector('object', [Coin() for _ in range(100)])
        v2.sort(reverse=bool(i % 2))
        assert len(v2) == 100


def test_vector_object_sort_raising_comparator_leaves_vector_unchanged():
    class Boom:
        def __init__(self, n):
            self.n = n

        def __lt__(self, o):
            raise ValueError('boom')

    v = fc.Vector('object', [Boom(i) for i in range(10)])
    with pytest.raises(ValueError):  # noqa
        v.sort()
    assert [x.n for x in v] == list(range(10))


def test_vector_object_sort_is_stable_like_list_sort():
    class E:
        def __init__(self, k, seq):
            self.k = k
            self.seq = seq

        def __lt__(self, o):
            return self.k < o.k

    xs = [E(k, i) for i, k in enumerate([3, 1, 2, 1, 3, 1, 2])]
    for reverse in (False, True):
        v = fc.Vector('object', xs)
        v.sort(reverse=reverse)
        model = list(xs)
        model.sort(key=lambda e: e.k, reverse=reverse)
        assert [(e.k, e.seq) for e in v] == [(e.k, e.seq) for e in model]


def test_vector_errors():
    v = fc.Vector('int64', [1, 2, 3])
    with pytest.raises(IndexError):
        v[3]
    with pytest.raises(IndexError):
        v[-4]
    with pytest.raises(IndexError):
        v[3] = 0
    with pytest.raises(IndexError):
        v.pop(9)
    with pytest.raises(IndexError):
        fc.Vector('int64').pop()
    with pytest.raises(ValueError):  # noqa
        v.remove(99)
    with pytest.raises(ValueError):  # noqa
        v.index(1, 1)
    with pytest.raises(TypeError):
        v[0] = 'x'
    with pytest.raises(TypeError):
        hash(v)


def test_vector_index_range_args():
    v = fc.Vector('int64', [0, 1, 2, 1, 0])
    assert v.index(1) == 1
    assert v.index(1, 2) == 3
    assert v.index(0, -2) == 4
    assert v.index(0, 0, -1) == 0
    with pytest.raises(ValueError):  # noqa
        v.index(2, 3)


def test_vector_extend_and_iadd():
    v = fc.Vector('int64', [1])
    orig = v
    v.extend([2, 3])
    v.extend(fc.Vector('int64', [4]))
    v.extend(iter([5]))
    v += [6]
    v += fc.Vector('object', [7])
    assert v is orig
    assert list(v) == [1, 2, 3, 4, 5, 6, 7]
    v += v
    assert list(v) == [1, 2, 3, 4, 5, 6, 7] * 2


def test_vector_comparisons():
    assert fc.Vector('int64', [1, 2]) == [1, 2]
    assert fc.Vector('int64', [1, 2]) == fc.Vector('float64', [1.0, 2.0])
    assert fc.Vector('int64', [1, 2]) != [1, 3]
    assert fc.Vector('int64', [1, 2]) < [1, 3]
    assert fc.Vector('int64', [1, 2]) <= [1, 2]
    assert fc.Vector('int64', [2]) > [1, 9]
    assert fc.Vector('int64', [1]) >= [1]
    assert (fc.Vector('int64', [1]) == (1,)) is False
    with pytest.raises(TypeError):
        _ = fc.Vector('int64', [1]) < (1,)


def test_vector_slice_fuzz_vs_list():
    rnd = random.Random(7)
    v = fc.Vector('int64', range(20))
    model = list(range(20))
    for _ in range(300):
        start = rnd.choice([None, *range(-25, 25)])
        stop = rnd.choice([None, *range(-25, 25)])
        step = rnd.choice([None, *[i for i in range(-5, 6) if i]])
        sl = slice(start, stop, step)
        assert list(v[sl]) == model[sl], sl
        op = rnd.randrange(3)
        if op == 0:
            del v[sl]
            del model[sl]
        elif op == 1:
            tgt = model[sl]
            if step in (None, 1):
                repl = [rnd.randrange(100) for _ in range(rnd.randrange(0, 6))]
            else:
                repl = [rnd.randrange(100) for _ in range(len(tgt))]
            v[sl] = repl
            model[sl] = repl
        assert list(v) == model, sl
        if len(model) < 5:
            ext = [rnd.randrange(100) for _ in range(20)]
            v.extend(ext)
            model.extend(ext)
    assert type(v[::2]) is fc.Vector
    assert v[::2].dtype == v.dtype


##
# object semantics


def test_sorted_object_uses_richcompare():
    calls = []

    class K:
        def __init__(self, n):
            self.n = n

        def __lt__(self, o):
            calls.append('lt')
            return self.n < o.n

        def __gt__(self, o):
            return self.n > o.n

        def __hash__(self):
            raise AssertionError('hash must not be used')

    s = fc.Set('object', [K(3), K(1), K(2)])
    assert [k.n for k in s] == [1, 2, 3]
    assert calls
    assert K(2) in s
    assert K(9) not in s


def test_unordered_object_uses_hash_eq():
    class K:
        def __init__(self, n):
            self.n = n

        def __hash__(self):
            return hash(self.n)

        def __eq__(self, o):
            return isinstance(o, K) and self.n == o.n

        def __lt__(self, o):
            raise AssertionError('lt must not be used')

    s = fc.UnorderedSet('object', [K(1), K(2), K(1)])
    assert len(s) == 2
    assert K(2) in s
    m = fc.UnorderedMap('object', 'int64')
    m[K(5)] = 50
    assert m[K(5)] == 50


def test_unhashable_objects():
    class U:
        __hash__ = None  # type: ignore

        def __lt__(self, o):
            return id(self) < id(o)

        def __gt__(self, o):
            return id(self) > id(o)

    fc.Set('object', [U(), U()])  # ok: sorted never hashes
    with pytest.raises(TypeError):
        fc.UnorderedSet('object', [U()])
    with pytest.raises(TypeError):
        fc.UnorderedMap('object', 'object')[U()] = 1


def test_comparator_exception_leaves_container_consistent():
    class Boom:
        def __lt__(self, o):
            raise ValueError('boom')

        def __gt__(self, o):
            raise ValueError('boom')

    s = fc.Set('object', [1, 2, 3])
    with pytest.raises(ValueError):  # noqa
        s.add(Boom())
    assert list(s) == [1, 2, 3]
    with pytest.raises(ValueError):  # noqa
        _ = Boom() in s
    assert list(s) == [1, 2, 3]
    s.add(4)
    assert list(s) == [1, 2, 3, 4]

    class BadEq:
        def __hash__(self):
            return 1

        def __eq__(self, o):
            raise ValueError('boom')

    u = fc.UnorderedSet('object')
    u.add(BadEq())
    with pytest.raises(ValueError):  # noqa
        u.add(BadEq())  # same hash bucket -> __eq__ raises
    assert len(u) == 1


def test_setdefault_inconsistent_comparator_does_not_leak():
    # Regression: an inconsistent __lt__ can make setdefault's find() miss while its try_emplace still lands on the
    # existing node; the existing entry must not be re-retained (a refcount leak). The script below reproduces that
    # split under libstdc++'s walk order (find: k1<k2, k2<k1; emplace: k2<k1, k1<k2); on other STLs the path may not
    # trigger, in which case the assertions hold trivially.
    script: list = []

    class SK:
        def __lt__(self, o):
            if script:
                return script.pop(0)
            return False

        def __gt__(self, o):
            return False

    k1 = SK()
    k2 = SK()
    val = ['v']
    m = fc.Map('object', 'object')
    m[k1] = val
    base = sys.getrefcount(val)
    script[:] = [False, True, False, False]
    ret = m.setdefault(k2, None)
    assert ret is val or ret is None
    del ret
    assert len(m) <= 2
    assert sys.getrefcount(val) == base
    s = fc.Set('object')

    class Evil:
        def __lt__(self, o):
            s.add(123)
            return True

        def __gt__(self, o):
            return False

    s.add(1)
    with pytest.raises(RuntimeError, match='reentrant'):
        s.add(Evil())

    m = fc.Map('object', 'object')

    class EvilK:
        def __lt__(self, o):
            m.clear()
            return True

        def __gt__(self, o):
            return False

    m[1] = 'a'
    with pytest.raises(RuntimeError, match='reentrant'):
        m[EvilK()] = 'b'


##
# lifecycle


def test_uninitialized_and_reinit():
    s = fc.Set.__new__(fc.Set)
    with pytest.raises(RuntimeError, match='not initialized'):
        s.add(1)
    with pytest.raises(RuntimeError, match='not initialized'):
        len(s)
    s2 = fc.Set('int64')
    with pytest.raises(TypeError, match='already initialized'):
        s2.__init__('int64')


def test_gc_cycles_collected():
    class P:
        pass

    refs = []
    for make in (
            lambda: fc.Map('object', 'object'),
            lambda: fc.UnorderedMap('object', 'object'),
    ):
        m = make()
        p = P()
        refs.append(weakref.ref(p))
        m['self'] = m
        m['p'] = p
        del m, p
    v = fc.Vector('object')
    p = P()
    refs.append(weakref.ref(p))
    v.append(v)
    v.append(p)
    del v, p
    s = fc.Set('object')
    p = P()
    refs.append(weakref.ref(p))
    ref_holder = fc.Vector('object', [s, p])
    s.add(ref_holder)  # sorted-object cycle: s -> ref_holder -> s, no hashing involved
    del s, p, ref_holder
    gc.collect()
    assert all(r() is None for r in refs)


def test_copy_independence():
    for c in (
            fc.Set('int64', [1, 2]),
            fc.UnorderedSet('object', ['a']),
            fc.Map('int64', 'object', [(1, 'a')]),
            fc.UnorderedMap('float64', 'float64', [(1.0, 2.0)]),
            fc.Vector('int64', [1, 2]),
    ):
        d = c.copy()
        assert type(d) is type(c)
        assert d == c
        assert d is not c
        c.clear()
        assert len(c) == 0
        assert len(d) > 0


def test_same_spec_fast_paths():
    a = fc.UnorderedMap('int64', 'int64', [(i, i) for i in range(100)])
    b = fc.UnorderedMap('int64', 'int64')
    b.update(a)
    assert a == b
    b[0] = 99
    assert a != b
    s = fc.Set('float64', [1.0, 2.0])
    t = fc.Set('float64')
    t.update(s)
    assert s == t
    v = fc.Vector('uint64-wrap', [1, 2])
    w = v.copy()
    w.extend(v)
    assert list(w) == [1, 2, 1, 2]


##
# abcs


def test_abc_registration():
    assert isinstance(fc.Set('int64'), cabc.MutableSet)
    assert isinstance(fc.UnorderedSet('int64'), cabc.MutableSet)
    assert isinstance(fc.Map('int64', 'int64'), cabc.MutableMapping)
    assert isinstance(fc.UnorderedMap('int64', 'int64'), cabc.MutableMapping)
    assert isinstance(fc.Vector('int64'), cabc.MutableSequence)
    assert isinstance(iter(fc.Vector('int64')), cabc.Iterator)


##
# iteration & mutation


@pytest.mark.parametrize('make', [
    lambda: fc.Set('int64', [1, 2, 3]),
    lambda: fc.UnorderedSet('int64', [1, 2, 3]),
    lambda: fc.Map('int64', 'int64', [(i, i) for i in (1, 2, 3)]),
    lambda: fc.UnorderedMap('int64', 'int64', [(i, i) for i in (1, 2, 3)]),
])
def test_iteration_mutation_raises(make):
    c = make()
    it = iter(c)
    next(it)
    (c.add if hasattr(c, 'add') else lambda k: c.__setitem__(k, k))(99)
    with pytest.raises(RuntimeError, match='mutated during iteration'):
        next(it)
    # value overwrite is not a structural mutation for maps
    if hasattr(c, 'keys'):
        it = iter(c)
        next(it)
        c[2] = -2
        next(it)


def test_vector_iteration_tolerates_mutation():
    v = fc.Vector('int64', [1, 2, 3])
    it = iter(v)
    assert next(it) == 1
    v.append(4)
    assert [next(it), next(it), next(it)] == [2, 3, 4]
    v2 = fc.Vector('int64', [1, 2, 3])
    it = iter(v2)
    next(it)
    v2.clear()
    with pytest.raises(StopIteration):
        next(it)
    v2.append(9)  # exhausted stays exhausted
    with pytest.raises(StopIteration):
        next(it)


def test_iterator_type_sealed():
    it = iter(fc.Set('int64', [1]))
    with pytest.raises(TypeError):
        type(it)()


##
# repr


def test_repr_round_trip():
    env = {c.__name__: c for c in (*SET_CLASSES, *MAP_CLASSES, fc.Vector)}
    for c in (
            fc.Set('int64', [2, 1]),
            fc.UnorderedSet('object', ['a']),
            fc.Map('int64', 'float64', [(1, 2.5)]),
            fc.UnorderedMap('object', 'object', [('k', 'v')]),
            fc.Vector('uint64-clamp', [1, 2]),
            fc.Vector('object', []),
    ):
        r = repr(c)
        assert type(c).__name__ in r
        assert eval(r, env) == c  # noqa


def test_repr_cycle():
    v = fc.Vector('object')
    v.append(v)
    assert '...' in repr(v)
    m = fc.Map('object', 'object')
    m['m'] = m
    assert '...' in repr(m)


##
# threading


def _run_threads(n, fn):
    barrier = threading.Barrier(n)
    errs = []

    def wrap(i):
        try:
            barrier.wait()
            fn(i)
        except BaseException as e:  # noqa
            errs.append(e)

    ts = [threading.Thread(target=wrap, args=(i,)) for i in range(n)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    if errs:
        raise errs[0]


@pytest.mark.parametrize(('cls', 'init_args'), [
    (fc.Set, lambda i: ('int64', [i])),
    (fc.UnorderedSet, lambda i: ('int64', [i])),
    (fc.Map, lambda i: ('int64', 'int64', [(i, i)])),
    (fc.Vector, lambda i: ('int64', [i])),
])
def test_threaded_first_init_race_single_winner(cls, init_args):
    # Racing the first __init__ of a shared uninitialized object must let exactly one thread publish an impl (the
    # losers raise the re-init TypeError) rather than leaking the losers' impls.
    for _ in range(20):
        o = cls.__new__(cls)
        wins, errs = [], []
        barrier = threading.Barrier(4)

        def work(i):
            barrier.wait()
            try:
                o.__init__(*init_args(i))
            except TypeError:
                errs.append(i)
            else:
                wins.append(i)

        ts = [threading.Thread(target=work, args=(i,)) for i in range(4)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        assert len(wins) == 1
        assert len(errs) == 3
        assert len(o) == 1


def test_threaded_int_map_stress():
    m = fc.UnorderedMap('int64', 'int64')

    def work(i):
        rnd = random.Random(i)
        for _ in range(4000):
            k = rnd.randrange(200)
            op = rnd.randrange(6)
            if op == 0:
                m[k] = k * 10
            elif op == 1:
                m.pop(k, None)
            elif op == 2:
                m.get(k)
            elif op == 3:
                _ = k in m
            elif op == 4:
                m.setdefault(k, k)
            else:
                len(m)

    _run_threads(8, work)
    for k, v in m.items():
        assert v in (k, k * 10)


def test_threaded_object_map_with_gc():
    m = fc.Map('object', 'object')
    stop = threading.Event()

    def gc_work():
        while not stop.is_set():
            gc.collect()

    gt = threading.Thread(target=gc_work)
    gt.start()
    try:
        def work(i):
            rnd = random.Random(i)
            other = fc.Map('object', 'object', [(str(j), j) for j in range(20)])
            for _ in range(600):
                k = str(rnd.randrange(50))
                op = rnd.randrange(5)
                if op == 0:
                    m[k] = [k]
                elif op == 1:
                    m.pop(k, None)
                elif op == 2:
                    _ = m == other
                elif op == 3:
                    m.copy()
                elif rnd.random() < 0.2:
                    # Iteration racing structural mutation legitimately raises, dict-style; on free-threaded builds
                    # it does so routinely. RuntimeError comes from the key iterator's version check; KeyError comes
                    # from the abc ItemsView looking a yielded key back up after a concurrent pop.
                    try:
                        dict(m.items())
                    except RuntimeError as e:
                        assert 'mutated during iteration' in str(e)  # noqa
                    except KeyError:
                        pass
                else:
                    _ = k in m

        _run_threads(6, work)
    finally:
        stop.set()
        gt.join()
    for k, v in m.items():
        assert v == [k]


def test_threaded_vector_counted_invariants():
    v = fc.Vector('int64')
    n_threads, n_ops = 8, 2000
    pops = [0] * n_threads

    def work(i):
        for j in range(n_ops):
            v.append(i * n_ops + j)
            if j % 3 == 0:
                try:
                    v.pop()
                except IndexError:
                    pass
                else:
                    pops[i] += 1

    _run_threads(n_threads, work)
    assert len(v) == n_threads * n_ops - sum(pops)
    assert len(set(v)) == len(v)


def test_threaded_iterators_race_mutators():
    s = fc.Set('int64', range(100))

    def work(i):
        rnd = random.Random(i)
        if i % 2 == 0:
            for _ in range(300):
                try:
                    for _x in s:
                        pass
                except RuntimeError:
                    pass
                list(iter(s)) if rnd.random() < 0.1 else None
        else:
            for _ in range(300):
                k = rnd.randrange(150)
                s.add(k) if rnd.random() < 0.5 else s.discard(k)

    try:
        _run_threads(6, work)
    except RuntimeError as e:
        assert 'mutated during iteration' in str(e)  # noqa
    assert sorted(s) == list(s)
