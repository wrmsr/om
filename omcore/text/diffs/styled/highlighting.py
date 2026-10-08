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
"""Syntax highlighting of a patch's code, keyed by line number on each side."""
import pathlib
import typing as ta

from .... import check
from .... import lang
from ... import diffs
from ... import highlights as hl
from ... import styled as st
from .options import DiffStyledDocOptions


type CodeHighlighter = ta.Callable[[str, ta.Sequence[str]], ta.Sequence[st.StyledText]]
type HighlightedLines = ta.Mapping[int, st.StyledText]


##


def default_highlighter(path: str, lines: ta.Sequence[str]) -> ta.Sequence[st.StyledText]:
    info = pathlib.PurePath(path).suffix.removeprefix('.')
    if not info or (highlighter := hl.get_highlighter(info)) is None:
        return tuple(st.StyledText(line) for line in lines)

    highlighted = tuple(highlighter.highlight(lines))
    check.state(all(value.text == line for value, line in zip(highlighted, lines, strict=True)))
    return highlighted


def reconstruct_source(target: ta.Sequence[str], patch: diffs.FilePatch, tab_size: int) -> list[str]:
    source: list[str] = []
    target_index = 0
    for hunk in patch.hunks:
        hunk_target_index = max(hunk.new_start - 1, 0)
        source.extend(target[target_index:hunk_target_index])
        source.extend(
            line.text.expandtabs(tab_size)
            for line in hunk.lines
            if line.kind in (diffs.HunkLineKind.CONTEXT, diffs.HunkLineKind.REMOVE)
        )
        target_index = hunk_target_index + hunk.new_count
    source.extend(target[target_index:])
    return source


def hunk_side_lines(
        hunk: diffs.Hunk,
        tab_size: int,
) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """
    A hunk's numbered lines as each side has them: context and removals on the source, context and additions on the
    target, in order.
    """

    source: list[tuple[int, str]] = []
    target: list[tuple[int, str]] = []
    source_number = hunk.old_start
    target_number = hunk.new_start

    for line in hunk.lines:
        text = line.text.expandtabs(tab_size)
        if line.kind is not diffs.HunkLineKind.ADD:
            source.append((source_number, text))
            source_number += 1
        if line.kind is not diffs.HunkLineKind.REMOVE:
            target.append((target_number, text))
            target_number += 1

    return source, target


class DiffCodeHighlighter(lang.Final):
    """
    Highlights a run of code lines as a diff draws them: a blank line takes the indent around it, so indent guides run
    through it unbroken.
    """

    def __init__(
            self,
            options: DiffStyledDocOptions,
            *,
            highlighter: CodeHighlighter | None = None,
    ) -> None:
        super().__init__()

        self._options = options
        self._highlighter = highlighter or default_highlighter

    def highlight(self, path: str, lines: ta.Sequence[str]) -> tuple[st.StyledText, ...]:
        visual_lines = list(lines)
        previous_indent = 0
        for index, line in enumerate(visual_lines):
            if line.strip():
                previous_indent = len(line) - len(line.lstrip(' '))
                continue
            next_indent = 0
            for following in visual_lines[index + 1:]:
                if following.strip():
                    next_indent = len(following) - len(following.lstrip(' '))
                    break
            visual_lines[index] = ' ' * min(previous_indent, next_indent)

        if not self._options.syntax_highlighting:
            return tuple(st.StyledText(line) for line in visual_lines)
        highlighted = tuple(self._highlighter(path, visual_lines))
        check.state(len(highlighted) == len(visual_lines))
        check.state(all(value.text == line for value, line in zip(highlighted, visual_lines, strict=True)))
        return highlighted
