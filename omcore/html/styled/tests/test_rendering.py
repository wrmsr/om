import pytest

from ....text import styled as st
from ..css import style_to_css
from ..rendering import render_html


def test_render_html_escapes_text_but_not_quotes():
    assert render_html('<b>& "quoted"\n') == '&lt;b&gt;&amp; "quoted"\n'


def test_render_html_resolves_overlapping_styles():
    red = st.RgbColor(255, 0, 0)
    theme = st.StyleTheme({
        'outer': st.StylePatch(fg=red, bold=True),
        'inner': st.StylePatch(
            fg=st.DEFAULT_COLOR,
            bold=False,
            underline=True,
        ),
    })
    text = st.StyledText('abc', (
        st.StyleSpan.of(0, 3, 'outer'),
        st.StyleSpan.of(1, 2, 'inner'),
    ))

    assert render_html(text, theme=theme) == (
        '<span style="color:#ff0000;font-weight:bold">a</span>'
        '<span style="text-decoration-line:underline">b</span>'
        '<span style="color:#ff0000;font-weight:bold">c</span>'
    )


def test_render_html_coalesces_equivalent_resolved_runs():
    theme = st.StyleTheme({
        'left': st.StylePatch(bold=True),
        'right': st.StylePatch(bold=True),
    })
    text = st.StyledText('ab', (
        st.StyleSpan.of(0, 1, 'left'),
        st.StyleSpan.of(1, 2, 'right'),
    ))

    assert render_html(text, theme=theme) == '<span style="font-weight:bold">ab</span>'


def test_render_html_document():
    document = st.StyledDocument.of_lines([
        st.StyledText('<one>').styled(st.StylePatch(bold=True)),
        'two',
    ], trailing_newline=True)

    assert render_html(document) == '<span style="font-weight:bold">&lt;one&gt;</span>\ntwo\n'


def test_style_to_css_resets_to_base():
    base = st.ResolvedStyle(
        fg=st.RgbColor(255, 0, 0),
        bg=st.RgbColor(0, 0, 255),
        bold=True,
        dim=True,
        italic=True,
        underline=True,
        hidden=True,
    )
    style = st.StylePatch(
        fg=st.DEFAULT_COLOR,
        bg=st.DEFAULT_COLOR,
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
    assert style_to_css(st.ResolvedStyle(
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
    assert style_to_css(st.ResolvedStyle(reverse=True)) == 'color:Canvas;background-color:CanvasText'


def test_render_html_rejects_target_specific_color():
    class TargetColor(st.Color):
        pass

    with pytest.raises(TypeError, match='TargetColor'):
        render_html(st.StyledText('x').styled(st.StylePatch(fg=TargetColor())))
