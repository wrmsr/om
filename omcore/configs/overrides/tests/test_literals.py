import math

import pytest

from ..literals import RawList
from ..literals import RawMap
from ..literals import RawScalar
from ..literals import guess_raw
from ..literals import guess_scalar
from ..literals import parse_raw_value


def test_parse_scalars():
    assert parse_raw_value('foo') == RawScalar('foo')
    assert parse_raw_value('  foo bar, baz ') == RawScalar('foo bar, baz')
    assert parse_raw_value('') == RawScalar('')
    assert parse_raw_value('1.10') == RawScalar('1.10')

    assert parse_raw_value('"foo"') == RawScalar('foo', quoted=True)
    assert parse_raw_value("'fo\"o'") == RawScalar('fo"o', quoted=True)
    assert parse_raw_value(r'"a\n\"b"') == RawScalar('a\n"b', quoted=True)

    # Not a single quoted string, so verbatim.
    assert parse_raw_value('"a" and "b"') == RawScalar('"a" and "b"')
    assert parse_raw_value('"unterminated') == RawScalar('"unterminated')


def test_parse_structures():
    assert parse_raw_value('[]') == RawList([], text='[]')
    assert parse_raw_value('{}') == RawMap([], text='{}')

    s = '{lr: 3e-4, betas: [0.9, 0.99], name: adam, note: "a, b", "k 2": {x: null,},}'
    assert parse_raw_value(s) == RawMap(
        [
            ('lr', RawScalar('3e-4')),
            ('betas', RawList([RawScalar('0.9'), RawScalar('0.99')])),
            ('name', RawScalar('adam')),
            ('note', RawScalar('a, b', quoted=True)),
            ('k 2', RawMap([('x', RawScalar('null'))])),
        ],
        text=s,
    )

    assert parse_raw_value('{url: http://x:80/y}') == RawMap(
        [('url', RawScalar('http://x:80/y'))],
        text='{url: http://x:80/y}',
    )


@pytest.mark.parametrize('s', [
    '{name}-{id}.txt',
    '[a-z]+',
    '{name}',
    '{a: 1',
    '[1,,2]',
    '{a: 1, a: 2}',
    '[1] x',
])
def test_parse_malformed_structures_are_scalars(s):
    n = parse_raw_value(s)
    assert isinstance(n, RawScalar)
    assert n.text == s
    assert not n.quoted
    assert n.structure_error is not None


def test_guess_scalar():
    for s, v in [
        ('null', None),
        ('true', True),
        ('false', False),
        ('0', 0),
        ('5', 5),
        ('-5', -5),
        ('+5', 5),
        ('0x1F', 31),
        ('-0x10', -16),
        ('1.10', 1.1),
        ('5.', 5.),
        ('.5', .5),
        ('3e-4', 3e-4),
        ('1E3', 1000.),
        ('Infinity', math.inf),
        ('-Infinity', -math.inf),
    ]:
        g = guess_scalar(s)
        assert g == v
        assert type(g) is type(v)

    assert math.isnan(guess_scalar('NaN'))

    for s in [
        '',
        'foo',
        'True',
        'None',
        'nan',
        'inf',
        '007',
        '1_000',
        '1.2.3',
        '1e',
        '0x',
        '5 6',
        '-',
        '2026-01-01',
    ]:
        assert guess_scalar(s) == s


def test_guess_raw():
    assert guess_raw(parse_raw_value('{a: 1, b: [x, "2", 2, null], c: {d: true}}')) == {
        'a': 1,
        'b': ['x', '2', 2, None],
        'c': {'d': True},
    }
    assert guess_raw(parse_raw_value('"5"')) == '5'
    assert guess_raw(parse_raw_value('5')) == 5
