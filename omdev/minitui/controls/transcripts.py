"""
The transcript: an app-retained record of what was committed, and the control that scrolls it - browse mode's model and
view.

Committed content is dead scrollback by design; the terminal owns it and minitui never looks at it again. An app that
wants to look back keeps its own record: `Transcript` is an append-only log of blocks - each commit's lines exactly as
displayed, plus an opaque tag saying what the block was (a message, a card, a command echo) - with row-to-block lookup.
`TranscriptView` is a scrolled window over it: the fullscreen browse view. Retained cells render straight back out as
segments carrying their already-resolved styles (the theme passes those through), clipped to the current width, and a
set of live controls - the streaming tail, warm cards - is appended as the document's trailing block so it scrolls along
with history. Follow mode keeps the window pinned to the bottom until the user scrolls up, and re-pins when they scroll
back down.

Clicks resolve to a `TranscriptHit` - the document row, the block and its tag, or the live control under the row. That
is the anchor a context menu would open from once overlay compositing exists in the controls layer; this view only
reports the hit (via `on_click`) and forwards clicks on live controls to them.
"""
import bisect
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..events.keys import Key
from ..events.types import Event
from ..events.types import KeyEvent
from ..events.types import MouseEvent
from ..events.types import MouseEventKind
from ..screens.cells import Line
from ..text.segments import Segment
from .base import Control


##


@dc.dataclass(frozen=True)
class TranscriptBlock(lang.Final):
    lines: tuple[Line, ...]
    tag: ta.Any = None  # opaque app identity: what this block was


class Transcript:
    """
    An append-only record of committed lines, in blocks. Optionally bounded in rows, in which case whole blocks drop off
    the front once the bound is exceeded (the newest block always stays).
    """

    def __init__(
            self,
            *,
            max_rows: int | None = None,
    ) -> None:
        super().__init__()

        self._max_rows = max_rows

        self._blocks: list[TranscriptBlock] = []
        self._ends: list[int] = []  # cumulative: the document row after each block

    @property
    def blocks(self) -> ta.Sequence[TranscriptBlock]:
        return self._blocks

    @property
    def height(self) -> int:
        return self._ends[-1] if self._ends else 0

    def record(self, lines: ta.Sequence[Line], tag: ta.Any = None) -> TranscriptBlock:
        block = TranscriptBlock(tuple(lines), tag)
        self._ends.append(self.height + len(block.lines))
        self._blocks.append(block)
        if self._max_rows is not None:
            self._trim(self._max_rows)
        return block

    def _trim(self, max_rows: int) -> None:
        drop = 0
        while drop < len(self._blocks) - 1:
            removed = self._ends[drop - 1] if drop else 0
            if self._ends[-1] - removed <= max_rows:
                break
            drop += 1
        if drop:
            removed = self._ends[drop - 1]
            del self._blocks[:drop]
            self._ends = [end - removed for end in self._ends[drop:]]

    def block_at(self, row: int) -> tuple[TranscriptBlock, int] | None:
        """The block containing document row `row` and the row's index within it, or None when out of range."""

        if not 0 <= row < self.height:
            return None
        i = bisect.bisect_right(self._ends, row)
        start = self._ends[i - 1] if i else 0
        return self._blocks[i], row - start

    def lines(self, start: int, stop: int) -> list[Line]:
        """Document rows [start, stop), clamped to the record."""

        start = max(start, 0)
        stop = min(stop, self.height)
        out: list[Line] = []
        if start >= stop:
            return out
        i = bisect.bisect_right(self._ends, start)
        row = self._ends[i - 1] if i else 0
        while i < len(self._blocks) and row < stop:
            block = self._blocks[i]
            out.extend(block.lines[max(start - row, 0):stop - row])
            row += len(block.lines)
            i += 1
        return out


##


@dc.dataclass(frozen=True)
class TranscriptHit(lang.Final):
    """
    What lies under a row of the view: a transcript block (and the row's index within it), or a trailing live control
    (and the row's index within its rendering).
    """

    row: int  # document row

    _: dc.KW_ONLY

    block: TranscriptBlock | None = None
    block_row: int = 0
    control: Control | None = None
    control_row: int = 0


def _line_segments(line: Line, width: int) -> list[Segment]:
    """
    A retained line back to segments: adjacent same-style cells merge, and the row is clipped to `width` columns (a wide
    character straddling the edge is dropped whole - autowrap is off, so overflow would pin and garble).
    """

    out: list[Segment] = []
    text: list[str] = []
    style = None
    used = 0
    for cell in line.cells:
        if used + cell.width > width:
            break
        used += cell.width
        if text and cell.style != style:
            out.append(Segment(''.join(text), style))
            text = []
        style = cell.style
        text.append(cell.text)
    if text:
        out.append(Segment(''.join(text), style))
    return out


class TranscriptView(Control):
    """
    A scrolled window of `height` rows over a transcript plus trailing live controls. Renders exactly `height` rows
    (padding below the document's end), so whatever is stacked after it stays put.
    """

    def __init__(
            self,
            transcript: Transcript,
            *,
            height: int = 0,
            scroll_rows: int = 3,
            on_click: ta.Callable[[TranscriptHit, MouseEvent], None] | None = None,
    ) -> None:
        super().__init__()

        self._transcript = transcript
        self._height = max(height, 0)
        self._scroll_rows = scroll_rows
        self._on_click = on_click

        self._trailing: tuple[Control, ...] = ()
        self._offset = 0
        self._follow = True

        # Geometry of the last render: the scrolling math and hit-testing work from it.
        self._last_total = 0
        self._last_offset = 0
        self._last_trailing: tuple[tuple[Control, int, int], ...] = ()  # (control, first row, end row), document rows

        self._key_actions: ta.Mapping[Key, ta.Callable[[], None]] = {
            Key('up'): lambda: self.scroll_by(-1),
            Key('k'): lambda: self.scroll_by(-1),
            Key('down'): lambda: self.scroll_by(1),
            Key('j'): lambda: self.scroll_by(1),
            Key('pageup'): self.page_up,
            Key('b', ctrl=True): self.page_up,
            Key('pagedown'): self.page_down,
            Key('f', ctrl=True): self.page_down,
            Key('space'): self.page_down,
            Key('home'): self.scroll_to_top,
            Key('g'): self.scroll_to_top,
            Key('end'): self.scroll_to_bottom,
            Key('G'): self.scroll_to_bottom,
        }

    @property
    def transcript(self) -> Transcript:
        return self._transcript

    @property
    def height(self) -> int:
        return self._height

    @property
    def offset(self) -> int:
        """The document row shown at the top of the view, as of the last render."""

        return self._last_offset

    @property
    def total(self) -> int:
        """The document's row count - transcript plus trailing controls - as of the last render."""

        return self._last_total

    @property
    def follow(self) -> bool:
        """Pinned to the bottom: new content keeps the end in view."""

        return self._follow

    def set_height(self, height: int) -> None:
        self._height = max(height, 0)

    def set_trailing(self, controls: ta.Iterable[Control]) -> None:
        """The live controls rendered after the transcript as the document's last block, top to bottom."""

        self._trailing = tuple(controls)

    ##
    # Scrolling

    def _max_offset(self) -> int:
        return max(self._last_total - self._height, 0)

    def scroll_by(self, rows: int) -> None:
        """
        Positive is toward the present, negative into history. The bottom re-enters follow mode; leaving it ends it.
        """

        max_offset = self._max_offset()
        target = min(max(self._last_offset + rows, 0), max_offset)
        self._offset = target
        self._follow = target >= max_offset

    def page_up(self) -> None:
        self.scroll_by(-max(self._height - 1, 1))

    def page_down(self) -> None:
        self.scroll_by(max(self._height - 1, 1))

    def scroll_to_top(self) -> None:
        self._offset = 0
        self._follow = self._max_offset() == 0

    def scroll_to_bottom(self) -> None:
        self._follow = True

    ##
    # Rendering

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        doc = self._transcript.height

        trailing_rows: list[ta.Sequence[Segment]] = []
        spans: list[tuple[Control, int, int]] = []
        row = doc
        for control in self._trailing:
            rows = control.render(width)
            if rows:
                spans.append((control, row, row + len(rows)))
                trailing_rows.extend(rows)
                row += len(rows)
        total = row

        self._last_total = total
        self._last_trailing = tuple(spans)
        max_offset = self._max_offset()
        offset = max_offset if self._follow else min(self._offset, max_offset)
        self._offset = offset
        self._last_offset = offset

        stop = offset + self._height
        out: list[ta.Sequence[Segment]] = [
            _line_segments(line, width)
            for line in self._transcript.lines(offset, min(stop, doc))
        ]
        if stop > doc:
            out.extend(trailing_rows[max(offset - doc, 0):stop - doc])
        while len(out) < self._height:
            out.append([])
        return out

    ##
    # Events (the app routes; local y arrives in the event)

    def hit(self, y: int) -> TranscriptHit | None:
        """What is under view row `y` (0 is the top row shown), or None for padding below the document."""

        row = self._last_offset + y
        if y < 0 or row >= self._last_total:
            return None
        if (found := self._transcript.block_at(row)) is not None:
            block, block_row = found
            return TranscriptHit(row, block=block, block_row=block_row)
        for control, start, end in self._last_trailing:
            if start <= row < end:
                return TranscriptHit(row, control=control, control_row=row - start)
        return None

    def handle_event(self, event: Event) -> bool:
        if isinstance(event, MouseEvent):
            if event.kind is MouseEventKind.SCROLL_UP:
                self.scroll_by(-self._scroll_rows)
                return True
            if event.kind is MouseEventKind.SCROLL_DOWN:
                self.scroll_by(self._scroll_rows)
                return True
            if event.kind is MouseEventKind.DOWN:
                if (hit := self.hit(event.y)) is None:
                    return False
                if (control := hit.control) is not None:
                    return control.handle_event(dc.replace(event, y=hit.control_row))
                if (on_click := self._on_click) is not None:
                    on_click(hit, event)
                    return True
            return False

        if isinstance(event, KeyEvent):
            if (action := self._key_actions.get(event.key)) is not None:
                action()
                return True
            return False

        return False
