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
"""Build width-aware styled documents from parsed patch sets."""
import collections.abc
import difflib
import itertools
import pathlib
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore.text import diffs
from omcore.text import styled as st
from omcore.text.widths import char_width
from omcore.text.widths import str_width

from .. import minitui as mt


##


type CodeHighlighter = ta.Callable[[str, ta.Sequence[str]], ta.Sequence[st.StyledText]]
type HighlightedLines = ta.Mapping[int, st.StyledText]


@dc.dataclass(frozen=True)
class DiffRenderOptions(lang.Final):
    width: int = 80
    tab_size: int = 4
    syntax_highlighting: bool = True

    def __post_init__(self) -> None:
        check.arg(isinstance(self.width, int) and not isinstance(self.width, bool) and self.width >= 20)
        check.arg(isinstance(self.tab_size, int) and not isinstance(self.tab_size, bool) and self.tab_size >= 1)
        check.arg(isinstance(self.syntax_highlighting, bool))


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


def simple_pluralise(word: str, number: int) -> str:
    return word if number == 1 else word + 's'


def _style(text: st.StyledTextLike, style: st.StyleLike) -> st.StyledText:
    return st.StyledText.of(text).styled(style)


def _styled_parts(*parts: tuple[st.StyledTextLike, st.StyleLike | None]) -> st.StyledText:
    builder = st.StyledTextBuilder()
    for text, style in parts:
        builder.append(text, style)
    return builder.build()


def _truncate(text: st.StyledText, width: int) -> st.StyledText:
    if width <= 0:
        return st.StyledText()

    current = 0
    end = 0
    for index, char in enumerate(text.text):
        cw = char_width(char)
        if current + cw > width:
            break
        current += cw
        end = index + 1
    return text if end == len(text) else text.slice(0, end)


def _fit(text: st.StyledTextLike, width: int, style: st.StyleLike | None = None) -> st.StyledText:
    value = _truncate(st.StyledText.of(text), width)
    pad = max(width - str_width(value.text), 0)
    builder = st.StyledTextBuilder()
    builder.append(value, style)
    if pad:
        builder.append(' ' * pad, style)
    return builder.build()


def _center(text: st.StyledTextLike, width: int) -> st.StyledText:
    value = _truncate(st.StyledText.of(text), width)
    remaining = max(width - str_width(value.text), 0)
    left = remaining // 2
    return st.StyledText.of(' ' * left, value, ' ' * (remaining - left))


def _right(text: st.StyledTextLike, width: int) -> st.StyledText:
    value = _truncate(st.StyledText.of(text), width)
    return st.StyledText.of(' ' * max(width - str_width(value.text), 0), value)


def _rule(
        title: st.StyledTextLike | None,
        *,
        width: int,
        character: str,
        style: st.StyleLike,
) -> st.StyledText:
    if title is None:
        return _style(character * width, style)

    value = _truncate(st.StyledText.of(title), max(width - 2, 0))
    remaining = max(width - str_width(value.text) - 2, 0)
    left = remaining // 2
    return st.StyledText.of(
        _style(character * left, style),
        _style(' ', style),
        value,
        _style(' ', style),
        _style(character * (remaining - left), style),
    )


def _underline_bar(width: int, end: float) -> st.StyledText:
    end = min(max(end, 0), width)
    if end == 0:
        return _style('━' * width, 'diff.bar.removed')

    end = round(end * 2) / 2
    half_end = end - int(end) > 0
    builder = st.StyledTextBuilder()
    builder.append('━' * int(end), 'diff.bar.added')
    if half_end:
        builder.append('╸', 'diff.bar.added')
    elif end != width:
        builder.append('╺', 'diff.bar.removed')
    tail = width - int(end) - 1
    if tail > 0:
        builder.append('━' * tail, 'diff.bar.removed')
    return builder.build()


def _is_rename(patch: diffs.FilePatch) -> bool:
    kinds = {header.kind for header in patch.extended_headers}
    return diffs.ExtendedHeaderKind.RENAME_FROM in kinds and diffs.ExtendedHeaderKind.RENAME_TO in kinds


def _patch_path(patch: diffs.FilePatch) -> str:
    return patch.new_path or patch.old_path or '<unknown>'


def _source_path(patch: diffs.FilePatch) -> str:
    return patch.old_path or _patch_path(patch)


def _default_highlighter(path: str, lines: ta.Sequence[str]) -> ta.Sequence[st.StyledText]:
    info = pathlib.PurePath(path).suffix.removeprefix('.')
    if not info or (highlighter := mt.get_highlighter(info)) is None:
        return tuple(st.StyledText(line) for line in lines)

    styled: list[st.StyledText] = []
    for line, segments in zip(lines, highlighter.highlight(lines), strict=True):
        builder = st.StyledTextBuilder()
        for segment in segments:
            style = segment.style
            if isinstance(style, st.ResolvedStyle):
                style = st.StylePatch(
                    fg=style.fg if style.fg is not None else st.DEFAULT_COLOR,
                    bg=style.bg if style.bg is not None else st.DEFAULT_COLOR,
                    bold=style.bold,
                    dim=style.dim,
                    italic=style.italic,
                    underline=style.underline,
                    blink=style.blink,
                    reverse=style.reverse,
                    strike=style.strike,
                    hidden=style.hidden,
                )
            builder.append(segment.text, style)
        value = builder.build()
        check.state(value.text == line)
        styled.append(value)
    return tuple(styled)


def _reconstruct_source(target: ta.Sequence[str], patch: diffs.FilePatch, tab_size: int) -> list[str]:
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


def _intraline_ranges(source: str, target: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
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


def _indent_guides(text: st.StyledText, tab_size: int) -> st.StyledText:
    leading = len(text.text) - len(text.text.lstrip(' '))
    if leading < tab_size:
        return text

    chars = list(text.text)
    positions = range(0, leading, tab_size)
    for position in positions:
        chars[position] = '│'

    guided = st.StyledText(''.join(chars), text.spans)
    for position in range(0, leading, tab_size):
        guided = guided.styled('diff.indent', position, position + 1)
    return guided


class DiffRenderer(lang.Final):
    """Lay out a patch set as a target-neutral styled document."""

    def __init__(
            self,
            options: DiffRenderOptions | None = None,
            *,
            project_root: pathlib.Path | None = None,
            highlighter: CodeHighlighter | None = None,
    ) -> None:
        super().__init__()

        self._options = options or DiffRenderOptions()
        self._project_root = project_root
        self._highlighter = highlighter or _default_highlighter

    def render(self, patch_set: diffs.PatchSet) -> st.StyledDocument:
        if not isinstance(patch_set, diffs.PatchSet):
            raise TypeError(patch_set)

        lines: list[st.StyledText] = []
        lines.extend(self._render_patch_set_header(patch_set))
        for patch in patch_set.files:
            lines.extend(self._render_file(patch))
        lines.append(_right(_styled_parts(
            ('/', 'diff.summary.changed'),
            ('/', 'diff.summary.removed'),
            ('/', 'diff.summary.added'),
            (' diff   ', st.StylePatch(dim=True)),
        ), self._options.width))
        return st.StyledDocument(tuple(lines), trailing_newline=True)

    def _render_patch_set_header(self, patch_set: diffs.PatchSet) -> list[st.StyledText]:
        modified = sum(not patch.is_new_file and not patch.is_deleted_file for patch in patch_set.files)
        added = sum(patch.is_new_file for patch in patch_set.files)
        removed = sum(patch.is_deleted_file for patch in patch_set.files)

        lines: list[st.StyledText] = []
        for count, word, style in (
                (modified, 'changed', 'diff.summary.changed'),
                (added, 'added', 'diff.summary.added'),
                (removed, 'removed', 'diff.summary.removed'),
        ):
            if count:
                lines.append(_center(_styled_parts(
                    (str(count), 'diff.summary.count'),
                    (f" {simple_pluralise('file', count)} {word}", style),
                ), self._options.width))

        bar_width = self._options.width // 5
        changed_lines = max(1, patch_set.added_count + patch_set.removed_count)
        bar = _underline_bar(bar_width, patch_set.added_count / changed_lines * bar_width)
        lines.append(_center(_styled_parts(
            (f'+{patch_set.added_count} ', 'diff.bar.added'),
            (bar, None),
            (f' -{patch_set.removed_count}', 'diff.bar.removed'),
        ), self._options.width))
        lines.append(st.StyledText())
        return lines

    def _render_file(self, patch: diffs.FilePatch) -> list[st.StyledText]:
        lines = [self._render_file_header(patch)]
        if patch.is_deleted_file:
            lines.extend(self._render_message_body('File was removed', 'diff.message.removed'))
            return lines

        if patch.binary:
            size = self._binary_size(patch)
            message = 'File is binary' if size is None else f'File is binary · {size} bytes'
            lines.extend(self._render_message_body(message, 'diff.message.binary'))
            return lines

        if _is_rename(patch) and not patch.added_count and not patch.removed_count:
            lines.extend(self._render_message_body('File was only renamed', 'diff.message.renamed'))

        source_highlighted: HighlightedLines
        target_highlighted: HighlightedLines
        if (file_lines := self._load_file_lines(patch)) is not None:
            source_lines, target_lines = file_lines
            source_highlighted = dict(enumerate(
                self._highlight(_source_path(patch), source_lines),
                start=1,
            ))
            target_highlighted = dict(enumerate(
                self._highlight(_patch_path(patch), target_lines),
                start=1,
            ))
            source_max = max(len(source_lines), *(h.old_start + h.old_count - 1 for h in patch.hunks), 1)
            target_max = max(
                len(target_lines) + bool(target_lines),
                *(h.new_start + h.new_count - 1 for h in patch.hunks),
                1,
            )
        else:
            source_highlighted, target_highlighted = self._highlight_patch_lines(patch)
            source_max = max((1, *(h.old_start + h.old_count - 1 for h in patch.hunks)))
            target_max = max((1, *(h.new_start + h.new_count - 1 for h in patch.hunks)))

        for hunk in patch.hunks:
            lines.extend(self._render_hunk(
                hunk,
                source_highlighted,
                target_highlighted,
                source_max=source_max,
                target_max=target_max,
            ))
        lines.append(_rule(None, width=self._options.width, character='▔', style='diff.border'))
        return lines

    def _render_file_header(self, patch: diffs.FilePatch) -> st.StyledText:
        parts: list[tuple[st.StyledTextLike, st.StyleLike | None]] = []
        if _is_rename(patch):
            parts.extend([
                (pathlib.PurePath(_source_path(patch)).name, 'diff.header.old-path'),
                (' → ', None),
            ])
        elif patch.is_new_file:
            parts.append(('Added ', 'diff.header.added'))
        parts.extend([
            (_patch_path(patch), 'diff.header.path'),
            (' (', None),
            (str(patch.added_count), 'diff.header.additions'),
            (' additions, ', None),
            (str(patch.removed_count), 'diff.header.removals'),
            (' removals)', None),
        ])
        return _rule(
            _styled_parts(*parts),
            width=self._options.width,
            character='▁',
            style='diff.border',
        )

    def _render_message_body(self, message: str, style: st.StyleLike) -> list[st.StyledText]:
        return [
            _rule(None, width=self._options.width, character='╲', style='diff.hatched'),
            _rule(_style(message, style), width=self._options.width, character='╲', style='diff.hatched'),
            _rule(None, width=self._options.width, character='╲', style='diff.hatched'),
            _rule(None, width=self._options.width, character='▔', style='diff.border'),
        ]

    def _binary_size(self, patch: diffs.FilePatch) -> int | None:
        if self._project_root is not None:
            try:
                return (self._project_root / _patch_path(patch)).stat().st_size
            except OSError:
                pass
        if patch.git_binary_patch is not None:
            return sum(record.size for record in patch.git_binary_patch.records)
        return None

    def _load_file_lines(self, patch: diffs.FilePatch) -> tuple[list[str], list[str]] | None:
        if self._project_root is not None:
            try:
                target = (self._project_root / _patch_path(patch)).read_text().splitlines()
            except (OSError, UnicodeError):
                pass
            else:
                target = [line.expandtabs(self._options.tab_size) for line in target]
                return _reconstruct_source(target, patch, self._options.tab_size), target
        return None

    def _highlight_patch_lines(self, patch: diffs.FilePatch) -> tuple[HighlightedLines, HighlightedLines]:
        source_highlighted: dict[int, st.StyledText] = {}
        target_highlighted: dict[int, st.StyledText] = {}
        for hunk in patch.hunks:
            rows = _aligned_hunk_rows(hunk, self._options.tab_size)
            for side, path, destination in (
                    ('source', _source_path(patch), source_highlighted),
                    ('target', _patch_path(patch), target_highlighted),
            ):
                numbered: list[tuple[int, str]] = []
                seen: set[int] = set()
                for row in rows:
                    line = getattr(row, side)
                    if line is not None and line.number and line.number not in seen:
                        numbered.append((line.number, line.text))
                        seen.add(line.number)
                highlighted = self._highlight(path, [text for _, text in numbered])
                destination.update(
                    (number, value)
                    for (number, _), value in zip(numbered, highlighted, strict=True)
                )
        return source_highlighted, target_highlighted

    def _highlight(self, path: str, lines: ta.Sequence[str]) -> tuple[st.StyledText, ...]:
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

    def _render_hunk(
            self,
            hunk: diffs.Hunk,
            source_highlighted: HighlightedLines,
            target_highlighted: HighlightedLines,
            *,
            source_max: int,
            target_max: int,
    ) -> list[st.StyledText]:
        title = _styled_parts(
            ('@@ ', 'diff.hunk.marker'),
            (f'-{hunk.old_start},{hunk.old_count}', 'diff.hunk.remove'),
            (' ', None),
            (f'+{hunk.new_start},{hunk.new_count}', 'diff.hunk.add'),
            (f" @@ {hunk.section or ''}", 'diff.hunk.section'),
        )
        lines = [_rule(title, width=self._options.width, character='╲', style='diff.hunk')]

        source_width = self._options.width // 2
        target_width = self._options.width - source_width
        source_gutter = len(str(source_max)) + 3
        target_gutter = len(str(target_max)) + 3

        for row in _aligned_hunk_rows(hunk, self._options.tab_size):
            removed_ranges: collections.abc.Sequence[tuple[int, int]] = ()
            added_ranges: collections.abc.Sequence[tuple[int, int]] = ()
            if row.intraline and row.source is not None and row.target is not None:
                removed_ranges, added_ranges = _intraline_ranges(row.source.text, row.target.text)

            lines.append(st.StyledText.of(
                self._render_side(
                    row.source,
                    source_highlighted,
                    width=source_width,
                    gutter_width=source_gutter,
                    ranges=removed_ranges,
                    intraline_style='diff.intraline.remove',
                ),
                self._render_side(
                    row.target,
                    target_highlighted,
                    width=target_width,
                    gutter_width=target_gutter,
                    ranges=added_ranges,
                    intraline_style='diff.intraline.add',
                ),
            ))
        return lines

    def _render_side(
            self,
            line: _SideLine | None,
            highlighted: HighlightedLines,
            *,
            width: int,
            gutter_width: int,
            ranges: collections.abc.Sequence[tuple[int, int]],
            intraline_style: str,
    ) -> st.StyledText:
        if line is None:
            return _style(' ' * width, 'diff.padding')
        if not line.number:
            return _style('╲' * width, 'diff.padding')

        code = highlighted.get(line.number, st.StyledText(line.text))
        code = _indent_guides(code, self._options.tab_size)
        content_width = max(width - gutter_width, 0)
        code = _truncate(code, content_width)

        builder = st.StyledTextBuilder()
        builder.append(f'{line.number:>{gutter_width - 1}} ', 'diff.gutter')
        builder.append(code)
        builder.append(' ' * max(content_width - str_width(code.text), 0))
        rendered = builder.build().styled('diff.code')
        if line.changed:
            rendered = rendered.styled('diff.line.remove' if intraline_style.endswith('remove') else 'diff.line.add')

        offset = gutter_width
        for start, end in ranges:
            start = min(max(start, 0), len(code))
            end = min(max(end, start), len(code))
            if end > start:
                rendered = rendered.styled(intraline_style, offset + start, offset + end)
        return rendered


def render_diff_document(
        patch_set: diffs.PatchSet,
        project_root: pathlib.Path | None = None,
        *,
        width: int = 80,
        tab_size: int = 4,
        syntax_highlighting: bool = True,
) -> st.StyledDocument:
    """Convenience entry point for producing a target-neutral diff document."""

    return DiffRenderer(
        DiffRenderOptions(
            width=width,
            tab_size=tab_size,
            syntax_highlighting=syntax_highlighting,
        ),
        project_root=project_root,
    ).render(patch_set)
