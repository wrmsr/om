import pytest

from .. import DEFAULT_COLOR
from .. import EMPTY_STYLE_PATCH
from .. import PLAIN_STYLE
from .. import ResolvedStyle
from .. import RgbColor
from .. import StyledText
from .. import StyledTextBuilder
from .. import StyledTextRun
from .. import StyleName
from .. import StylePatch
from .. import StyleSpan
from .. import StyleTheme
from .. import parse_rgb


##


def test_rgb():
    assert parse_rgb('#123456') == RgbColor(0x12, 0x34, 0x56)
    assert parse_rgb('#abc') == RgbColor(0xaa, 0xbb, 0xcc)
    assert parse_rgb('#abc').hex == '#aabbcc'


@pytest.mark.parametrize('value', ['abc', '#abcd', '#gggggg'])
def test_rgb_rejects_invalid_strings(value):
    with pytest.raises(ValueError, match=value):
        parse_rgb(value)


@pytest.mark.parametrize(('channels', 'match'), [
    ((-1, 0, 0), '-1'),
    ((0, 256, 0), '256'),
    ((0, 0, True), 'True'),
])
def test_rgb_rejects_invalid_channels(channels, match):
    with pytest.raises(ValueError, match=match):
        RgbColor(*channels)


##


def test_patch_overlay_is_per_property_and_tri_state():
    red = RgbColor(255, 0, 0)
    blue = RgbColor(0, 0, 255)

    parent = StylePatch(fg=red, bg=blue, bold=True, italic=True)
    child = StylePatch(fg=DEFAULT_COLOR, bold=False, underline=True)
    composed = parent.overlay(child)

    assert composed.fg is DEFAULT_COLOR
    assert composed.bg == blue
    assert composed.bold is False
    assert composed.italic is True
    assert composed.underline is True


def test_patch_resolution_can_inherit_and_clear():
    red = RgbColor(255, 0, 0)
    blue = RgbColor(0, 0, 255)
    base = ResolvedStyle(fg=red, bg=blue, bold=True, italic=True)

    resolved = StylePatch(
        fg=DEFAULT_COLOR,
        bold=False,
        underline=True,
    ).resolve(base)

    assert resolved.fg is None
    assert resolved.bg == blue
    assert resolved.bold is False
    assert resolved.italic is True
    assert resolved.underline is True


def test_empty_and_plain_styles():
    assert EMPTY_STYLE_PATCH.is_empty
    assert PLAIN_STYLE.is_plain
    assert EMPTY_STYLE_PATCH.overlay(StylePatch()) is EMPTY_STYLE_PATCH


def test_theme_resolution():
    red = RgbColor(255, 0, 0)
    theme = StyleTheme({
        'outer': StylePatch(fg=red, bold=True),
        StyleName('inner'): StylePatch(bold=False, italic=True),
    })

    resolved = theme.resolve_refs((
        StyleName('outer'),
        StyleName('inner'),
    ))

    assert resolved.fg == red
    assert resolved.bold is False
    assert resolved.italic is True
    assert theme.resolve(StyleName('unknown')) == EMPTY_STYLE_PATCH
    assert theme.as_dict() == {
        'outer': StylePatch(fg=red, bold=True),
        'inner': StylePatch(bold=False, italic=True),
    }


def test_theme_extension_does_not_mutate_original():
    theme = StyleTheme({'x': StylePatch(bold=True)})
    extended = theme.extend({
        'x': StylePatch(italic=True),
        'y': StylePatch(underline=True),
    })

    assert theme.resolve(StyleName('x')) == StylePatch(bold=True)
    assert extended.resolve(StyleName('x')) == StylePatch(italic=True)
    assert extended.resolve(StyleName('y')) == StylePatch(underline=True)


##


def test_plain_value():
    text = StyledText('hello')

    assert text.plain == 'hello'
    assert str(text) == 'hello'
    assert len(text) == 5
    assert text
    assert text.runs() == (StyledTextRun('hello'),)
    assert StyledText().runs() == ()


def test_overlapping_spans_flatten_in_insertion_order():
    text = StyledText('abcdef', (
        StyleSpan.of(0, 4, 'outer'),
        StyleSpan.of(2, 6, 'inner'),
    ))

    assert text.runs() == (
        StyledTextRun('ab', (StyleName('outer'),)),
        StyledTextRun('cd', (StyleName('outer'), StyleName('inner'))),
        StyledTextRun('ef', (StyleName('inner'),)),
    )


def test_span_order_does_not_depend_on_start_position():
    text = StyledText('abcdef', (
        StyleSpan.of(2, 6, 'higher-start'),
        StyleSpan.of(0, 4, 'lower-start'),
    ))

    assert text.runs()[1] == StyledTextRun(
        'cd',
        (StyleName('higher-start'), StyleName('lower-start')),
    )


def test_resolved_runs_compose_and_coalesce():
    red = RgbColor(255, 0, 0)
    theme = StyleTheme({
        'outer': StylePatch(fg=red, bold=True),
        'inner': StylePatch(bold=False),
    })
    text = StyledText('abcd', (
        StyleSpan.of(0, 4, 'outer'),
        StyleSpan.of(1, 3, 'inner'),
    ))

    runs = text.resolved_runs(theme)

    assert tuple(run.text for run in runs) == ('a', 'bc', 'd')
    assert runs[0].style == ResolvedStyle(fg=red, bold=True)
    assert runs[1].style == ResolvedStyle(fg=red, bold=False)
    assert runs[2].style == ResolvedStyle(fg=red, bold=True)

    unknown_runs = StyledText('abc').styled('missing').resolved_runs(theme)
    assert unknown_runs[0].text == 'abc'
    assert unknown_runs[0].style == PLAIN_STYLE


def test_concat_shifts_spans():
    left = StyledText('ab').styled('left', 1, 2)
    right = StyledText('de').styled('right', 0, 1)

    text = StyledText.of(left, 'c', right)

    assert text.text == 'abcde'
    assert text.spans == (
        StyleSpan.of(1, 2, 'left'),
        StyleSpan.of(3, 4, 'right'),
    )
    assert left + 'c' + right == text


def test_slice_clips_and_shifts_spans():
    text = StyledText('abcdef', (
        StyleSpan.of(0, 3, 'left'),
        StyleSpan.of(2, 6, 'right'),
    ))

    assert text.slice(1, 5) == StyledText('bcde', (
        StyleSpan.of(0, 2, 'left'),
        StyleSpan.of(1, 4, 'right'),
    ))
    assert text.slice(-3, -1) == StyledText('de', (
        StyleSpan.of(0, 2, 'right'),
    ))
    assert text.slice(4, 2) == StyledText()


def test_join():
    separator = StyledText(', ').styled('separator')
    value = separator.join((
        StyledText('a').styled('item'),
        'b',
        'c',
    ))

    assert value.text == 'a, b, c'
    assert value.spans == (
        StyleSpan.of(0, 1, 'item'),
        StyleSpan.of(1, 3, 'separator'),
        StyleSpan.of(4, 6, 'separator'),
    )


def test_empty_patch_and_empty_range_are_noops():
    text = StyledText('abc')

    assert text.styled(StylePatch()) is text
    assert text.styled('x', 1, 1) is text


def test_span_validation():
    with pytest.raises(ValueError, match='1'):
        StyleSpan.of(1, 1, 'x')
    with pytest.raises(ValueError, match='1'):
        StyledText('a', (StyleSpan.of(0, 2, 'x'),))
    with pytest.raises(ValueError, match='0'):
        StyledText('a').styled('x', 0, 2)


##


def test_builder_append_preserves_inner_priority():
    red = RgbColor(255, 0, 0)
    green = RgbColor(0, 255, 0)
    inner = StyledText('x').styled(StylePatch(fg=green, italic=True))

    builder = StyledTextBuilder()
    builder.append(inner, StylePatch(fg=red, bold=True))
    value = builder.build()

    assert value.runs()[0].styles == (
        StylePatch(fg=red, bold=True),
        StylePatch(fg=green, italic=True),
    )
    assert value.resolved_runs()[0].style == ResolvedStyle(
        fg=green,
        bold=True,
        italic=True,
    )


def test_builder_stylize_and_clear():
    builder = StyledTextBuilder()
    builder.append('ab').append('cd')
    builder.stylize('middle', 1, 3)

    assert builder.position == 4
    assert builder.build() == StyledText('abcd', (
        StyleSpan.of(1, 3, 'middle'),
    ))

    builder.clear()
    assert not builder
    assert builder.build() == StyledText()
