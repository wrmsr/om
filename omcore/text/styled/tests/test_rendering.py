import pytest

from ..colors import Color
from ..colors import RgbColor
from ..html import render_html
from ..html import style_to_css
from ..plain import render_plain
from ..styles import DEFAULT_COLOR
from ..styles import ResolvedStyle
from ..styles import StylePatch
from ..styles import StyleTheme
from ..text import StyledText
from ..text import StyleSpan


##


def test_render_plain():
    text = StyledText('<hello>\nworld').styled(StylePatch(bold=True))

    assert render_plain(text) == '<hello>\nworld'
    assert render_plain('plain') == 'plain'


def test_render_html_escapes_text_but_not_quotes():
    assert render_html('<b>& "quoted"\n') == '&lt;b&gt;&amp; "quoted"\n'


def test_render_html_resolves_overlapping_styles():
    red = RgbColor(255, 0, 0)
    theme = StyleTheme({
        'outer': StylePatch(fg=red, bold=True),
        'inner': StylePatch(
            fg=DEFAULT_COLOR,
            bold=False,
            underline=True,
        ),
    })
    text = StyledText('abc', (
        StyleSpan.of(0, 3, 'outer'),
        StyleSpan.of(1, 2, 'inner'),
    ))

    assert render_html(text, theme=theme) == (
        '<span style="color:#ff0000;font-weight:bold">a</span>'
        '<span style="text-decoration-line:underline">b</span>'
        '<span style="color:#ff0000;font-weight:bold">c</span>'
    )


def test_render_html_coalesces_equivalent_resolved_runs():
    theme = StyleTheme({
        'left': StylePatch(bold=True),
        'right': StylePatch(bold=True),
    })
    text = StyledText('ab', (
        StyleSpan.of(0, 1, 'left'),
        StyleSpan.of(1, 2, 'right'),
    ))

    assert render_html(text, theme=theme) == '<span style="font-weight:bold">ab</span>'


def test_style_to_css_resets_to_base():
    base = ResolvedStyle(
        fg=RgbColor(255, 0, 0),
        bg=RgbColor(0, 0, 255),
        bold=True,
        dim=True,
        italic=True,
        underline=True,
        hidden=True,
    )
    style = StylePatch(
        fg=DEFAULT_COLOR,
        bg=DEFAULT_COLOR,
        bold=False,
        dim=False,
        italic=False,
        underline=False,
        hidden=False,
    ).resolve(base)

    assert style_to_css(style, base=base) == (
        'color:initial;background-color:initial;font-weight:normal;opacity:1;font-style:normal;'
        'text-decoration-line:none;visibility:visible'
    )


def test_style_to_css_combines_decorations_and_other_attributes():
    assert style_to_css(ResolvedStyle(
        dim=True,
        italic=True,
        underline=True,
        blink=True,
        strike=True,
        hidden=True,
    )) == (
        'opacity:.5;font-style:italic;text-decoration-line:underline blink line-through;visibility:hidden'
    )


def test_style_to_css_reverse_uses_css_system_colors_without_explicit_colors():
    assert style_to_css(ResolvedStyle(reverse=True)) == 'color:Canvas;background-color:CanvasText'


def test_render_html_rejects_target_specific_color():
    class TargetColor(Color):
        pass

    with pytest.raises(TypeError, match='TargetColor'):
        render_html(StyledText('x').styled(StylePatch(fg=TargetColor())))
