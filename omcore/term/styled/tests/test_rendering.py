from ....text import styled as st
from ..colors import RED
from ..colors import ColorDepth
from ..rendering import render_ansi
from ..rendering import render_ansi_runs
from ..sgr import sgr_transition
from ..sgr import style_sgr


def test_style_sgr():
    assert style_sgr(st.PLAIN_STYLE) == ''
    assert style_sgr(st.ResolvedStyle(bold=True)) == '\x1b[0;1m'
    assert style_sgr(st.ResolvedStyle(fg=RED)) == '\x1b[0;31m'
    assert style_sgr(st.ResolvedStyle(fg=st.RgbColor(255, 0, 0), bold=True)) == '\x1b[0;1;38;2;255;0;0m'
    assert style_sgr(st.ResolvedStyle(fg=st.RgbColor(255, 0, 0)), ColorDepth.ANSI_256) == '\x1b[0;38;5;196m'
    assert style_sgr(st.ResolvedStyle(fg=st.RgbColor(255, 0, 0)), ColorDepth.ANSI_16) == '\x1b[0;91m'
    assert style_sgr(st.ResolvedStyle(fg=st.RgbColor(255, 0, 0)), ColorDepth.MONO) == ''


def test_sgr_transition():
    bold = st.ResolvedStyle(bold=True)
    assert sgr_transition(bold, bold) == ''
    assert sgr_transition(st.PLAIN_STYLE, bold) == '\x1b[0;1m'
    assert sgr_transition(bold, st.PLAIN_STYLE) == '\x1b[0m'


def test_render_ansi_runs():
    assert render_ansi_runs([
        st.ResolvedStyledTextRun('plain'),
        st.ResolvedStyledTextRun('red', st.ResolvedStyle(fg=RED)),
        st.ResolvedStyledTextRun(' still'),
    ]) == 'plain\x1b[0;31mred\x1b[0m still'

    assert render_ansi_runs([]) == ''


def test_render_ansi_text():
    text = st.StyledText('a\nb').styled(st.StylePatch(bold=True))

    assert render_ansi(text, depth=ColorDepth.MONO) == '\x1b[0;1ma\x1b[0m\n\x1b[0;1mb\x1b[0m'
    assert render_ansi('plain\n') == 'plain\n'
    assert render_ansi('') == ''


def test_render_ansi_document_with_theme_and_base():
    document = st.StyledDocument.of_lines([
        st.StyledText('one').styled('strong'),
        'two',
    ], trailing_newline=True)
    theme = st.StyleTheme({'strong': st.StylePatch(bold=True)})

    assert render_ansi(document, theme=theme) == '\x1b[0;1mone\x1b[0m\ntwo\n'
    assert render_ansi(document, theme=theme, base=st.ResolvedStyle(italic=True)) == (
        '\x1b[0;1;3mone\x1b[0m\n\x1b[0;3mtwo\x1b[0m\n'
    )
