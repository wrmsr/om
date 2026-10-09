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
"""
Lays out a patch set as a styled document: the frame every layout shares - the summary, each file's header and the
special bodies of removed, binary and renamed files, each hunk's header - around hunk lines laid out by one layout.
"""
import pathlib

from .... import lang
from ... import diffs
from ... import styled as st
from ...styled import grid
from .highlighting import CodeHighlighter
from .highlighting import DiffCodeHighlighter
from .highlighting import HighlightedLines
from .highlighting import hunk_side_lines
from .highlighting import reconstruct_source
from .layouts import DiffFileLines
from .layouts import DiffHunkLayout
from .options import DiffLayout
from .options import DiffStyledDocOptions
from .sources import DiffFileSource
from .sources import texts_match_hunks
from .split import SplitDiffHunkLayout
from .unified import UnifiedDiffHunkLayout


##


_ELLIPSIS = '\N{HORIZONTAL ELLIPSIS}'


def simple_pluralise(word: str, number: int) -> str:
    return word if number == 1 else word + 's'


def _underline_bar(width: int, end: float) -> st.StyledText:
    end = min(max(end, 0), width)
    if end == 0:
        return st.StyledText.assemble(('━' * width, 'diff.bar.removed'))

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


##


def build_diff_hunk_layout(options: DiffStyledDocOptions) -> DiffHunkLayout:
    if (layout := options.resolved_layout) == 'split':
        return SplitDiffHunkLayout(options)
    elif layout == 'unified':
        return UnifiedDiffHunkLayout(options)
    else:
        raise ValueError(layout)


class DiffStyledDocRenderer(lang.Final):
    """Lay out a patch set as a target-neutral styled document."""

    def __init__(
            self,
            options: DiffStyledDocOptions | None = None,
            *,
            file_source: DiffFileSource | None = None,
            highlighter: CodeHighlighter | None = None,
            hunk_layout: DiffHunkLayout | None = None,
    ) -> None:
        """A given `hunk_layout` is used as is, whatever the options' layout."""

        super().__init__()

        self._options = options or DiffStyledDocOptions()
        self._file_source = file_source
        self._code_highlighter = DiffCodeHighlighter(self._options, highlighter=highlighter)
        self._hunk_layout = hunk_layout if hunk_layout is not None else build_diff_hunk_layout(self._options)

    def render(self, patch_set: diffs.PatchSet) -> st.StyledDocument:
        if not isinstance(patch_set, diffs.PatchSet):
            raise TypeError(patch_set)

        lines: list[st.StyledText] = []
        lines.extend(self._render_patch_set_header(patch_set))
        for patch in patch_set.files:
            lines.extend(self._render_file(patch))
        lines.append(grid.fit(st.StyledText.assemble(
            ('/', 'diff.summary.changed'),
            ('/', 'diff.summary.removed'),
            ('/', 'diff.summary.added'),
            (' diff   ', st.StylePatch(dim=True)),
        ), self._options.width, align='right'))
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
                lines.append(grid.fit(st.StyledText.assemble(
                    (str(count), 'diff.summary.count'),
                    (f" {simple_pluralise('file', count)} {word}", style),
                ), self._options.width, align='center'))

        bar_width = self._options.width // 5
        changed_lines = max(1, patch_set.added_count + patch_set.removed_count)
        bar = _underline_bar(bar_width, patch_set.added_count / changed_lines * bar_width)
        lines.append(grid.fit(st.StyledText.assemble(
            (f'+{patch_set.added_count} ', 'diff.bar.added'),
            (bar, None),
            (f' -{patch_set.removed_count}', 'diff.bar.removed'),
        ), self._options.width, align='center'))
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

        file_lines = self._file_lines(patch)
        for hunk in patch.hunks:
            lines.append(self._render_hunk_header(hunk))
            lines.extend(self._hunk_layout.render_hunk(hunk, file_lines))
        lines.append(grid.rule(self._options.width, character='▔', style='diff.border'))
        return lines

    def _file_lines(self, patch: diffs.FilePatch) -> DiffFileLines:
        source_highlighted: HighlightedLines
        target_highlighted: HighlightedLines
        if (full_texts := self._full_texts(patch)) is not None:
            source_lines, target_lines = full_texts
            source_highlighted = dict(enumerate(
                self._code_highlighter.highlight(_source_path(patch), source_lines),
                start=1,
            ))
            target_highlighted = dict(enumerate(
                self._code_highlighter.highlight(_patch_path(patch), target_lines),
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

        return DiffFileLines(
            source=source_highlighted,
            target=target_highlighted,
            source_max=source_max,
            target_max=target_max,
        )

    def _render_file_header(self, patch: diffs.FilePatch) -> st.StyledText:
        head: list[tuple[st.StyledTextLike, st.StyleLike | None]] = []
        if _is_rename(patch):
            head.extend([
                (pathlib.PurePath(_source_path(patch)).name, 'diff.header.old-path'),
                (' → ', None),
            ])
        elif patch.is_new_file:
            head.append(('Added ', 'diff.header.added'))
        head_text = grid.show_controls(st.StyledText.assemble(*head))

        tail_text = st.StyledText.assemble(
            (' (', None),
            (str(patch.added_count), 'diff.header.additions'),
            (' additions, ', None),
            (str(patch.removed_count), 'diff.header.removals'),
            (' removals)', None),
        )

        # A path too long for the header gives up its start rather than the counts after it, as its end names the file.
        # The rule sets the title off by a space on each side.
        path_width = self._options.width - 2 - grid.cell_width(head_text) - grid.cell_width(tail_text)
        path_text = grid.truncate_left(grid.show_controls(_patch_path(patch)), path_width, ellipsis=_ELLIPSIS)

        return grid.rule(
            self._options.width,
            title=st.StyledText.assemble(head_text, (path_text, 'diff.header.path'), tail_text),
            character='▁',
            style='diff.border',
        )

    def _render_message_body(self, message: str, style: st.StyleLike) -> list[st.StyledText]:
        return [
            grid.rule(self._options.width, character='╲', style='diff.hatched'),
            grid.rule(
                self._options.width,
                title=st.StyledText.assemble((message, style)),
                character='╲',
                style='diff.hatched',
            ),
            grid.rule(self._options.width, character='╲', style='diff.hatched'),
            grid.rule(self._options.width, character='▔', style='diff.border'),
        ]

    def _binary_size(self, patch: diffs.FilePatch) -> int | None:
        if self._file_source is not None and (size := self._file_source.get_target_size(patch)) is not None:
            return size
        if patch.git_binary_patch is not None:
            return sum(record.size for record in patch.git_binary_patch.records)
        return None

    def _full_texts(self, patch: diffs.FilePatch) -> tuple[list[str], list[str]] | None:
        """
        The file's full texts on both sides, where the source has them and they agree with the patch. Otherwise None,
        and the hunks are drawn from the patch alone - every row is drawn by its line number from these, so text of some
        other version would put the wrong code on every row.
        """

        if self._file_source is None:
            return None

        # A file too big to highlight whole is not even read, where the source can tell its size without reading it.
        limits = self._options.context_limits
        if (size := self._file_source.get_target_size(patch)) is not None and not limits.admits_size(size):
            return None

        if (texts := self._file_source.get_texts(patch)) is None:
            return None
        if not all(limits.admits(text) for text in (texts.source, texts.target) if text is not None):
            return None

        # Only the target stands alone: a source text not given is rebuilt from it and the hunks.
        if (target := texts.target) is None or not texts_match_hunks(patch, target, side='target'):
            return None
        if (source := texts.source) is not None and not texts_match_hunks(patch, source, side='source'):
            return None

        tab_size = self._options.tab_size
        target_lines = [line.expandtabs(tab_size) for line in target]
        if source is not None:
            source_lines = [line.expandtabs(tab_size) for line in source]
        else:
            source_lines = reconstruct_source(target_lines, patch, tab_size)
        return source_lines, target_lines

    def _highlight_patch_lines(self, patch: diffs.FilePatch) -> tuple[HighlightedLines, HighlightedLines]:
        # Without the file there is nothing between hunks to give context, so each hunk is highlighted on its own.
        source_highlighted: dict[int, st.StyledText] = {}
        target_highlighted: dict[int, st.StyledText] = {}
        for hunk in patch.hunks:
            for path, numbered, destination in zip(
                    (_source_path(patch), _patch_path(patch)),
                    hunk_side_lines(hunk, self._options.tab_size),
                    (source_highlighted, target_highlighted),
                    strict=True,
            ):
                highlighted = self._code_highlighter.highlight(path, [text for _, text in numbered])
                destination.update(
                    (number, value)
                    for (number, _), value in zip(numbered, highlighted, strict=True)
                )
        return source_highlighted, target_highlighted

    def _render_hunk_header(self, hunk: diffs.Hunk) -> st.StyledText:
        title = st.StyledText.assemble(
            ('@@ ', 'diff.hunk.marker'),
            (f'-{hunk.old_start},{hunk.old_count}', 'diff.hunk.remove'),
            (' ', None),
            (f'+{hunk.new_start},{hunk.new_count}', 'diff.hunk.add'),
            (f" @@ {hunk.section or ''}", 'diff.hunk.section'),
        )
        # The section is a line of the file, so it may hold anything the file does.
        return grid.rule(self._options.width, title=grid.show_controls(title), character='╲', style='diff.hunk')


def render_diff_styled_doc(
        patch_set: diffs.PatchSet,
        file_source: DiffFileSource | None = None,
        *,
        width: int = 80,
        tab_size: int = 4,
        syntax_highlighting: bool = True,
        layout: DiffLayout = 'auto',
) -> st.StyledDocument:
    """Convenience entry point for producing a target-neutral diff document."""

    return DiffStyledDocRenderer(
        DiffStyledDocOptions(
            width=width,
            tab_size=tab_size,
            syntax_highlighting=syntax_highlighting,
            layout=layout,
        ),
        file_source=file_source,
    ).render(patch_set)
