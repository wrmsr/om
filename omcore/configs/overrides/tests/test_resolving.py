import pytest

from ..errors import OverrideValueError
from ..errors import UnhandledOverrideShapeError
from ..literals import parse_raw_value
from ..parsing import parse_path
from ..resolving import ValueResolver
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


def resolve(s, shape, **kwargs):
    return ValueResolver(**kwargs).resolve(parse_raw_value(s), shape)


def check(s, shape, expected, **kwargs):
    v = resolve(s, shape, **kwargs)
    assert v == expected
    assert type(v) is type(expected)


def test_str():
    check('foo', STR, 'foo')
    check('1.10', STR, '1.10')
    check('123', STR, '123')
    check('null', STR, 'null')
    check('true', STR, 'true')
    check('', STR, '')
    check('"quoted"', STR, 'quoted')
    check('"a" "b"', STR, '"a" "b"')
    check('hello world, yes', STR, 'hello world, yes')

    # Verbatim when it is the entire value, whatever it looks like.
    check('[a-z]', STR, '[a-z]')
    check('[a-z]+', STR, '[a-z]+')
    check('{x: 1}', STR, '{x: 1}')
    check('{name}-{id}.txt', STR, '{name}-{id}.txt')

    # But not when nested.
    with pytest.raises(OverrideValueError):
        resolve('[[a]]', ListShape(STR))


def test_numbers():
    check('5', INT, 5)
    check('-5', INT, -5)
    check('007', INT, 7)
    check('1_000', INT, 1000)
    check('0x10', INT, 16)

    check('3e-4', FLOAT, 3e-4)
    check('5', FLOAT, 5.)
    check('.5', FLOAT, .5)
    check('inf', FLOAT, float('inf'))

    for s in ['1.5', '1e3', 'x', '', 'true', '"5"', '[5]']:
        with pytest.raises(OverrideValueError):
            resolve(s, INT)

    for s in ['x', '', 'true', '"1.5"', '{a: 1}']:
        with pytest.raises(OverrideValueError):
            resolve(s, FLOAT)


def test_bool():
    check('true', BOOL, True)
    check('false', BOOL, False)

    for s in ['1', '0', 'yes', 'True', '"true"', '']:
        with pytest.raises(OverrideValueError):
            resolve(s, BOOL)


def test_choice():
    c = ChoiceShape(['a', 'b', '5', 5, True, None])
    check('a', c, 'a')
    check('"b"', c, 'b')
    check('5', c, '5')
    check('true', c, True)
    check('null', c, None)

    check('5', ChoiceShape([5, 6]), 5)
    check('1', ChoiceShape([1.]), 1.)

    with pytest.raises(OverrideValueError, match="did you mean 'RED'"):
        resolve('REDD', ChoiceShape(['RED', 'BLUE']))
    with pytest.raises(OverrideValueError):
        resolve('"5"', ChoiceShape([5]))
    with pytest.raises(OverrideValueError):
        resolve('[a]', ChoiceShape(['a']))

    # A bool is not an int, nor the other way around.
    with pytest.raises(OverrideValueError):
        resolve('1', ChoiceShape([True]))
    with pytest.raises(OverrideValueError):
        resolve('true', ChoiceShape([1]))


def test_optional():
    check('null', OptionalShape(STR), None)
    check('"null"', OptionalShape(STR), 'null')
    check('x', OptionalShape(STR), 'x')
    check('null', OptionalShape(INT), None)
    check('5', OptionalShape(INT), 5)

    with pytest.raises(OverrideValueError):
        resolve('null', INT)


def test_union():
    u = UnionShape([BOOL, INT, STR])
    check('5', u, 5)
    check('true', u, True)
    check('foo', u, 'foo')
    check('1.5', u, '1.5')
    check('"5"', u, '5')

    check('5', UnionShape([FLOAT, STR]), 5.)
    check('5', UnionShape([ChoiceShape(['auto']), INT]), 5)
    check('auto', UnionShape([ChoiceShape(['auto']), INT]), 'auto')

    uo = UnionShape([INT, ObjectShape({'x': INT}), STR])
    check('5', uo, 5)
    check('{x: 5}', uo, {'x': 5})
    check('{y: 5}', uo, '{y: 5}')

    with pytest.raises(OverrideValueError):
        resolve('foo', UnionShape([INT, FLOAT]))


def test_containers():
    check('[1, 2]', ListShape(INT), [1, 2])
    check('[1, 2]', ListShape(STR), ['1', '2'])
    check('[]', ListShape(INT), [])
    check('[1, x]', TupleShape([INT, STR]), [1, 'x'])
    check('{a: 1, b: 2}', MapShape(FLOAT), {'a': 1., 'b': 2.})

    for s, shape in [
        ('1', ListShape(INT)),
        ('{a: 1}', ListShape(INT)),
        ('[1, x]', ListShape(INT)),
        ('[1]', TupleShape([INT, STR])),
        ('[1]', MapShape(INT)),
    ]:
        with pytest.raises(OverrideValueError):
            resolve(s, shape)

    with pytest.raises(OverrideValueError, match=r"Expected int at 'a\.1', got 'x'"):
        ValueResolver().resolve(parse_raw_value('[1, x]'), ListShape(INT), parse_path('a'))
    with pytest.raises(OverrideValueError, match=r"Expected int at '\[1\]\.b'"):
        resolve('[{b: 1}, {b: x}]', ListShape(MapShape(INT)))


def test_object():
    o = ObjectShape({
        'name': STR,
        'dim': INT,
        'tags': ListShape(STR),
        'sub': OptionalShape(LazyShape(lambda: o)),
    })

    check('{name: 123, dim: 123}', o, {'name': '123', 'dim': 123})
    check(
        '{name: a, tags: [1, x], sub: {dim: 2, sub: null}}',
        o,
        {'name': 'a', 'tags': ['1', 'x'], 'sub': {'dim': 2, 'sub': None}},
    )

    with pytest.raises(OverrideValueError, match="Unknown key 'nmae' at the root - did you mean 'name'"):
        resolve('{nmae: x}', o)
    with pytest.raises(OverrideValueError, match="Unknown key 'dmi' at 'sub'"):
        resolve('{sub: {dmi: 1}}', o)

    oo = ObjectShape({'name': STR}, open=True)
    check('{name: 1, x: 1, y: [a, 2]}', oo, {'name': '1', 'x': 1, 'y': ['a', 2]})


def test_structure_errors_are_reported():
    with pytest.raises(OverrideValueError, match="expected ',' or '}'"):
        resolve('{name: a', ObjectShape({'name': STR}))


def test_tagged_wrapper():
    t = TaggedShape({
        'adam': ObjectShape({'lr': FLOAT}),
        'sgd': ObjectShape({'lr': FLOAT, 'momentum': FLOAT}),
    })

    check('{sgd: {lr: 1}}', t, {'sgd': {'lr': 1.}})
    check('{adam: {}}', t, {'adam': {}})

    for s in ['{sdg: {}}', '{}', '{adam: {}, sgd: {}}', 'adam', '{adam: {momentum: 1}}']:
        with pytest.raises(OverrideValueError):
            resolve(s, t)


def test_tagged_field():
    t = TaggedShape(
        {
            'adam': ObjectShape({'lr': FLOAT}),
            'sgd': ObjectShape({'lr': FLOAT, 'momentum': FLOAT}),
        },
        tag_field='type',
    )

    check('{type: sgd, momentum: 1}', t, {'type': 'sgd', 'momentum': 1.})
    check('{lr: 1, type: adam}', t, {'type': 'adam', 'lr': 1.})

    for s in ['{lr: 1}', '{type: sdg}', '{type: adam, momentum: 1}', 'adam']:
        with pytest.raises(OverrideValueError):
            resolve(s, t)


def test_any():
    check('5', AnyShape(), 5)
    check('"5"', AnyShape(), '5')
    check('foo', AnyShape(), 'foo')
    check('1.10', AnyShape(), 1.1)
    check('{a: [1, x, null]}', AnyShape(), {'a': [1, 'x', None]})
    check('{a: 1', AnyShape(), '{a: 1')
    check('{a: 5}', MapShape(AnyShape()), {'a': 5})


def test_unknown():
    u = UnknownShape('some handler')

    with pytest.raises(UnhandledOverrideShapeError, match='some handler'):
        resolve('5', u)
    check('5', u, 5, guess_unknown=True)
    check('{a: x}', u, {'a': 'x'}, guess_unknown=True)

    # Only when actually reached.
    o = ObjectShape({'a': INT, 'u': u})
    check('{a: 5}', o, {'a': 5})
    with pytest.raises(UnhandledOverrideShapeError, match="at 'u'"):
        resolve('{a: 5, u: 5}', o)
    check('{a: 5, u: 5}', o, {'a': 5, 'u': 5}, guess_unknown=True)

    # Never papered over by a union's other alternatives.
    with pytest.raises(UnhandledOverrideShapeError):
        resolve('foo', UnionShape([INT, u, STR]))
    check('5', UnionShape([INT, u, STR]), 5)
