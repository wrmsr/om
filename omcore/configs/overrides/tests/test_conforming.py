import collections.abc
import typing as ta

import pytest

from ..conforming import conform_value
from ..errors import OverrideValueError
from ..shapes import AnyShape
from ..shapes import ChoiceShape
from ..shapes import LazyShape
from ..shapes import ListShape
from ..shapes import MapShape
from ..shapes import ObjectShape
from ..shapes import OptionalShape
from ..shapes import ScalarShape
from ..shapes import TaggedShape
from ..shapes import TupleShape
from ..shapes import UnionShape
from ..shapes import UnknownShape


STR = ScalarShape(str)
INT = ScalarShape(int)
FLOAT = ScalarShape(float)
BOOL = ScalarShape(bool)


def check(value, shape, expected):
    v = conform_value(value, shape)
    assert v == expected
    assert type(v) is type(expected)


def check_bad(value, shape, match=None):
    with pytest.raises(OverrideValueError, match=match):
        conform_value(value, shape)


def test_scalars():
    check('x', STR, 'x')
    check(True, BOOL, True)
    check(5, INT, 5)
    check(5.5, FLOAT, 5.5)

    # Ints and floats of the same value are the only things taken for one another.
    check(5, FLOAT, 5.)
    check(5., INT, 5)

    bad: list[tuple[ScalarShape, list[ta.Any]]] = [
        (STR, [5, 1.1, True, None, [], {}]),
        (INT, ['5', 5.5, True, None, float('inf'), float('nan')]),
        (FLOAT, ['5', True, None]),
        (BOOL, ['true', 1, 0, None]),
    ]
    for shape, vs in bad:
        for v in vs:
            check_bad(v, shape)

    check_bad(1.1, STR, r'Expected str at the root, got number 1\.1')
    check_bad('false', BOOL, "Expected bool at the root, got string 'false'")


def test_choices():
    c = ChoiceShape(['a', 5, True, None])
    check('a', c, 'a')
    check(5, c, 5)
    check(5., c, 5)
    check(True, c, True)
    check(None, c, None)

    for v in ['b', 6, False, '5', 1, 'True']:
        check_bad(v, c)
    check_bad(1, ChoiceShape([True]))
    check_bad(True, ChoiceShape([1]))


def test_optionals_and_unions():
    check(None, OptionalShape(STR), None)
    check('x', OptionalShape(STR), 'x')
    check_bad(5, OptionalShape(STR))
    check_bad(None, STR)

    u = UnionShape([BOOL, INT, STR])
    check(True, u, True)
    check(5, u, 5)
    check('5', u, '5')
    check_bad(5.5, u)
    check_bad([], u)

    check(5, UnionShape([FLOAT, STR]), 5.)
    check({'x': 5.}, UnionShape([INT, ObjectShape({'x': INT})]), {'x': 5})


def test_containers():
    check([1, 2.], ListShape(INT), [1, 2])
    check((1, 2), ListShape(FLOAT), [1., 2.])
    check([1, 'x'], TupleShape([FLOAT, STR]), [1., 'x'])
    check({'a': 1}, MapShape(FLOAT), {'a': 1.})

    check_bad('ab', ListShape(STR))
    check_bad({'a': 1}, ListShape(INT))
    check_bad([1], MapShape(INT))
    check_bad(5, MapShape(INT))
    check_bad([1], TupleShape([INT, INT]), 'exactly 2 elements')
    check_bad({1: 1}, MapShape(INT), 'string keys')
    check_bad([1, 'x'], ListShape(INT), r"Expected int at '\[1\]', got string 'x'")
    check_bad({'a': [{'b': 1}, {'b': None}]}, MapShape(ListShape(MapShape(INT))), r"at 'a\.1\.b', got null")


def test_objects():
    o = ObjectShape({
        'name': STR,
        'dim': INT,
        'sub': OptionalShape(LazyShape(lambda: o)),
    })

    check({'name': 'x', 'sub': {'dim': 2., 'sub': None}}, o, {'name': 'x', 'sub': {'dim': 2, 'sub': None}})
    check({}, o, {})

    check_bad({'nmae': 'x'}, o, "Unknown key 'nmae' at the root - did you mean 'name'")
    check_bad({'sub': {'dmi': 1}}, o, "Unknown key 'dmi' at 'sub'")
    check_bad({'name': 5}, o, "Expected str at 'name', got number 5")
    check_bad([], o, 'Expected map at the root, got a list')

    oo = ObjectShape({'name': STR}, open=True)
    check({'name': 'x', 'other': [1, {'a': None}]}, oo, {'name': 'x', 'other': [1, {'a': None}]})
    check_bad({'name': 5, 'other': 1}, oo)


def test_tagged():
    alts = {
        'adam': ObjectShape({'lr': FLOAT}),
        'sgd': ObjectShape({'lr': FLOAT, 'momentum': FLOAT}),
    }

    w = TaggedShape(alts)
    check({'sgd': {'lr': 1}}, w, {'sgd': {'lr': 1.}})
    check_bad({}, w, 'exactly one tag')
    check_bad({'adam': {}, 'sgd': {}}, w, r"exactly one tag at the root, got \['adam', 'sgd'\]")
    check_bad({'sdg': {}}, w, "Unknown tag 'sdg' at the root - did you mean 'sgd'")
    check_bad({'adam': {'momentum': 1}}, w, "Unknown key 'momentum' at 'adam'")
    check_bad('adam', w)

    f = TaggedShape(alts, tag_field='type')
    check({'type': 'sgd', 'momentum': 1}, f, {'type': 'sgd', 'momentum': 1.})
    check({'lr': 1, 'type': 'adam'}, f, {'type': 'adam', 'lr': 1.})
    check_bad({'lr': 1}, f, "Missing 'type' tag")
    check_bad({'type': 'sdg'}, f, "Unknown tag 'sdg'")
    check_bad({'type': 'adam', 'momentum': 1}, f, "Unknown key 'momentum'")
    check_bad({'type': ['adam']}, f, 'Unknown tag')


def test_nothing_to_conform_to():
    class Odd:
        pass

    odd = Odd()
    for shape in [AnyShape(), UnknownShape('whatever')]:
        check(5, shape, 5)
        check('5', shape, '5')
        assert conform_value(odd, shape) is odd
        assert conform_value({'a': (1, odd)}, shape) == {'a': [1, odd]}

    o = ObjectShape({'a': INT, 'u': UnknownShape(), 'x': AnyShape()})
    check({'a': 1., 'u': {'k': 1.}, 'x': [1.]}, o, {'a': 1, 'u': {'k': 1.}, 'x': [1.]})


def test_results_are_plain_and_unaliased():
    class M(collections.abc.Mapping):
        def __init__(self, d):
            self.d = d

        def __getitem__(self, k):
            return self.d[k]

        def __iter__(self):
            return iter(self.d)

        def __len__(self):
            return len(self.d)

    inner = [1, 2]
    src = M({'xs': inner, 'any': M({'k': inner}), 'm': M({'k': 1})})
    out = conform_value(src, ObjectShape({'xs': ListShape(INT), 'any': AnyShape(), 'm': MapShape(INT)}))

    assert out == {'xs': [1, 2], 'any': {'k': [1, 2]}, 'm': {'k': 1}}
    assert type(out) is dict
    assert type(out['any']) is dict
    assert type(out['m']) is dict
    assert out['xs'] is not inner
    assert out['any']['k'] is not inner
