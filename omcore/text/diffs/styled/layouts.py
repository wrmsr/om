# Copyright (c) 2025 Darren Burns
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""What a document hands a hunk layout, the interface a layout implements, and the pieces layouts share."""
import abc
import difflib
import typing as ta

from .... import dataclasses as dc
from .... import lang
from ... import diffs
from ... import styled as st
from ...styled import grid
from .highlighting import HighlightedLines


##


@dc.dataclass(frozen=True, kw_only=True)
class DiffFileLines(lang.Final):
    """A file's code as its hunks' layout draws it: highlighted, by line number on each side, and the widest numbers."""

    source: HighlightedLines
    target: HighlightedLines

    source_max: int
    target_max: int


class DiffHunkLayout(lang.Abstract):
    """Lays out the lines of a hunk, each row the document's full width, beneath the header the document gives it."""

    @abc.abstractmethod
    def render_hunk(self, hunk: diffs.Hunk, lines: DiffFileLines) -> ta.Sequence[st.StyledText]:
        raise NotImplementedError


##


def intraline_ranges(source: str, target: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """The changed character ranges within a pair of similar lines, or none where the lines are too unlike to pair."""

    matcher = difflib.SequenceMatcher(None, source, target)
    if matcher.ratio() <= .5:
        return [], []

    removed: list[tuple[int, int]] = []
    added: list[tuple[int, int]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ('delete', 'replace'):
            removed.append((i1, i2))
        if tag in ('insert', 'replace'):
            added.append((j1, j2))
    return removed, added


_LINE_STYLES: ta.Mapping[diffs.HunkLineKind, tuple[str, str]] = {
    diffs.HunkLineKind.REMOVE: ('diff.line.remove', 'diff.intraline.remove'),
    diffs.HunkLineKind.ADD: ('diff.line.add', 'diff.intraline.add'),
}


def render_code_line(
        code: st.StyledText,
        gutter: st.StyledText,
        *,
        width: int,
        tab_size: int,
        kind: diffs.HunkLineKind,
        intraline: ta.Sequence[tuple[int, int]] = (),
) -> st.StyledText:
    """
    One line of code behind its gutter, exactly `width` cells: truncated to fit, padded out, a changed line on its
    side's background and the ranges of `intraline` within it marked. The gutter is plain text, so its length is its
    width.
    """

    code = grid.indent_guides(code, tab_size, style='diff.indent')
    content_width = max(width - grid.cell_width(gutter), 0)
    code = grid.truncate(code, content_width)

    builder = st.StyledTextBuilder()
    builder.append(gutter)
    builder.append(code)
    builder.append(' ' * max(content_width - grid.cell_width(code), 0))
    rendered = builder.build().styled('diff.code')

    if (styles := _LINE_STYLES.get(kind)) is None:
        return rendered

    line_style, intraline_style = styles
    rendered = rendered.styled(line_style)

    offset = len(gutter)
    for start, end in intraline:
        start = min(max(start, 0), len(code))
        end = min(max(end, start), len(code))
        if end > start:
            rendered = rendered.styled(intraline_style, offset + start, offset + end)
    return rendered
