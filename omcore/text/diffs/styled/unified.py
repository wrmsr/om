"""
The unified layout: one column, every line given the full width. Within each change the old lines come first and then
the new, so a change reads as a block of removals over a block of additions however the patch interleaved them.
"""
import typing as ta

from ... import diffs
from ... import styled as st
from .layouts import DiffFileLines
from .layouts import DiffHunkLayout
from .layouts import intraline_ranges
from .layouts import render_code_line
from .options import DiffStyledDocOptions


##


_MARKERS: ta.Mapping[diffs.HunkLineKind, tuple[str, str | None]] = {
    diffs.HunkLineKind.CONTEXT: (' ', None),
    diffs.HunkLineKind.REMOVE: ('-', 'diff.marker.remove'),
    diffs.HunkLineKind.ADD: ('+', 'diff.marker.add'),
}


class UnifiedDiffHunkLayout(DiffHunkLayout):
    def __init__(self, options: DiffStyledDocOptions) -> None:
        super().__init__()

        self._options = options

    def _render_line(
            self,
            code: st.StyledText,
            lines: DiffFileLines,
            *,
            kind: diffs.HunkLineKind,
            source_number: int | None,
            target_number: int | None,
            intraline: ta.Sequence[tuple[int, int]] = (),
    ) -> st.StyledText:
        # Each line is numbered on the sides it is on: a removal only on the old, an addition only on the new.
        source = f'{source_number if source_number is not None else "":>{len(str(lines.source_max))}}'
        target = f'{target_number if target_number is not None else "":>{len(str(lines.target_max))}}'
        marker, marker_style = _MARKERS[kind]
        gutter = st.StyledText.assemble(
            (f' {source} {target} ', 'diff.gutter'),
            (marker, marker_style),
            (' ', None),
        )

        return render_code_line(
            code,
            gutter,
            width=self._options.width,
            tab_size=self._options.tab_size,
            kind=kind,
            intraline=intraline,
        )

    def render_hunk(self, hunk: diffs.Hunk, lines: DiffFileLines) -> ta.Sequence[st.StyledText]:
        rows: list[st.StyledText] = []

        # The change under way: numbered lines removed and added since the last context line.
        removed: list[tuple[int, str]] = []
        added: list[tuple[int, str]] = []

        def flush_change() -> None:
            # Lines pair up for intraline highlighting only where a change added as many lines as it removed - as the
            # split layout pairs them across its halves.
            removed_ranges: list[ta.Sequence[tuple[int, int]]] = [()] * len(removed)
            added_ranges: list[ta.Sequence[tuple[int, int]]] = [()] * len(added)
            if len(removed) == len(added):
                for i, ((_, old), (_, new)) in enumerate(zip(removed, added, strict=True)):
                    removed_ranges[i], added_ranges[i] = intraline_ranges(old, new)

            for (number, text), ranges in zip(removed, removed_ranges, strict=True):
                rows.append(self._render_line(
                    lines.source.get(number, st.StyledText(text)),
                    lines,
                    kind=diffs.HunkLineKind.REMOVE,
                    source_number=number,
                    target_number=None,
                    intraline=ranges,
                ))

            for (number, text), ranges in zip(added, added_ranges, strict=True):
                rows.append(self._render_line(
                    lines.target.get(number, st.StyledText(text)),
                    lines,
                    kind=diffs.HunkLineKind.ADD,
                    source_number=None,
                    target_number=number,
                    intraline=ranges,
                ))

            removed.clear()
            added.clear()

        source_number = hunk.old_start
        target_number = hunk.new_start
        for line in hunk.lines:
            text = line.text.expandtabs(self._options.tab_size)

            if line.kind is diffs.HunkLineKind.REMOVE:
                removed.append((source_number, text))
                source_number += 1

            elif line.kind is diffs.HunkLineKind.ADD:
                added.append((target_number, text))
                target_number += 1

            elif line.kind is diffs.HunkLineKind.CONTEXT:
                flush_change()
                rows.append(self._render_line(
                    lines.target.get(target_number, st.StyledText(text)),
                    lines,
                    kind=diffs.HunkLineKind.CONTEXT,
                    source_number=source_number,
                    target_number=target_number,
                ))
                source_number += 1
                target_number += 1

            else:
                raise TypeError(line.kind)

        flush_change()
        return rows
