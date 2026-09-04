from ....text import styled as st
from ..colors import RED
from ..colors import ColorDepth
from ..colors import IndexedColor
from ..parsing import apply_sgr_params
from ..parsing import parse_ansi_text
from ..parsing import strip_ansi_escapes
from ..rendering import render_ansi


def test_parse_ansi_text():
    text = parse_ansi_text('plain \x1b[1;31mbold red\x1b[0m done')

    assert text.text == 'plain bold red done'
    assert text.resolved_runs() == (
        st.ResolvedStyledTextRun('plain '),
        st.ResolvedStyledTextRun('bold red', st.ResolvedStyle(fg=RED, bold=True)),
        st.ResolvedStyledTextRun(' done'),
    )


def test_parsed_styled_runs_are_complete_and_plain_runs_inherit():
    text = parse_ansi_text('\x1b[1mbold\x1b[22m normal')

    base = st.ResolvedStyle(italic=True, bold=True)
    runs = text.resolved_runs(base=base)
    assert runs[0].style == st.ResolvedStyle(bold=True)
    assert runs[1].style == base


def test_parse_drops_non_sgr_escapes_and_keeps_newlines():
    assert parse_ansi_text('\x1b[2Jx\ny\x1b[?25l') == st.StyledText('x\ny')
    assert strip_ansi_escapes('\x1b[2J\x1b[1mx\x1b[0m') == 'x'


def test_apply_sgr_params():
    style = apply_sgr_params(st.PLAIN_STYLE, [1, 4, 38, 5, 196, 48, 2, 1, 2, 3])
    assert style == st.ResolvedStyle(
        fg=IndexedColor(196),
        bg=st.RgbColor(1, 2, 3),
        bold=True,
        underline=True,
    )
    assert apply_sgr_params(style, [39, 24]) == st.ResolvedStyle(bg=st.RgbColor(1, 2, 3), bold=True)
    assert apply_sgr_params(style, []) == st.PLAIN_STYLE
    assert apply_sgr_params(style, [0]) == st.PLAIN_STYLE


def test_render_parse_round_trip():
    text = st.StyledText.assemble(
        'a ',
        ('b', st.StylePatch(fg=st.RgbColor(10, 20, 30), bold=True)),
        ' c',
        ('d', st.StylePatch(bg=RED, underline=True)),
    )

    rendered = render_ansi(text, depth=ColorDepth.TRUE)
    assert parse_ansi_text(rendered).resolved_runs() == text.resolved_runs()
