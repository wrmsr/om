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
"""The split layout: old and new side by side, each half aligned to the other on their shared context."""
import itertools
import typing as ta

from .... import dataclasses as dc
from .... import lang
from ... import diffs
from ... import styled as st
from .highlighting import HighlightedLines
from .layouts import DiffFileLines
from .layouts import DiffHunkLayout
from .layouts import intraline_ranges
from .layouts import render_code_line
from .options import DiffStyledDocOptions


##


@dc.dataclass(frozen=True)
class _SideLine(lang.Final):
    number: int
    text: str
    changed: bool


@dc.dataclass(frozen=True)
class _AlignedRow(lang.Final):
    source: _SideLine | None
    target: _SideLine | None
    intraline: bool = False


def _aligned_hunk_rows(hunk: diffs.Hunk, tab_size: int) -> list[_AlignedRow]:
    source: list[_SideLine] = []
    target: list[_SideLine] = []
    contexts: list[tuple[int, int]] = []
    source_number = hunk.old_start
    target_number = hunk.new_start

    for line in hunk.lines:
        text = line.text.expandtabs(tab_size)
        if line.kind is diffs.HunkLineKind.CONTEXT:
            source.append(_SideLine(source_number, text, False))
            target.append(_SideLine(target_number, text, False))
            contexts.append((source_number, target_number))
            source_number += 1
            target_number += 1
        elif line.kind is diffs.HunkLineKind.REMOVE:
            source.append(_SideLine(source_number, text, True))
            source_number += 1
        elif line.kind is diffs.HunkLineKind.ADD:
            target.append(_SideLine(target_number, text, True))
            target_number += 1
        else:
            raise AssertionError(line.kind)

    source_padding: dict[int, int] = {}
    target_padding: dict[int, int] = {}
    first_source, first_target = contexts[0] if contexts else (0, 0)
    current_delta = first_source - first_target
    for source_number, target_number in contexts:
        delta = source_number - target_number
        change = current_delta - delta
        if change > 0:
            source_padding[source_number] = abs(change)
        elif change < 0:
            target_padding[target_number] = abs(change)
        current_delta = delta

    def padded(lines: ta.Sequence[_SideLine], padding: ta.Mapping[int, int]) -> list[_SideLine]:
        out: list[_SideLine] = []
        for line in lines:
            out.extend([_SideLine(0, '', False)] * padding.get(line.number, 0))
            out.append(line)
        return out

    padded_source = padded(source, source_padding)
    padded_target = padded(target, target_padding)

    def streak_lengths(lines: ta.Sequence[_SideLine | None]) -> dict[int, int]:
        lengths: dict[int, int] = {}
        start = 0
        while start < len(lines):
            start_line = lines[start]
            if start_line is None or not start_line.changed:
                start += 1
                continue
            end = start + 1
            while end < len(lines):
                end_line = lines[end]
                if end_line is None or not end_line.changed:
                    break
                end += 1
            for index in range(start, end):
                lengths[index] = end - start
            start = end
        return lengths

    source_streaks = streak_lengths(padded_source)
    target_streaks = streak_lengths(padded_target)
    rows: list[_AlignedRow] = []
    for index, (source_line, target_line) in enumerate(itertools.zip_longest(padded_source, padded_target)):
        rows.append(_AlignedRow(
            source_line,
            target_line,
            intraline=(
                source_line is not None and
                target_line is not None and
                source_line.changed and
                target_line.changed and
                source_streaks.get(index) == target_streaks.get(index)
            ),
        ))
    return rows


##


class SplitDiffHunkLayout(DiffHunkLayout):
    def __init__(self, options: DiffStyledDocOptions) -> None:
        super().__init__()

        self._options = options

    def _render_side(
            self,
            line: _SideLine | None,
            highlighted: HighlightedLines,
            *,
            width: int,
            gutter_width: int,
            kind: diffs.HunkLineKind,
            ranges: ta.Sequence[tuple[int, int]],
    ) -> st.StyledText:
        if line is None:
            return st.StyledText.assemble((' ' * width, 'diff.padding'))
        if not line.number:
            return st.StyledText.assemble(('╲' * width, 'diff.padding'))

        return render_code_line(
            highlighted.get(line.number, st.StyledText(line.text)),
            st.StyledText.assemble((f'{line.number:>{gutter_width - 1}} ', 'diff.gutter')),
            width=width,
            tab_size=self._options.tab_size,
            kind=kind if line.changed else diffs.HunkLineKind.CONTEXT,
            intraline=ranges,
        )

    def render_hunk(self, hunk: diffs.Hunk, lines: DiffFileLines) -> ta.Sequence[st.StyledText]:
        source_width = self._options.width // 2
        target_width = self._options.width - source_width
        source_gutter = len(str(lines.source_max)) + 3
        target_gutter = len(str(lines.target_max)) + 3

        rows: list[st.StyledText] = []
        for row in _aligned_hunk_rows(hunk, self._options.tab_size):
            removed_ranges: ta.Sequence[tuple[int, int]] = ()
            added_ranges: ta.Sequence[tuple[int, int]] = ()
            if row.intraline and row.source is not None and row.target is not None:
                removed_ranges, added_ranges = intraline_ranges(row.source.text, row.target.text)

            rows.append(st.StyledText.of(
                self._render_side(
                    row.source,
                    lines.source,
                    width=source_width,
                    gutter_width=source_gutter,
                    kind=diffs.HunkLineKind.REMOVE,
                    ranges=removed_ranges,
                ),
                self._render_side(
                    row.target,
                    lines.target,
                    width=target_width,
                    gutter_width=target_gutter,
                    kind=diffs.HunkLineKind.ADD,
                    ranges=added_ranges,
                ),
            ))
        return rows
