from omcore.term import styled as tst
from omcore.text import styled as st

from ..rendering import render_ansi_segment_rows
from ..rendering import render_ansi_segments
from ..segments import Segment
from ..styles import Theme


def test_render_ansi_segments() -> None:
    assert render_ansi_segments([
        Segment('plain'),
        Segment('red', 'red'),
        Segment(' still'),
    ], theme=Theme({'red': st.StylePatch(fg=tst.RED)})) == (
        'plain\x1b[0;31mred\x1b[0m still'
    )


def test_render_ansi_segment_rows() -> None:
    assert render_ansi_segment_rows([
        [Segment('one')],
        [],
        [Segment('two')],
    ], trailing_newline=True) == 'one\n\ntwo\n'


def test_render_ansi_segments_downgrade() -> None:
    segments = [Segment('x', st.ResolvedStyle(fg=st.RgbColor(255, 0, 0), bold=True))]

    assert render_ansi_segments(segments, depth=tst.ColorDepth.ANSI_16) == '\x1b[0;1;91mx\x1b[0m'
    assert render_ansi_segments(segments, depth=tst.ColorDepth.MONO) == '\x1b[0;1mx\x1b[0m'
