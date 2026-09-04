from omcore.term.styled import ColorDepth
from omcore.text import styled as st

from ...screens.cells import line_from_segments
from ...screens.cells import render_cells
from ..segments import Segment
from ..segments import styled_text_to_segment_lines
from ..styles import EMPTY_THEME
from ..styles import Style
from ..styles import Theme


##


def test_shared_style_type():
    assert Style is st.ResolvedStyle


def test_styled_text_to_segment_lines_resolves_layers():
    red = st.RgbColor(255, 0, 0)
    theme = Theme({
        'outer': st.StylePatch(fg=red, bold=True),
        'inner': st.StylePatch(
            fg=st.DEFAULT_COLOR,
            bold=False,
            underline=True,
        ),
    })
    text = st.StyledText('a\nbc\n', (
        st.StyleSpan.of(0, 5, 'outer'),
        st.StyleSpan.of(2, 4, 'inner'),
    ))

    assert styled_text_to_segment_lines(text, theme=theme) == [
        [Segment('a', Style(fg=red, bold=True))],
        [Segment('bc', Style(underline=True))],
        [],
    ]


def test_styled_text_renders_headlessly_at_each_color_depth():
    text = st.StyledText('X').styled(st.StylePatch(
        fg=st.RgbColor(255, 0, 0),
        bold=True,
    ))
    rows = styled_text_to_segment_lines(text)
    line = line_from_segments(rows[0], EMPTY_THEME)

    assert render_cells(line.cells, ColorDepth.TRUE) == '\x1b[0;1;38;2;255;0;0mX\x1b[0m'
    assert render_cells(line.cells, ColorDepth.ANSI_256) == '\x1b[0;1;38;5;196mX\x1b[0m'
    assert render_cells(line.cells, ColorDepth.ANSI_16) == '\x1b[0;1;91mX\x1b[0m'
    assert render_cells(line.cells, ColorDepth.MONO) == '\x1b[0;1mX\x1b[0m'
