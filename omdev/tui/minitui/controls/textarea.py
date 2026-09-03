"""
The vim-powered text area: a scrolled vim window as a control.

Full width, minimum one row, growing with content up to `max_height`, then scrolling - the viewport follows the cursor,
so arbitrarily large pasted content stays motion- and search-accessible instead of being truncated away. Lines hard-wrap
at the width (cell-exact, mid-word, like vim's 'wrap' without 'linebreak') so document<->screen position math stays
trivial. With `options.number` a vim-style line number column leads each row (right-aligned, at least `numberwidth`
wide, blank on wrapped continuation rows), ahead of any prompt.

Enter semantics (per design): insert mode Enter inserts a newline (vim-pure); normal mode Enter submits; from insert
mode, ctrl+j (universal - the other newline byte), ctrl/shift+enter (extended-key terminals), or alt+enter submit.
Insert mode additionally honors the common readline/emacs chord subset (`_INSERT_CHORD_TOKENS`): ctrl+a/e/f/b/p/n
movement, alt+f/b word motion, and the ctrl+w / alt+backspace / alt+d / ctrl+k / ctrl+u kill family. Engine decorations
(visual selection, search matches) render as style tags resolved by the composition theme.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..docs.documents import Document
from ..docs.highlighting import IncrementalHighlighter
from ..docs.positions import Pos
from ..docs.positions import SpanKind
from ..events.keys import Key
from ..events.types import Event
from ..events.types import KeyEvent
from ..events.types import PasteEvent
from ..text.highlights.base import Highlighter
from ..text.segments import Segment
from ..text.styles import StyleLike
from ..text.widths import ascii_control_repr
from ..text.widths import char_width
from ..vim.engine import VimEngine
from ..vim.modes import Mode
from ..vim.options import DEFAULT_OPTIONS
from ..vim.options import VimOptions
from .base import Control


##


# The line number column's theme tag (vim's LineNr group). A view concern, unlike the engine's decoration tags.
LINENR_TAG = 'vim.linenr'


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

# Readline/emacs chords honored in INSERT mode - the most common movement + kill subset. Chords not listed still fall
# through to the app (ctrl+d, ctrl+o, ...); an app wanting ctrl+p/n for history should claim them only at the first/last
# line, arrow-style, so mid-buffer they reach the editor as line movement.
_INSERT_CHORD_TOKENS: ta.Mapping[Key, str] = {
    Key('a', ctrl=True): '<home>',
    Key('e', ctrl=True): '<end>',
    Key('b', ctrl=True): '<left>',
    Key('f', ctrl=True): '<right>',
    Key('p', ctrl=True): '<up>',
    Key('n', ctrl=True): '<down>',
    Key('b', alt=True): '<a-b>',
    Key('f', alt=True): '<a-f>',
    Key('w', ctrl=True): '<c-w>',         # delete word back (vim's own insert chord)
    Key('backspace', alt=True): '<c-w>',  # readline M-backspace, same kill
    Key('d', alt=True): '<a-d>',
    Key('k', ctrl=True): '<c-k>',
    Key('u', ctrl=True): '<c-u>',
}


def _display_char(c: str, tab_width: int) -> tuple[str, int]:
    """
    What one document character displays as: tabs become `tab_width` spaces (a fixed expansion, not true col%ts tab
    stops - identical for leading tabs, the case that matters), control chars caret notation.
    """

    if c == '\t':
        return (' ' * tab_width, tab_width)
    if (caret := ascii_control_repr(c)) is not None:
        return (caret, len(caret))
    return (c, char_width(c))


_TagInterval: ta.TypeAlias = tuple[int, int, StyleLike]  # [start_col, end_col) -> style/tag


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
            highlighter: Highlighter | None = None,
            options: VimOptions | None = None,
    ) -> None:
        super().__init__()

        self._engine = VimEngine(
            doc if doc is not None else Document(),
            ex_handler=ex_handler,
            options=options if options is not None else DEFAULT_OPTIONS,
        )
        self._max_height = max_height
        self._prompt = prompt
        self._prompt_style = prompt_style
        self._on_submit = on_submit
        self._highlighter = highlighter

        self._top = 0  # first visible screen row of the wrapped document
        self._last_width = 80  # viewport ops happen between renders; remember the geometry
        self._pending_z = False

        self._hl_version: int | None = None
        self._hl_tags: list[list[_TagInterval]] = []

        if isinstance(highlighter, IncrementalHighlighter):
            # Feed every applied edit (undo inverses included) so keystrokes cost incremental reparses.
            self.doc.add_listener(lambda doc, applied: highlighter.note_edit(applied.edit))

        if not start_in_normal:
            self._engine.enter_insert()

    @property
    def engine(self) -> VimEngine:
        return self._engine

    @property
    def max_height(self) -> int:
        return self._max_height

    def set_max_height(self, max_height: int) -> None:
        self._max_height = max(max_height, 1)

    @property
    def doc(self) -> Document:
        return self._engine.doc

    def clear(self) -> None:
        self.set_text('')

    def set_text(self, text: str) -> None:
        """Replace the whole content (history navigation, programmatic fills); cursor to end, insert mode."""

        self.doc.set_text(text)
        self._engine.enter_insert()
        self._engine.set_cursor(self.doc.end_pos())
        self._top = 0

    ##
    # Wrapping

    def _gutter_width(self) -> int:
        """Per vim: at least `numberwidth` columns, or the last line number's digits plus the separating space."""

        opts = self._engine.options
        if not opts.number:
            return 0
        return max(opts.numberwidth, len(str(self.doc.line_count())) + 1)

    def _left_width(self) -> int:
        return self._gutter_width() + len(self._prompt)

    def _text_width(self, width: int) -> int:
        return max(width - self._left_width(), 1)

    def _wrap_rows(self, width: int) -> list[_WrapRow]:
        text_width = self._text_width(width)
        doc = self.doc
        rows: list[_WrapRow] = []
        for r in range(doc.line_count()):
            line = doc.line(r)
            start = 0
            col = 0
            budget = 0
            tw = self._engine.options.tabstop
            while col < len(line):
                _, w = _display_char(line[col], tw)
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
    # Style layers: syntax base spans under engine decorations

    def _base_tags(self, doc_row: int) -> ta.Sequence[_TagInterval]:
        if self._highlighter is None:
            return ()
        if self._hl_version != self.doc.version:
            self._hl_tags = []
            for row in self._highlighter.highlight(self.doc.lines()):
                intervals: list[_TagInterval] = []
                col = 0
                for seg in row:
                    end = col + len(seg.text)
                    if seg.style is not None:
                        intervals.append((col, end, seg.style))
                    col = end
                self._hl_tags.append(intervals)
            self._hl_version = self.doc.version
        if 0 <= doc_row < len(self._hl_tags):
            return self._hl_tags[doc_row]
        return ()

    def _row_tags(self, doc_row: int) -> list[tuple[int, int, str]]:
        """Tagged col intervals for one document row, later entries taking priority."""

        doc = self.doc
        out: list[tuple[int, int, str]] = []
        for dec in self._engine.decorations():
            span = dec.span
            if span.kind is SpanKind.LINEWISE:
                if span.start.row <= doc_row <= span.end.row:
                    out.append((0, len(doc.line(doc_row)), dec.tag))
                continue
            if span.kind is SpanKind.BLOCK:
                if span.start.row <= doc_row <= span.end.row:
                    b = min(span.end.col, len(doc.line(doc_row)))
                    if b > span.start.col:
                        out.append((span.start.col, b, dec.tag))
                continue
            if not span.start.row <= doc_row <= span.end.row:
                continue
            a = span.start.col if doc_row == span.start.row else 0
            b = span.end.col if doc_row == span.end.row else len(doc.line(doc_row))
            if b > a:
                out.append((a, b, dec.tag))
        return out

    def _segment_row(self, row: _WrapRow, tags: ta.Sequence[_TagInterval]) -> list[Segment]:
        line = self.doc.line(row.doc_row)
        segments: list[Segment] = []

        if gutter := self._gutter_width():
            # Continuation rows of a wrapped line get a blank column, as vim does without 'showbreak'.
            number = f'{row.doc_row + 1:>{gutter - 1}} ' if row.first else ' ' * gutter
            segments.append(Segment(number, LINENR_TAG))

        if self._prompt:
            prefix = self._prompt if row.first and row.doc_row == 0 else ' ' * len(self._prompt)
            segments.append(Segment(prefix, self._prompt_style))

        def tag_at(col: int) -> StyleLike:
            found: StyleLike = None
            for a, b, tag in tags:
                if a <= col < b:
                    found = tag
            return found

        text = ''
        style: StyleLike = None
        for col in range(row.start_col, row.end_col):
            c_tag = tag_at(col)
            if text and c_tag != style:
                segments.append(Segment(text, style))
                text = ''
            style = c_tag
            text += _display_char(line[col], self._engine.options.tabstop)[0]
        if text:
            segments.append(Segment(text, style))

        # A tag covering the newline slot (a secondary cursor parked at end-of-line) renders as a styled space.
        if row.end_col == len(line) and (eol_tag := tag_at(len(line))) is not None:
            segments.append(Segment(' ', eol_tag))

        return segments

    ##
    # Control interface

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        self._last_width = width
        rows = self._wrap_rows(width)
        top, height = self._scroll(rows)
        visible = rows[top: top + height]
        return [
            self._segment_row(row, [*self._base_tags(row.doc_row), *self._row_tags(row.doc_row)])
            for row in visible
        ] or [[]]

    def cursor(self, width: int) -> tuple[int, int] | None:
        rows = self._wrap_rows(width)
        top, height = self._scroll(rows)
        cursor_row = self._cursor_screen_row(rows)
        if not top <= cursor_row < top + height:
            return None
        row = rows[cursor_row]
        cur = self._engine.cursor
        line = self.doc.line(row.doc_row)
        x = self._left_width() + sum(
            _display_char(c, self._engine.options.tabstop)[1]
            for c in line[row.start_col: min(cur.col, row.end_col)]
        )
        return (x, cursor_row - top)

    ##
    # Viewport operations (view concerns vim routes through the editor: scrolling lives with the window, not the engine
    # - the engine stays headless)

    def _visible_modes(self) -> bool:
        return self._engine.mode in (Mode.NORMAL, Mode.VISUAL, Mode.VISUAL_LINE, Mode.VISUAL_BLOCK)

    def _viewport(self) -> tuple[list[_WrapRow], int, int]:
        rows = self._wrap_rows(self._last_width)
        top, height = self._scroll(rows)
        return rows, top, height

    def _cursor_to_wrap_row(self, rows: ta.Sequence[_WrapRow], index: int) -> None:
        row = rows[min(max(index, 0), len(rows) - 1)]
        cur = self._engine.cursor
        col = min(max(cur.col, row.start_col), max(row.end_col - 1, row.start_col))
        self._engine.set_cursor(Pos(row.doc_row, col))

    def _scroll_rows(self, delta: int) -> None:
        """Move the view and cursor together by `delta` wrapped screen rows (the ctrl+d/u/f/b family)."""

        rows, top, height = self._viewport()
        self._cursor_to_wrap_row(rows, self._cursor_screen_row(rows) + delta)
        self._top = min(max(top + delta, 0), max(len(rows) - height, 0))

    def _scroll_half_page(self, *, down: bool) -> None:
        half = max(self._viewport()[2] // 2, 1)
        self._scroll_rows(half if down else -half)

    def _scroll_page(self, *, down: bool) -> None:
        # Vim's ctrl+f/b: a full page less a two-line overlap for continuity.
        page = max(self._viewport()[2] - 2, 1)
        self._scroll_rows(page if down else -page)

    def _scroll_line(self, *, down: bool) -> None:
        rows, top, height = self._viewport()
        self._top = min(max(top + (1 if down else -1), 0), max(len(rows) - height, 0))
        cursor_row = self._cursor_screen_row(rows)
        if cursor_row < self._top:
            self._cursor_to_wrap_row(rows, self._top)
        elif cursor_row >= self._top + height:
            self._cursor_to_wrap_row(rows, self._top + height - 1)

    def _reposition(self, where: str) -> None:
        rows, top, height = self._viewport()
        cursor_row = self._cursor_screen_row(rows)
        if where == 't':
            new_top = cursor_row
        elif where == 'b':
            new_top = cursor_row - height + 1
        else:  # 'z': center
            new_top = cursor_row - height // 2
        self._top = min(max(new_top, 0), max(len(rows) - height, 0))

    def _move_to_screen_line(self, where: str) -> None:
        rows, top, height = self._viewport()
        if where == 'H':
            index = top
        elif where == 'L':
            index = top + height - 1
        else:  # 'M'
            index = top + height // 2
        row = rows[min(max(index, 0), len(rows) - 1)]
        line = self.doc.line(row.doc_row)
        stripped = line.lstrip(' \t')
        col = (len(line) - len(stripped)) if stripped else 0
        self._engine.set_cursor(Pos(row.doc_row, col))

    def _handle_view_key(self, key: Key) -> bool:
        if not self._visible_modes():
            self._pending_z = False
            return False

        if self._pending_z:
            self._pending_z = False
            if key in (Key('z'), Key('t'), Key('b')):
                self._reposition('z' if key.base == 'z' else key.base)
            return True

        if key == Key('d', ctrl=True) or key == Key('u', ctrl=True):
            self._scroll_half_page(down=key.base == 'd')
            return True
        if key == Key('f', ctrl=True) or key == Key('b', ctrl=True):
            self._scroll_page(down=key.base == 'f')
            return True
        if key == Key('e', ctrl=True) or key == Key('y', ctrl=True):
            self._scroll_line(down=key.base == 'e')
            return True

        if self._engine.status().pending:
            return False  # an in-progress command (d, 2, ...) owns plain letters

        if key == Key('z'):
            self._pending_z = True
            return True
        if key in (Key('H'), Key('M'), Key('L')):
            self._move_to_screen_line(key.base)
            return True

        return False

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

        # Submit semantics. ctrl+j is the universally-portable submit chord: 0x0a is byte-distinguishable from Enter's
        # 0x0d on every terminal (we clear ICRNL), no extended-key protocol required.
        if key.base == 'enter':
            if key.ctrl or key.alt or key.shift:
                self._submit()
                return True
            if engine.mode is Mode.NORMAL:
                self._submit()
                return True
            engine.feed('\r')
            return True

        if key == Key('j', ctrl=True) and self._on_submit is not None:
            self._submit()
            return True

        if key == Key('r', ctrl=True):
            if engine.mode is Mode.NORMAL:
                engine.redo()
                return True
            return False

        if key == Key('v', ctrl=True) and self._visible_modes():
            engine.feed('<c-v>')
            return True

        if self._handle_view_key(key):
            return True

        if engine.mode is Mode.INSERT and (token := _INSERT_CHORD_TOKENS.get(key)) is not None:
            engine.feed(token)
            return True

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
