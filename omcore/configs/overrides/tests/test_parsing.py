import pytest

from ..errors import OverrideSyntaxError
from ..literals import RawScalar
from ..ops import FileOpValue
from ..ops import MergeOp
from ..ops import RawOpValue
from ..ops import RemoveOp
from ..ops import SetOp
from ..parsing import parse_override
from ..parsing import parse_path
from ..paths import AppendSegment
from ..paths import IndexSegment
from ..paths import KeySegment
from ..paths import SelectSegment
from ..paths import render_path


def test_paths():
    assert parse_path('') == ()
    assert parse_path('a') == (KeySegment('a'),)
    assert parse_path('.a') == (KeySegment('a'),)
    assert parse_path('a.b-c.d_e') == (KeySegment('a'), KeySegment('b-c'), KeySegment('d_e'))

    assert parse_path('a[0][-1]') == (KeySegment('a'), IndexSegment(0), IndexSegment(-1))
    assert parse_path('a.0.-1') == (KeySegment('a'), KeySegment('0'), KeySegment('-1'))
    assert parse_path('[0].a') == (IndexSegment(0), KeySegment('a'))

    assert parse_path('a[+]') == (KeySegment('a'), AppendSegment())
    assert parse_path('a.+') == (KeySegment('a'), AppendSegment())
    assert parse_path('a[+].b') == (KeySegment('a'), AppendSegment(), KeySegment('b'))

    assert parse_path('a."b c".d') == (KeySegment('a'), KeySegment('b c', quoted=True), KeySegment('d'))
    assert parse_path('a["b.c"]') == (KeySegment('a'), KeySegment('b.c', quoted=True))
    assert parse_path("a['0']") == (KeySegment('a'), KeySegment('0', quoted=True))
    assert parse_path('"a b"') == (KeySegment('a b', quoted=True),)


def test_select_paths():
    assert parse_path('a[name=enc].dim') == (
        KeySegment('a'),
        SelectSegment(['name'], RawScalar('enc')),
        KeySegment('dim'),
    )
    assert parse_path('a[ spec.id = 3 ]') == (KeySegment('a'), SelectSegment(['spec', 'id'], RawScalar('3')))
    assert parse_path('a[name="x ] y"]') == (KeySegment('a'), SelectSegment(['name'], RawScalar('x ] y', quoted=True)))
    assert parse_path('a["k 1".n=two words]') == (
        KeySegment('a'),
        SelectSegment(['k 1', 'n'], RawScalar('two words')),
    )
    assert parse_path('a[0=x]') == (KeySegment('a'), SelectSegment(['0'], RawScalar('x')))


@pytest.mark.parametrize('s', [
    'a.b.c',
    'a.0.-1.+',
    '[0].a',
    '[+]',
    'a["b c"].d',
    'a["0"]',
    'a[name=enc].dim',
    'a[spec.id="3"]',
    '["a.b"]',
])
def test_render_paths(s):
    assert render_path(parse_path(s)) == s


def test_render_paths_prefers_dots():
    assert render_path(parse_path('a[0][+]')) == 'a.0.+'
    assert render_path(parse_path('a."b"')) == 'a.b'


@pytest.mark.parametrize('s', [
    'a..b',
    'a.',
    'a b',
    'a[',
    'a[]',
    'a[foo]',
    'a[=x]',
    'a[k=]',
    'a[0',
    'a."b',
    'a.b!',
])
def test_path_errors(s):
    with pytest.raises(OverrideSyntaxError):
        parse_path(s)


def test_statements():
    assert parse_override('a.b=1') == SetOp(parse_path('a.b'), RawOpValue('1'))
    assert parse_override(' a.b = 1 ') == SetOp(parse_path('a.b'), RawOpValue('1'))
    assert parse_override('a.b=') == SetOp(parse_path('a.b'), RawOpValue(''))
    assert parse_override('a=b=c') == SetOp(parse_path('a'), RawOpValue('b=c'))
    assert parse_override('a.b={x: [1, 2]}') == SetOp(parse_path('a.b'), RawOpValue('{x: [1, 2]}'))
    assert parse_override('={}') == SetOp((), RawOpValue('{}'))

    assert parse_override('a.b+={x: 1}') == MergeOp(parse_path('a.b'), RawOpValue('{x: 1}'))
    assert parse_override('+={x: 1}') == MergeOp((), RawOpValue('{x: 1}'))

    # Append then set, as opposed to a merge into `a`.
    assert parse_override('a.+=x') == SetOp(parse_path('a[+]'), RawOpValue('x'))
    assert parse_override('a[+]=x') == SetOp(parse_path('a[+]'), RawOpValue('x'))
    assert parse_override('a+=x') == MergeOp(parse_path('a'), RawOpValue('x'))

    assert parse_override('/a.b') == RemoveOp(parse_path('a.b'))
    assert parse_override('/a[name=x]') == RemoveOp(parse_path('a[name=x]'))

    assert parse_override('a.b=@c.json') == SetOp(parse_path('a.b'), FileOpValue('c.json'))
    assert parse_override('a.b+=@~/c.yml') == MergeOp(parse_path('a.b'), FileOpValue('~/c.yml'))
    assert parse_override('@c.json') == MergeOp((), FileOpValue('c.json'))
    assert parse_override('a.b="@c.json"') == SetOp(parse_path('a.b'), RawOpValue('"@c.json"'))


@pytest.mark.parametrize('s', [
    '',
    'a.b',
    'a.b 1',
    '/',
    '/a.b=1',
    '/a b',
    '@',
    'a=@',
    'a..b=1',
    '+a=1',
])
def test_statement_errors(s):
    with pytest.raises(OverrideSyntaxError):
        parse_override(s)
