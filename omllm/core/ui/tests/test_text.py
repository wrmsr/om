# ruff: noqa: B017 PT011
import pytest

from omcore import marshal as msh

from ..text import ConcatText
from ..text import StrText
from ..text import StyleText
from ..text import Text
from ..text import TextStyle


def assert_no_concat_children(t: Text) -> None:
    if isinstance(t, ConcatText):
        for c in t.l:
            assert not isinstance(c, ConcatText)
            assert_no_concat_children(c)

    elif isinstance(t, StyleText):
        assert_no_concat_children(t.c)


def assert_no_empty_concat_children(t: Text) -> None:
    if isinstance(t, ConcatText):
        assert t.l
        for c in t.l:
            assert bool(c)
            assert_no_empty_concat_children(c)

    elif isinstance(t, StyleText):
        assert_no_empty_concat_children(t.c)


def assert_no_adjacent_str_children(t: Text) -> None:
    if isinstance(t, ConcatText):
        last_was_str = False
        for c in t.l:
            is_str = isinstance(c, StrText)
            assert not (last_was_str and is_str)
            last_was_str = is_str
            assert_no_adjacent_str_children(c)

    elif isinstance(t, StyleText):
        assert_no_adjacent_str_children(t.c)


def assert_canonical(t: Text) -> None:
    assert_no_concat_children(t)
    assert_no_empty_concat_children(t)
    assert_no_adjacent_str_children(t)


def test_blank_is_singleton() -> None:
    assert Text.blank() is Text.of()
    assert Text.of('') is Text.blank()
    assert Text.of('', [], (), ['', []]) is Text.blank()


def test_single_text_is_returned_as_is() -> None:
    s = StrText('abc')

    assert Text.of(s) is s


def test_plain_strings_are_merged() -> None:
    t = Text.of('a', 'b', '', 'c')

    assert isinstance(t, StrText)
    assert t.s == 'abc'
    assert str(t) == 'abc'
    assert_canonical(t)


def test_nested_sequences_are_flattened_without_concat_when_all_strings() -> None:
    t = Text.of(['a', ['b', ('c', ['', 'd'])]], 'e')

    assert isinstance(t, StrText)
    assert t.s == 'abcde'
    assert str(t) == 'abcde'
    assert_canonical(t)


def test_existing_concat_is_flattened() -> None:
    styled = StyleText(
        StrText('c'),
        TextStyle(color='red'),
    )

    inner = ConcatText((
        StrText('b'),
        styled,
        StrText('d'),
    ))

    t = Text.of('a', inner, 'e')

    assert isinstance(t, ConcatText)
    assert list(t.l) == [
        StrText('ab'),
        styled,
        StrText('de'),
    ]

    assert str(t) == 'abcde'
    assert_canonical(t)


def test_adjacent_strs_are_merged_across_sequence_boundaries() -> None:
    t = Text.of(
        'a',
        ['b', ['c']],
        ('d',),
        ['e'],
    )

    assert isinstance(t, StrText)
    assert t.s == 'abcde'
    assert_canonical(t)


def test_style_is_preserved_as_boundary() -> None:
    styled = StyleText(
        StrText('b'),
        TextStyle(color='green', bold=True),
    )

    t = Text.of('a', styled, 'c')

    assert isinstance(t, ConcatText)
    assert list(t.l) == [
        StrText('a'),
        styled,
        StrText('c'),
    ]

    assert str(t) == 'abc'
    assert_canonical(t)


def test_adjacent_strings_on_both_sides_of_style_do_not_merge_across_style() -> None:
    styled = StyleText(
        StrText('X'),
        TextStyle(italic=True),
    )

    t = Text.of(['a', 'b'], styled, ['c', 'd'])

    assert isinstance(t, ConcatText)
    assert list(t.l) == [
        StrText('ab'),
        styled,
        StrText('cd'),
    ]

    assert str(t) == 'abXcd'
    assert_canonical(t)


def test_empty_strings_and_empty_sequences_are_removed_around_style() -> None:
    styled = StyleText(
        StrText('x'),
        TextStyle(color='blue'),
    )

    t = Text.of('', [], ['', styled, ''], (), '')

    assert t is styled
    assert str(t) == 'x'
    assert_canonical(t)


def test_str_of_fast_path_for_plain_string() -> None:
    assert Text.str_of('abc') == 'abc'


def test_str_of_coerces_nested_text() -> None:
    styled = StyleText(
        StrText('b'),
        TextStyle(color='yellow'),
    )

    assert Text.str_of(['a', styled, 'c']) == 'abc'


def test_join_with_empty_delimiter() -> None:
    t = Text.of('').join(['a', ['b'], 'c'])

    assert isinstance(t, StrText)
    assert t.s == 'abc'
    assert_canonical(t)


def test_join_with_string_delimiter() -> None:
    t = Text.of(', ').join(['a', 'b', 'c'])

    assert isinstance(t, StrText)
    assert t.s == 'a, b, c'
    assert str(t) == 'a, b, c'
    assert_canonical(t)


def test_join_with_styled_delimiter_preserves_boundaries() -> None:
    delim = StyleText(
        StrText('|'),
        TextStyle(color='red'),
    )

    t = delim.join(['a', 'b', 'c'])

    assert isinstance(t, ConcatText)
    assert list(t.l) == [
        StrText('a'),
        delim,
        StrText('b'),
        delim,
        StrText('c'),
    ]

    assert str(t) == 'a|b|c'
    assert_canonical(t)


def test_of_single_blank_text_is_blank_singleton() -> None:
    assert Text.of(StrText('')) is Text.blank()


def test_of_unwraps_default_style() -> None:
    t = Text.of('a', StyleText(StrText('b')), 'c')

    assert isinstance(t, StrText)
    assert t.s == 'abc'

    s = StrText('x')
    assert Text.of(StyleText(s)) == s


def test_str_is_cached() -> None:
    t = ConcatText((
        StrText('abc '),
        StyleText(StrText('def!'), TextStyle(bold=True)),
    ))

    s1 = str(t)
    s2 = str(t)
    assert s1 is s2


def test_style_with_no_attrs_is_noop() -> None:
    t = Text.of('abc')

    assert t.style() is t


def test_style_of_blank_is_blank() -> None:
    assert Text.of('').style(color='red') is Text.blank()


def test_style_with_attrs_wraps_once() -> None:
    t = Text.of('abc').style(color='red', bold=True)

    assert isinstance(t, StyleText)
    assert t.c == StrText('abc')
    assert t.y == TextStyle(color='red', bold=True)
    assert str(t) == 'abc'
    assert_canonical(t)


def test_style_merges_onto_existing_style() -> None:
    t = Text.of('x').style(color='red').style(color='green', bold=True)

    assert isinstance(t, StyleText)
    assert t.c == StrText('x')
    assert t.y == TextStyle(color='red', bold=True)


def test_style_text_rejects_nested_style() -> None:
    inner = StyleText(StrText('a'), TextStyle(bold=True))

    with pytest.raises(Exception):
        StyleText(inner, TextStyle(italic=True))


def test_concat_rejects_empty_children() -> None:
    with pytest.raises(Exception):
        ConcatText((StrText('a'), StrText('')))


def test_concat_rejects_nested_concat_children() -> None:
    inner = ConcatText((
        StrText('a'),
        StyleText(StrText('b')),
    ))

    with pytest.raises(Exception):
        ConcatText((inner, StrText('c')))


def test_concat_rejects_adjacent_str_children() -> None:
    with pytest.raises(Exception):
        ConcatText((StrText('a'), StrText('b')))


def test_deeply_nested_sequence_does_not_recurse() -> None:
    obj = 'x'
    for _ in range(10_000):
        obj = [obj]  # type: ignore

    t = Text.of(obj)

    assert isinstance(t, StrText)
    assert t.s == 'x'
    assert_canonical(t)


def test_many_nested_singletons_with_strings_are_linearish() -> None:
    objs = []
    for i in range(1_000):
        objs.append([str(i), ['-']])

    t = Text.of(*objs)

    assert isinstance(t, StrText)
    assert t.s == ''.join(f'{i}-' for i in range(1_000))
    assert_canonical(t)


def test_marshal() -> None:
    tx = ConcatText((
        StrText('abc'),
        StyleText(
            StrText('def'),
            TextStyle(color='red'),
        ),
        StrText('ghi'),
    ))

    v = msh.marshal(tx, Text)

    tx2 = msh.unmarshal(v, Text)

    assert tx2 == tx
