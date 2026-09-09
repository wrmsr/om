"""
Word wrapping over styled segments - the grid lowering in `omcore.text.styled.grid`, adapted to segment rows.

Wraps a single logical line (no newlines - split those first) to a column width: breaks at spaces, hard-breaks words
wider than the whole line, drops whitespace at wrap points, and preserves per-character styles throughout.
"""
from omcore.text.styled import grid

from .segments import Segment
from .segments import Segments
from .segments import segments_to_styled_text
from .segments import styled_text_to_segments


##


def wrap_segments(segments: Segments, width: int) -> list[list[Segment]]:
    """
    Wrap one logical line of segments to `width` columns, returning the rows (at least one, possibly empty).

    Rows never exceed `width` display columns; whitespace at a wrap point is dropped, interior whitespace preserved.
    """

    return [
        styled_text_to_segments(line)
        for line in grid.wrap(segments_to_styled_text(segments), width)
    ]
