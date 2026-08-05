import random
import typing as ta

import pytest

from ..persistent import DictPersistentMapping
from ..persistent import PersistentMapping
from ..persistent import PersistentSequence
from ..persistent import TuplePersistentSequence


##


def _check_seq(s, expected):
    assert len(s) == len(expected)
    assert list(s) == list(expected)
    assert tuple(s) == tuple(expected)
    assert list(reversed(s)) == list(reversed(expected))
    assert s.debug == tuple(expected)

    for i, v in enumerate(expected):
        assert s[i] == v
        assert s[i - len(expected)] == v

    with pytest.raises(IndexError):
        s[len(expected)]

    with pytest.raises(IndexError):
        s[-len(expected) - 1]


class TestTuplePersistentSequence:
    def test_interface(self):
        s = TuplePersistentSequence([1, 2, 3])

        assert isinstance(s, PersistentSequence)
        assert isinstance(s, ta.Sequence)

    def test_empty(self):
        s: TuplePersistentSequence[int] = TuplePersistentSequence()

        assert len(s) == 0
        assert list(s) == []
        assert s.debug == ()
        assert 0 not in s

        with pytest.raises(IndexError):
            s[0]

        assert list(s[:]) == []
        assert list(s.iter_from(0)) == []

    def test_construct(self):
        _check_seq(TuplePersistentSequence(range(10)), list(range(10)))
        _check_seq(TuplePersistentSequence(x for x in 'abc'), ['a', 'b', 'c'])
        _check_seq(TuplePersistentSequence(()), [])

    def test_getitem_int(self):
        s = TuplePersistentSequence(range(10))

        assert s[0] == 0
        assert s[9] == 9
        assert s[-1] == 9
        assert s[-10] == 0

        with pytest.raises(IndexError):
            s[10]

        with pytest.raises(IndexError):
            s[-11]

    def test_getitem_slice(self):
        s = TuplePersistentSequence(range(20))

        assert isinstance(s[3:8], TuplePersistentSequence)
        assert list(s[3:8]) == list(range(3, 8))
        assert list(s[:5]) == list(range(5))
        assert list(s[15:]) == list(range(15, 20))
        assert list(s[-8:-2]) == list(range(12, 18))
        assert list(s[8:3]) == []
        assert list(s[100:200]) == []

        assert s[:] is s
        assert s[0:len(s)] is s
        assert s[-100:100] is s

        with pytest.raises(ValueError):  # noqa
            s[::2]

        with pytest.raises(ValueError):  # noqa
            s[::-1]

    def test_contains(self):
        s = TuplePersistentSequence(range(5))

        assert 3 in s
        assert 5 not in s

    def test_iter(self):
        s = TuplePersistentSequence(range(5))

        assert list(iter(s)) == list(range(5))

    def test_reversed(self):
        s = TuplePersistentSequence(range(5))

        assert list(reversed(s)) == [4, 3, 2, 1, 0]

    def test_iter_from(self):
        s = TuplePersistentSequence(range(10))

        assert list(s.iter_from(0)) == list(range(10))
        assert list(s.iter_from(5)) == list(range(5, 10))
        assert list(s.iter_from(10)) == []
        assert list(s.iter_from(100)) == []
        assert list(s.iter_from(-3)) == [7, 8, 9]
        assert list(s.iter_from(-100)) == list(range(10))

    def test_index(self):
        s = TuplePersistentSequence([10, 20, 30, 20])

        assert s.index(20) == 1
        assert s.index(20, 2) == 3
        assert s.index(20, 2, 4) == 3

        with pytest.raises(ValueError):  # noqa
            s.index(99)

        with pytest.raises(ValueError):  # noqa
            s.index(10, 1)

    def test_count(self):
        s = TuplePersistentSequence([1, 2, 2, 3, 2])

        assert s.count(2) == 3
        assert s.count(1) == 1
        assert s.count(99) == 0

    def test_splice_insert(self):
        s = TuplePersistentSequence(range(10))
        s2 = s.splice(5, 5, [100, 101, 102])

        _check_seq(s, list(range(10)))
        _check_seq(s2, [0, 1, 2, 3, 4, 100, 101, 102, 5, 6, 7, 8, 9])

    def test_splice_delete(self):
        s = TuplePersistentSequence(range(20))
        s2 = s.splice(7, 13, ())

        _check_seq(s, list(range(20)))
        _check_seq(s2, list(range(7)) + list(range(13, 20)))

    def test_splice_replace(self):
        s = TuplePersistentSequence(range(10))
        s2 = s.splice(4, 6, [100, 101, 102])

        _check_seq(s2, [0, 1, 2, 3, 100, 101, 102, 6, 7, 8, 9])

    def test_splice_bounds(self):
        s = TuplePersistentSequence(range(10))

        _check_seq(s.splice(None, None, [100]), [100])
        _check_seq(s.splice(None, 2, ()), list(range(2, 10)))
        _check_seq(s.splice(8, None, ()), list(range(8)))
        _check_seq(s.splice(-2, None, [100]), [*range(8), 100])
        _check_seq(s.splice(8, 3, [100]), [*range(8), 100, *range(8, 10)])
        _check_seq(s.splice(100, 200, [100]), [*range(10), 100])

    def test_splice_noop_returns_self(self):
        s = TuplePersistentSequence(range(10))

        assert s.splice(5, 5, ()) is s
        assert s.splice(5, 5, iter(())) is s

    def test_splice_empty(self):
        s: TuplePersistentSequence[int] = TuplePersistentSequence()
        s2 = s.splice(0, 0, [1, 2, 3])

        _check_seq(s, [])
        _check_seq(s2, [1, 2, 3])

    def test_with(self):
        s = TuplePersistentSequence(range(10))
        s2 = s.with_(5, 100)
        s3 = s.with_(-1, 200)

        _check_seq(s, list(range(10)))
        _check_seq(s2, [0, 1, 2, 3, 4, 100, 6, 7, 8, 9])
        _check_seq(s3, [*range(9), 200])

        with pytest.raises(IndexError):
            s.with_(10, 100)

        with pytest.raises(IndexError):
            s.with_(-11, 100)

    def test_with_identical_returns_self(self):
        v = ['boxed']
        s = TuplePersistentSequence([0, v, 2])

        assert s.with_(1, v) is s
        assert s.with_(1, ['boxed']) is not s

    def test_without_index(self):
        s = TuplePersistentSequence(range(10))

        _check_seq(s.without(5), [0, 1, 2, 3, 4, 6, 7, 8, 9])
        _check_seq(s.without(0), list(range(1, 10)))
        _check_seq(s.without(9), list(range(9)))
        _check_seq(s.without(-1), list(range(9)))
        _check_seq(s, list(range(10)))

        with pytest.raises(IndexError):
            s.without(10)

        with pytest.raises(IndexError):
            s.without(-11)

    def test_without_slice(self):
        s = TuplePersistentSequence(range(20))

        _check_seq(s.without(slice(4, 16)), list(range(4)) + list(range(16, 20)))
        _check_seq(s.without(slice(None, None)), [])
        _check_seq(s.without(slice(-5, None)), list(range(15)))

        assert s.without(slice(5, 5)) is s
        assert s.without(slice(8, 3)) is s

        with pytest.raises(ValueError):  # noqa
            s.without(slice(None, None, 2))

    def test_append(self):
        s: TuplePersistentSequence[int] = TuplePersistentSequence()

        for i in range(20):
            s = s.append(i)

        _check_seq(s, list(range(20)))

    def test_extend(self):
        s = TuplePersistentSequence(range(5))
        s2 = s.extend(range(5, 10))
        s3 = s2.extend(x for x in [10, 11])

        _check_seq(s, list(range(5)))
        _check_seq(s2, list(range(10)))
        _check_seq(s3, list(range(12)))

        assert s.extend(()) is s
        assert s.extend(iter(())) is s

    def test_persistence(self):
        versions = []
        s: TuplePersistentSequence[int] = TuplePersistentSequence()

        for i in range(50):
            versions.append(s)
            s = s.append(i)

        for i, old in enumerate(versions):
            _check_seq(old, list(range(i)))

    def test_random_against_list(self):
        rng = random.Random(0)

        s: TuplePersistentSequence[int] = TuplePersistentSequence()
        lst: list[int] = []

        for step in range(1000):
            op = rng.randrange(6)

            if op == 0:
                v = rng.randrange(100000)
                idx = rng.randrange(len(lst) + 1)
                s = s.splice(idx, idx, [v])
                lst[idx:idx] = [v]

            elif op == 1 and lst:
                start = rng.randrange(len(lst))
                stop = rng.randrange(start, len(lst) + 1)
                vals = [rng.randrange(100000) for _ in range(rng.randrange(8))]
                s = s.splice(start, stop, vals)
                lst[start:stop] = vals

            elif op == 2:
                vals = [rng.randrange(100000) for _ in range(rng.randrange(16))]
                s = s.extend(vals)
                lst.extend(vals)

            elif op == 3 and lst:
                idx = rng.randrange(len(lst))
                s = s.without(idx)
                del lst[idx]

            elif op == 4 and lst:
                idx = rng.randrange(len(lst))
                v = rng.randrange(100000)
                s = s.with_(idx, v)
                lst[idx] = v

            elif lst:
                start = rng.randrange(len(lst))
                stop = rng.randrange(start, len(lst) + 1)
                s = s[start:stop]
                lst = lst[start:stop]

            if not step % 25:
                _check_seq(s, lst)

        _check_seq(s, lst)


##


def _check_map(m, expected):
    assert len(m) == len(expected)
    assert set(m) == set(expected)
    assert dict(m.iteritems()) == expected
    assert dict(m.items()) == expected
    assert sorted(m.itervalues()) == sorted(expected.values())
    assert sorted(m.values()) == sorted(expected.values())
    assert set(m.keys()) == set(expected)
    assert m.debug == expected
    assert m == expected

    for k, v in expected.items():
        assert k in m
        assert m[k] == v
        assert m.get(k) == v


class TestDictPersistentMapping:
    def test_interface(self):
        m = DictPersistentMapping([(1, 'a')])

        assert isinstance(m, PersistentMapping)
        assert isinstance(m, ta.Mapping)

    def test_empty(self):
        m: DictPersistentMapping[int, str] = DictPersistentMapping()

        assert len(m) == 0
        assert list(m) == []
        assert list(m.iteritems()) == []
        assert 1 not in m
        assert m.get(1) is None
        assert m.get(1, 'x') == 'x'

        with pytest.raises(KeyError):
            m[1]

        _check_map(m, {})

    def test_construct(self):
        _check_map(DictPersistentMapping([(1, 'a'), (2, 'b')]), {1: 'a', 2: 'b'})
        _check_map(DictPersistentMapping((k, k * 2) for k in range(3)), {0: 0, 1: 2, 2: 4})
        _check_map(DictPersistentMapping({1: 'a'}.items()), {1: 'a'})

        with pytest.raises(TypeError):
            DictPersistentMapping([(1, 'a')], _d={2: 'b'})

    def test_getitem_contains_len(self):
        m = DictPersistentMapping([(1, 'a'), (2, 'b')])

        assert len(m) == 2
        assert 1 in m
        assert 2 in m
        assert 3 not in m
        assert m[1] == 'a'
        assert m[2] == 'b'

        with pytest.raises(KeyError):
            m[3]

    def test_iter(self):
        m = DictPersistentMapping([(1, 'a'), (2, 'b'), (3, 'c')])

        assert set(iter(m)) == {1, 2, 3}
        assert set(m.iteritems()) == {(1, 'a'), (2, 'b'), (3, 'c')}
        assert set(m.itervalues()) == {'a', 'b', 'c'}
        assert set(m.items()) == {(1, 'a'), (2, 'b'), (3, 'c')}
        assert set(m.values()) == {'a', 'b', 'c'}
        assert set(m.keys()) == {1, 2, 3}

    def test_with(self):
        m0: DictPersistentMapping[int, str] = DictPersistentMapping()
        m1 = m0.with_(1, 'a')
        m2 = m1.with_(2, 'b')
        m3 = m2.with_(1, 'updated')

        _check_map(m0, {})
        _check_map(m1, {1: 'a'})
        _check_map(m2, {1: 'a', 2: 'b'})
        _check_map(m3, {1: 'updated', 2: 'b'})

    def test_without(self):
        m = DictPersistentMapping([(1, 'a'), (2, 'b'), (3, 'c')])
        m2 = m.without(2)

        _check_map(m, {1: 'a', 2: 'b', 3: 'c'})
        _check_map(m2, {1: 'a', 3: 'c'})

        with pytest.raises(KeyError):
            m2[2]

    def test_without_missing_returns_self(self):
        m = DictPersistentMapping([(1, 'a')])

        assert m.without(999) is m

    def test_default(self):
        m0: DictPersistentMapping[int, str] = DictPersistentMapping()
        m1 = m0.default(1, 'a')
        m2 = m1.default(1, 'ignored')

        _check_map(m0, {})
        _check_map(m1, {1: 'a'})
        _check_map(m2, {1: 'a'})
        assert m2 is m1

    def test_none_values(self):
        m0: DictPersistentMapping[int, None] = DictPersistentMapping()
        m = m0.with_(1, None)

        assert 1 in m
        assert m[1] is None
        assert m.get(1, 'x') is None
        _check_map(m, {1: None})

    def test_eq(self):
        m = DictPersistentMapping([(1, 'a')])

        assert m == {1: 'a'}
        assert m == DictPersistentMapping([(1, 'a')])
        assert m != {1: 'b'}
        assert m != {}

    def test_persistence(self):
        versions: list[DictPersistentMapping[int, str]] = [DictPersistentMapping()]

        m: DictPersistentMapping[int, str] = DictPersistentMapping()
        for i in range(20):
            m = m.with_(i, f'v{i}')
            versions.append(m)

        for i in range(20):
            m = m.without(i)
            versions.append(m)

        for i, ver in enumerate(versions[:21]):
            _check_map(ver, {k: f'v{k}' for k in range(i)})

        for i, ver in enumerate(versions[21:]):
            _check_map(ver, {k: f'v{k}' for k in range(i + 1, 20)})

    def test_random_against_dict(self):
        rng = random.Random(0)

        m: DictPersistentMapping[int, int] = DictPersistentMapping()
        d: dict[int, int] = {}

        for step in range(1000):
            k = rng.randrange(50)
            op = rng.randrange(4)

            if op in (0, 1):
                v = rng.randrange(100000)
                m = m.with_(k, v)
                d[k] = v

            elif op == 2:
                m = m.without(k)
                d.pop(k, None)

            elif k in d:
                assert m[k] == d[k]

            else:
                assert k not in m
                with pytest.raises(KeyError):
                    m[k]

            if not step % 25:
                _check_map(m, d)

        _check_map(m, d)
