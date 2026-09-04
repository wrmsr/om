from omcore.text import styled as st

from ..colors import RED
from ..colors import ColorDepth
from ..rendering import render_ansi_segment_rows
from ..rendering import render_ansi_segments
from ..rendering import render_ansi_styled_document
from ..rendering import render_ansi_styled_text
from ..segments import Segment
from ..styles import Theme


def test_render_ansi_segments() -> None:
    assert render_ansi_segments([
        Segment('plain'),
        Segment('red', 'red'),
        Segment(' still'),
    ], theme=Theme({'red': st.StylePatch(fg=RED)})) == (
        'plain\x1b[0;31mred\x1b[0m still'
    )


def test_render_ansi_segment_rows() -> None:
    assert render_ansi_segment_rows([
        [Segment('one')],
        [],
        [Segment('two')],
    ], trailing_newline=True) == 'one\n\ntwo\n'


def test_render_ansi_styled_text() -> None:
    text = st.StyledText('a\nb').styled(st.StylePatch(bold=True))

    assert render_ansi_styled_text(text, depth=ColorDepth.MONO) == (
        '\x1b[0;1ma\x1b[0m\n\x1b[0;1mb\x1b[0m'
    )


def test_render_ansi_styled_document() -> None:
    document = st.StyledDocument.of_lines([
        st.StyledText('one').styled('strong'),
        'two',
    ], trailing_newline=True)

    assert render_ansi_styled_document(
        document,
        theme=Theme({'strong': st.StylePatch(bold=True)}),
    ) == '\x1b[0;1mone\x1b[0m\ntwo\n'
