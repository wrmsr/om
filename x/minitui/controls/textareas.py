"""
The vim-powered text area: a scrolled vim window as a control.

Full width, minimum one row, growing with content up to `max_height`, then scrolling - the viewport follows the
cursor, so arbitrarily large pasted content stays motion- and search-accessible instead of being truncated away.
Lines hard-wrap at the width (cell-exact, mid-word, like vim's 'wrap' without 'linebreak') so document<->screen
position math stays trivial.

Enter semantics (per design): insert mode Enter inserts a newline (vim-pure); normal mode Enter submits; ctrl+enter
(kitty-negotiated terminals) or alt+enter (universal) submits from insert mode. Engine decorations (visual selection,
search matches) render as style tags resolved by the composition theme.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..docs.documents import Document
from ..docs.positions import Kind
from ..docs.positions import Pos
from ..events.keys import Key
from ..events.types import Event
from ..events.types import KeyEvent
from ..events.types import PasteEvent
from ..text.segments import Segment
from ..text.styles import StyleLike
from ..text.widths import char_width
from ..vim.engine import VimEngine
from ..vim.modes import Mode
from .bases import Control


##


_KEY_TOKENS: ta.Mapping[str, str] = {
    'up': '<up>',
    'down': '<down>',
    'left': '<left>',
    'right': '<right>',
    'home': '<home>',
    'end': '<end>',
    'enter': '\r',
    'escape': '\x1b',
    'backspace': '\x7f',
    'tab': '\t',
}


@dc.dataclass(frozen=True)
class _WrapRow(lang.Final):
    """One screen row of one document row: [start_col, end_col) plus its rendered cells' columns."""

    doc_row: int
    start_col: int
    end_col: int
    first: bool  # first screen row of its document row


class TextArea(Control):
    def __init__(
            self,
            doc: Document | None = None,
            *,
            max_height: int = 8,
            prompt: str = '',
            prompt_style: StyleLike = None,
            on_submit: ta.Callable[[str], None] | None = None,
            ex_handler: ta.Callable[[str], str | None] | None = None,
            start_in_normal: bool = False,
    ) -> None:
        super().__init__()

        self._engine = VimEngine(doc if doc is not None else Document(), ex_handler=ex_handler)
        self._max_height = max_height
        self._prompt = prompt
        self._prompt_style = prompt_style
        self._on_submit = on_submit

        self._top = 0  # first visible screen row of the wrapped document

        if not start_in_normal:
            self._engine.enter_insert()

    @property
    def engine(self) -> VimEngine:
        return self._engine

    @property
    def doc(self) -> Document:
        return self._engine.doc

    def clear(self) -> None:
        self.doc.set_text('')
        self._engine.set_cursor(Pos(0, 0))
        self._engine.enter_insert()
        self._top = 0

    ##
    # Wrapping

    def _text_width(self, width: int) -> int:
        return max(width - len(self._prompt), 1)

    def _wrap_rows(self, width: int) -> list[_WrapRow]:
        text_width = self._text_width(width)
        doc = self.doc
        rows: list[_WrapRow] = []
        for r in range(doc.line_count()):
            line = doc.line(r)
            start = 0
            col = 0
            budget = 0
            while col < len(line):
                w = char_width(line[col])
                if budget + w > text_width and col > start:
                    rows.append(_WrapRow(r, start, col, first=start == 0))
                    start = col
                    budget = 0
                budget += w
                col += 1
            rows.append(_WrapRow(r, start, len(line), first=start == 0))
        return rows

    def _cursor_screen_row(self, rows: ta.Sequence[_WrapRow]) -> int:
        cur = self._engine.cursor
        for i, row in enumerate(rows):
            if row.doc_row == cur.row and (row.start_col <= cur.col < row.end_col or (cur.col == row.end_col and (
                    i + 1 >= len(rows) or rows[i + 1].doc_row != cur.row))):
                return i
        return 0

    def _scroll(self, rows: ta.Sequence[_WrapRow]) -> tuple[int, int]:
        """Returns (top, height) after following the cursor."""

        height = min(max(len(rows), 1), self._max_height)
        cursor_row = self._cursor_screen_row(rows)
        top = self._top
        top = min(top, max(len(rows) - height, 0))
        if cursor_row < top:
            top = cursor_row
        elif cursor_row >= top + height:
            top = cursor_row - height + 1
        self._top = top
        return top, height

    ##
    # Decoration spans -> per-(row, col) tags

    def _row_tags(self, doc_row: int) -> list[tuple[int, int, str]]:
        """Tagged col intervals for one document row, later entries taking priority."""

        doc = self.doc
        out: list[tuple[int, int, str]] = []
        for dec in self._engine.decorations():
            span = dec.span
            if span.kind is Kind.LINEWISE:
                if span.start.row <= doc_row <= span.end.row:
                    out.append((0, len(doc.line(doc_row)), dec.tag))
                continue
            if not span.start.row <= doc_row <= span.end.row:
                continue
            a = span.start.col if doc_row == span.start.row else 0
            b = span.end.col if doc_row == span.end.row else len(doc.line(doc_row))
            if b > a:
                out.append((a, b, dec.tag))
        return out

    def _segment_row(self, row: _WrapRow, tags: ta.Sequence[tuple[int, int, str]]) -> list[Segment]:
        line = self.doc.line(row.doc_row)
        segments: list[Segment] = []

        if self._prompt:
            prefix = self._prompt if row.first and row.doc_row == 0 else ' ' * len(self._prompt)
            segments.append(Segment(prefix, self._prompt_style))

        def tag_at(col: int) -> str | None:
            found: str | None = None
            for a, b, tag in tags:
                if a <= col < b:
                    found = tag
            return found

        text = ''
        style: str | None = None
        for col in range(row.start_col, row.end_col):
            c_tag = tag_at(col)
            if text and c_tag != style:
                segments.append(Segment(text, style))
                text = ''
            style = c_tag
            text += line[col]
        if text:
            segments.append(Segment(text, style))
        return segments

    ##
    # Control interface

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        rows = self._wrap_rows(width)
        top, height = self._scroll(rows)
        visible = rows[top: top + height]
        return [self._segment_row(row, self._row_tags(row.doc_row)) for row in visible] or [[]]

    def cursor(self, width: int) -> tuple[int, int] | None:
        rows = self._wrap_rows(width)
        top, height = self._scroll(rows)
        cursor_row = self._cursor_screen_row(rows)
        if not top <= cursor_row < top + height:
            return None
        row = rows[cursor_row]
        cur = self._engine.cursor
        line = self.doc.line(row.doc_row)
        x = len(self._prompt) + sum(char_width(c) for c in line[row.start_col: min(cur.col, row.end_col)])
        return (x, cursor_row - top)

    def _submit(self) -> None:
        text = self.doc.text()
        if text.strip() and self._on_submit is not None:
            self._on_submit(text)
        self.clear()

    def handle_event(self, event: Event) -> bool:  # noqa: C901
        engine = self._engine

        if isinstance(event, PasteEvent):
            if engine.mode in (Mode.NORMAL, Mode.INSERT):
                engine.insert_text(event.text)
                return True
            return False

        if not isinstance(event, KeyEvent):
            return False

        key = event.key

        # Submit semantics.
        if key.base == 'enter':
            if key.ctrl or key.alt:
                self._submit()
                return True
            if engine.mode is Mode.NORMAL:
                self._submit()
                return True
            engine.feed('\r')
            return True

        if key == Key('r', ctrl=True):
            if engine.mode is Mode.NORMAL:
                engine.redo()
                return True
            return False

        if key.ctrl or key.super_:
            return False  # other chords are the app's business

        if (token := _KEY_TOKENS.get(key.base)) is not None:
            engine.feed(token)
            return True

        if key.alt:
            return False

        if event.text is not None:
            engine.feed(event.text)
            return True

        return False
