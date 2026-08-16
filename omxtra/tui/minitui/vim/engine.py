"""
The modal editing engine: keys in, document edits + pure-data feedback out.

Reshaped from x/vibes/minivim onto the docs layer:
 - All mutation flows through Document range edits; undo/redo are groups of `AppliedEdit` inverses (one group per
   change command - a `c` operator's typed insertion is part of its group, matching vim's undo units).
 - Cursors are a tuple (primary first) per the multi-cursor groundwork; only the primary is used so far.
 - `/` `?` `:` are a real CMDLINE mode: search is incremental (`decorations()` exposes live match spans), `:` lines
   go to an injectable ex handler.
 - `status()` and `decorations()` are the only outputs besides the document itself - the engine never renders and
   never reads a keyboard; frontends pump `feed()` with plain chars (plus '<left>'-style tokens for special keys).

Grown beyond minivim: CMDLINE mode, edit-group undo/redo, `%` and `~`, and blockwise visual (ctrl+v: BLOCK spans,
d/y/c/p over rectangles - block-change types on the first row only, no replication yet). Still deliberately out of
scope: marks/jumplist, macros (q), regex search, ex ranges, block insert (I/A). The dot-repeat is a keystroke
recorder/replayer, exactly like vim's redo buffer.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from ..docs.cursors import Cursor
from ..docs.documents import Document
from ..docs.edits import AppliedEdit
from ..docs.edits import TextEdit
from ..docs.edits import remap_pos_through
from ..docs.positions import Kind
from ..docs.positions import Pos
from ..docs.positions import Span
from ..docs.searching import find_matches
from ..docs.searching import next_match
from .modes import CmdlineKind
from .modes import Mode
from .motions import MOTION_NEEDS_ARG
from .motions import WANT_EOL
from .motions import MotionResult
from .motions import resolve
from .parsing import CMDLINE_STARTERS
from .parsing import ESC
from .parsing import Command
from .parsing import Parser
from .registers import Registers
from .registers import RegValue
from .registers import pieces_repeat
from .scans import BRACKET_PAIRS
from .scans import CLOSE_BRACKETS
from .scans import char_at
from .scans import char_class
from .scans import clamp_col
from .scans import find_char
from .scans import first_nonblank
from .scans import llen
from .scans import match_bracket
from .scans import retreat
from .scans import word_back
from .scans import word_end
from .scans import word_fwd
from .status import CURSOR_TAG
from .status import SEARCH_CURRENT_TAG
from .status import SEARCH_MATCH_TAG
from .status import SELECTION_TAG
from .status import Decoration
from .status import VimStatus
from .substitutes import SubstituteError
from .substitutes import apply_substitute
from .substitutes import parse_ex_range
from .substitutes import parse_substitute
from .textobjs import textobj


ExHandler: ta.TypeAlias = ta.Callable[[str], str | None]


##


BACKSPACES: ta.AbstractSet[str] = frozenset(('\x7f', '\x08'))

SHIFTWIDTH = 4

# Special-key tokens fed by frontends; mapped to motions in normal/visual mode, handled directly in insert mode.
TOKEN_MOTIONS: ta.Mapping[str, str] = {
    '<left>': 'h',
    '<right>': 'l',
    '<up>': 'k',
    '<down>': 'j',
    '<home>': '0',
    '<end>': '$',
}

# Synonym commands compile straight to op+motion / doubled op, like vim.
SYNONYMS: ta.Mapping[str, tuple[str, str | None, bool]] = {
    'x': ('d', 'l', False),
    'X': ('d', 'h', False),
    'D': ('d', '$', False),
    'C': ('c', '$', False),
    's': ('c', 'l', False),
    'S': ('c', None, True),
    'Y': ('y', None, True),
}


@dc.dataclass(frozen=True)
class _UndoEntry(lang.Final):
    edits: tuple[AppliedEdit, ...]
    cursor_before: Pos
    cursor_after: Pos


class VimEngine:
    def __init__(
            self,
            doc: Document | str = '',
            *,
            ex_handler: ExHandler | None = None,
    ) -> None:
        super().__init__()

        self._doc = Document(doc) if isinstance(doc, str) else doc
        self._ex_handler = ex_handler

        self._cursors: tuple[Cursor, ...] = (Cursor(Pos(0, 0)),)
        self._mode = Mode.NORMAL
        self._regs = Registers()
        self._parser = Parser()
        self._message = ''

        self._last_ft: tuple[str, str] | None = None  # (key, char) for ; ,
        self._visual_anchor: Pos | None = None

        self._cmdline_kind: CmdlineKind | None = None
        self._cmdline_text = ''
        self._last_visual_rows: tuple[int, int] | None = None  # the '< '> marks, by row
        self._last_search: tuple[str, bool] | None = None  # (query, forward)
        self._search_hl = False

        # dot-repeat: tap the raw key stream (vim's redo buffer)
        self._keys: list[str] = []
        self._last_change: list[str] = []
        self._rec_insert = False
        self._replaying = False
        self._no_record = False

        # undo: groups of applied edits, collected via the document listener while a group is open
        self._undo: list[_UndoEntry] = []
        self._redo: list[_UndoEntry] = []
        self._open_group: list[AppliedEdit] | None = None
        self._group_cursor_before = Pos(0, 0)
        self._history_suppressed = False

        self._doc.add_listener(self._on_doc_change)

    ##
    # Public surface

    @property
    def doc(self) -> Document:
        return self._doc

    @property
    def mode(self) -> Mode:
        return self._mode

    @property
    def cursors(self) -> tuple[Cursor, ...]:
        return self._cursors

    @property
    def cursor(self) -> Pos:
        return self._cursors[0].pos

    def set_cursor(self, pos: Pos) -> None:
        """Place the (single) cursor explicitly - collapses any secondary cursors."""

        pos = self._doc.clamp(pos, allow_newline_slot=self._mode is Mode.INSERT)
        self._set_all_cursors([pos])

    def add_cursor(self, pos: Pos) -> None:
        """Add a secondary cursor. Insert-mode edits apply at every cursor; Esc collapses back to the primary."""

        pos = self._doc.clamp(pos, allow_newline_slot=self._mode is Mode.INSERT)
        if all(c.pos != pos for c in self._cursors):
            self._cursors = (*self._cursors, Cursor(pos, want=pos.col))

    def clear_secondary_cursors(self) -> None:
        self._cursors = (self._cursors[0],)

    def feed(self, key: str) -> None:
        """
        Feed one key: a single character, or a '<left>'-style token for special keys.

        Enter arrives as '\\r' or '\\n'; escape as '\\x1b'; backspace as '\\x7f'.
        """

        if self._mode is Mode.INSERT:
            self._feed_insert(key)
        elif self._mode is Mode.CMDLINE:
            self._feed_cmdline(key)
        elif self._mode in (Mode.VISUAL, Mode.VISUAL_LINE, Mode.VISUAL_BLOCK):
            self._feed_visual(key)
        else:
            self._feed_normal(key)

    def send(self, keys: str) -> None:
        for k in keys:
            self.feed(k)

    def enter_insert(self) -> None:
        """Enter insert mode directly (frontends that start their input areas in insert mode)."""

        if self._mode in (Mode.VISUAL, Mode.VISUAL_LINE):
            self._leave_visual()
        elif self._mode is Mode.CMDLINE:
            self._leave_cmdline()
        self._mode = Mode.INSERT
        self._begin_change()

    def insert_text(self, text: str) -> None:
        """Insert text at every cursor (paste). In normal mode the cursor lands after the insertion."""

        self._begin_change()
        self._insert_at_cursors(text)
        if self._mode is not Mode.INSERT:
            self._end_change()

    def render(self) -> str:
        return self._doc.text()

    def status(self) -> VimStatus:
        cmdline: str | None = None
        if self._mode is Mode.CMDLINE and self._cmdline_kind is not None:
            cmdline = self._cmdline_kind.value + self._cmdline_text
        return VimStatus(
            mode=self._mode,
            pending=self._parser.pending,
            cmdline=cmdline,
            message=self._message,
            cursor_count=len(self._cursors),
        )

    def decorations(self) -> list[Decoration]:
        decs: list[Decoration] = []

        if (
                self._mode in (Mode.VISUAL, Mode.VISUAL_LINE, Mode.VISUAL_BLOCK) and
                self._visual_anchor is not None
        ):
            decs.append(Decoration(self._visual_span(), SELECTION_TAG))

        for extra in self._cursors[1:]:
            decs.append(Decoration(
                Span(Kind.EXCLUSIVE, extra.pos, Pos(extra.pos.row, extra.pos.col + 1)),
                CURSOR_TAG,
            ))

        query: str | None = None
        forward = True
        if self._mode is Mode.CMDLINE and self._cmdline_kind in (
                CmdlineKind.SEARCH_FORWARD,
                CmdlineKind.SEARCH_BACKWARD,
        ):
            query = self._cmdline_text
            forward = self._cmdline_kind is CmdlineKind.SEARCH_FORWARD
        elif self._search_hl and self._last_search is not None:
            query, forward = self._last_search

        if query:
            matches = find_matches(self._doc, query)
            current = next_match(matches, self.cursor, reverse=not forward)
            for span in matches:
                decs.append(Decoration(span, SEARCH_CURRENT_TAG if span == current else SEARCH_MATCH_TAG))

        return decs

    ##
    # Cursor plumbing

    def _set_cursor(self, pos: Pos, *, want: int | None = None) -> None:
        primary = self._cursors[0]
        self._cursors = (
            Cursor(pos, want=want if want is not None else primary.want),
            *self._cursors[1:],
        )

    def _set_all_cursors(self, positions: ta.Sequence[Pos]) -> None:
        """Replace the whole cursor set; positions[0] is the primary. Coinciding cursors merge (first wins)."""

        seen: set[Pos] = set()
        cursors: list[Cursor] = []
        for pos in positions:
            if pos not in seen:
                seen.add(pos)
                cursors.append(Cursor(pos, want=pos.col))
        self._cursors = tuple(cursors) if cursors else (Cursor(Pos(0, 0)),)

    def _edit_at_cursors(
            self,
            make: ta.Callable[[Pos], tuple[Pos, Pos, str] | None],
            place: ta.Callable[[AppliedEdit], Pos],
    ) -> None:
        """
        Apply one logical edit at every cursor: ascending document order, each cursor's position remapped through the
        edits already applied this keystroke - the whole reason edits are ranges with remappable positions.
        """

        order = sorted(range(len(self._cursors)), key=lambda i: self._cursors[i].pos)
        applied: list[TextEdit] = []
        new_pos: dict[int, Pos] = {}
        for i in order:
            pos = remap_pos_through(self._cursors[i].pos, applied)
            if (spec := make(pos)) is None:
                new_pos[i] = pos
                continue
            start, end, text = spec
            a = self._doc.replace(start, end, text)
            applied.append(a.edit)
            new_pos[i] = place(a)
        self._set_all_cursors([new_pos[i] for i in range(len(self._cursors))])

    @property
    def _want(self) -> int:
        return self._cursors[0].want

    ##
    # Undo plumbing

    def _on_doc_change(self, doc: Document, applied: AppliedEdit) -> None:
        if self._history_suppressed:
            return
        if self._open_group is not None:
            self._open_group.append(applied)
        else:
            # An edit outside any engine change (external/programmatic): position-based history is no longer valid.
            self._undo.clear()
            self._redo.clear()

    def _begin_change(self) -> None:
        if self._open_group is None:
            self._open_group = []
            self._group_cursor_before = self.cursor

    def _end_change(self) -> None:
        group = self._open_group
        self._open_group = None
        if group:
            self._undo.append(_UndoEntry(tuple(group), self._group_cursor_before, self.cursor))
            self._redo.clear()

    def _apply_history(self, entry: _UndoEntry, *, undo: bool) -> None:
        self._history_suppressed = True
        try:
            if undo:
                for applied in reversed(entry.edits):
                    self._doc.apply(applied.inverse)
            else:
                for applied in entry.edits:
                    self._doc.apply(applied.edit)
        finally:
            self._history_suppressed = False
        target = entry.cursor_before if undo else entry.cursor_after
        self._set_all_cursors([clamp_col(self._doc, self._doc.clamp(target))])

    ##
    # Normal mode

    def _feed_normal(self, key: str) -> None:
        if key in CMDLINE_STARTERS and self._parser.is_idle:
            self._enter_cmdline(CmdlineKind(key))
            return

        if key == '<c-v>' and self._parser.is_idle:
            self._keys.clear()
            self._visual_anchor = self.cursor
            self._set_visual(Mode.VISUAL_BLOCK)
            return

        key = TOKEN_MOTIONS.get(key, key)

        if not self._replaying:
            self._keys.append(key)

        state, cmd = self._parser.feed(key)

        if state == 'more':
            return

        if state == 'abort':
            self._keys.clear()
            if key == ESC:
                # Esc in normal mode also clears search highlight and messages (the :noh convention).
                self._search_hl = False
                self._message = ''
            return

        self._no_record = False
        changed = self._exec(check.not_none(cmd))

        if self._open_group is not None and self._mode is not Mode.INSERT:
            self._end_change()

        if self._replaying:
            return

        if changed and not self._no_record:
            if self._mode is Mode.INSERT:
                self._rec_insert = True  # keep taping until Esc
            else:
                self._last_change = self._keys.copy()
                self._keys.clear()
        else:
            self._keys.clear()

    ##
    # Insert mode

    def _insert_at_cursors(self, text: str) -> None:
        self._edit_at_cursors(
            lambda pos: (pos, pos, text),
            lambda a: a.edit.new_end,
        )

    def _backspace_at_cursors(self) -> None:
        doc = self._doc

        def make(pos: Pos) -> tuple[Pos, Pos, str] | None:
            if pos.col > 0:
                return (Pos(pos.row, pos.col - 1), pos, '')
            if pos.row > 0:
                return (Pos(pos.row - 1, llen(doc, pos.row - 1)), Pos(pos.row, 0), '')
            return None

        self._edit_at_cursors(make, lambda a: a.edit.start)

    def _move_cursors_insert(self, key: str) -> None:
        doc = self._doc

        def move(pos: Pos) -> Pos:
            if key == '<left>':
                return Pos(pos.row, max(0, pos.col - 1))
            if key == '<right>':
                return Pos(pos.row, min(pos.col + 1, llen(doc, pos.row)))
            if key == '<up>' and pos.row > 0:
                return Pos(pos.row - 1, min(pos.col, llen(doc, pos.row - 1)))
            if key == '<down>' and pos.row + 1 < doc.line_count():
                return Pos(pos.row + 1, min(pos.col, llen(doc, pos.row + 1)))
            if key == '<home>':
                return Pos(pos.row, 0)
            if key == '<end>':
                return Pos(pos.row, llen(doc, pos.row))
            return pos

        self._set_all_cursors([move(c.pos) for c in self._cursors])

    def _feed_insert(self, key: str) -> None:
        if self._rec_insert and not self._replaying:
            self._keys.append(key)

        if key == ESC:
            self.clear_secondary_cursors()
            cur = self.cursor
            self._mode = Mode.NORMAL
            self._set_cursor(Pos(cur.row, max(0, cur.col - 1)), want=max(0, cur.col - 1))
            self._end_change()
            if self._rec_insert:
                self._last_change = self._keys.copy()
                self._keys.clear()
                self._rec_insert = False
            return

        if key in ('\r', '\n'):
            self._insert_at_cursors('\n')
            return

        if key in BACKSPACES:
            self._backspace_at_cursors()
            return

        if key.startswith('<'):
            self._move_cursors_insert(key)
            return

        if len(key) == 1 and (key.isprintable() or key == '\t'):
            self._insert_at_cursors(key)

    ##
    # Cmdline mode (/ ? :)

    def _enter_cmdline(self, kind: CmdlineKind) -> None:
        self._mode = Mode.CMDLINE
        self._cmdline_kind = kind
        self._cmdline_text = ''
        self._message = ''

    def _leave_cmdline(self) -> None:
        self._mode = Mode.NORMAL
        self._cmdline_kind = None
        self._cmdline_text = ''

    def _accept_search(self, kind: CmdlineKind, query: str) -> None:
        forward = kind is CmdlineKind.SEARCH_FORWARD
        if not query:
            if self._last_search is None:
                return
            query = self._last_search[0]  # bare / or ? repeats the last query, with this direction

        self._last_search = (query, forward)
        self._search_hl = True

        matches = find_matches(self._doc, query)
        if (m := next_match(matches, self.cursor, reverse=not forward)) is not None:
            self._set_cursor(clamp_col(self._doc, m.start), want=m.start.col)
        else:
            self._message = f'Pattern not found: {query}'

    def _try_builtin_ex(self, text: str) -> bool:
        """Engine-owned ex commands: [range]s/// and bare-range line jumps. True if handled."""

        doc = self._doc
        rng, rest = parse_ex_range(
            text,
            current_row=self.cursor.row,
            last_row=doc.line_count() - 1,
            visual=self._last_visual_rows,
        )
        rest = rest.strip()

        if rng is not None and not rest:
            # A bare range is a jump to its last line (':42', ':$', ':%').
            col = first_nonblank(doc, rng.end_row)
            self._set_cursor(Pos(rng.end_row, col), want=col)
            return True

        if (spec := parse_substitute(rest)) is None:
            return False

        if rng is None:
            rng = parse_ex_range('.', current_row=self.cursor.row, last_row=doc.line_count() - 1)[0]
            rng = check.not_none(rng)

        last_query = self._last_search[0] if self._last_search is not None else None
        self._begin_change()
        try:
            result = apply_substitute(doc, rng, spec, last_search=last_query)
        except SubstituteError as e:
            self._message = str(e)
        else:
            col = first_nonblank(doc, min(result.last_row, doc.line_count() - 1))
            self._set_cursor(doc.clamp(Pos(result.last_row, col)), want=col)
            self._message = result.message
        finally:
            self._end_change()
        return True

    def _accept_ex(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        if self._try_builtin_ex(text):
            return
        if self._ex_handler is not None:
            self._message = self._ex_handler(text) or ''
        else:
            self._message = f'Not an editor command: {text}'

    def _feed_cmdline(self, key: str) -> None:
        if key == ESC:
            self._leave_cmdline()
            return

        if key in ('\r', '\n'):
            kind = check.not_none(self._cmdline_kind)
            text = self._cmdline_text
            self._leave_cmdline()
            if kind is CmdlineKind.EX:
                self._accept_ex(text)
            else:
                self._accept_search(kind, text)
            return

        if key in BACKSPACES:
            if self._cmdline_text:
                self._cmdline_text = self._cmdline_text[:-1]
            else:
                self._leave_cmdline()
            return

        if len(key) == 1 and key.isprintable():
            self._cmdline_text += key

    ##
    # Visual mode

    def _feed_visual(self, key: str) -> None:  # noqa: C901
        if key == ':' and self._parser.is_idle:
            self._leave_visual()  # records the '< '> marks
            self._enter_cmdline(CmdlineKind.EX)
            self._cmdline_text = "'<,'>"
            return

        if key == '<c-v>':
            if self._mode is Mode.VISUAL_BLOCK:
                self._leave_visual()
            else:
                self._set_visual(Mode.VISUAL_BLOCK)
            self._parser.reset()
            return

        key = TOKEN_MOTIONS.get(key, key)

        state, cmd = self._parser.feed(key)

        if state == 'more':
            return

        if state == 'abort':
            if key == ESC:
                self._leave_visual()
            return

        cmd = check.not_none(cmd)

        # exits / toggles
        if cmd.action == 'v':
            if self._mode is Mode.VISUAL:
                self._leave_visual()
            else:
                self._set_visual(Mode.VISUAL)
            return

        if cmd.action == 'V':
            if self._mode is Mode.VISUAL_LINE:
                self._leave_visual()
            else:
                self._set_visual(Mode.VISUAL_LINE)
            return

        if cmd.action == 'o':
            anchor = check.not_none(self._visual_anchor)
            self._visual_anchor = self.cursor
            self._set_cursor(anchor, want=anchor.col)
            return

        # blockwise I/A: a cursor per block row, live-replicating insert (vim replays at Esc; we show it live)
        if self._mode is Mode.VISUAL_BLOCK and cmd.action in ('I', 'A'):
            span = self._visual_span()
            self._leave_visual()
            self._begin_change()
            doc = self._doc
            positions: list[Pos] = []
            if cmd.action == 'A':
                col = span.end.col
                for r in range(span.start.row, span.end.row + 1):
                    if (pad := col - llen(doc, r)) > 0:
                        doc.insert(Pos(r, llen(doc, r)), ' ' * pad)
                    positions.append(Pos(r, col))
            else:
                col = span.start.col
                positions = [
                    Pos(r, col)
                    for r in range(span.start.row, span.end.row + 1)
                    if llen(doc, r) >= col  # vim skips lines that don't reach the block's left edge
                ]
                if not positions:
                    positions = [self._doc.clamp(Pos(span.start.row, col))]
            self._set_all_cursors(positions)
            self._mode = Mode.INSERT
            return

        # operator (or synonym) applies to the selection
        opkey = cmd.op

        if cmd.action in ('x', 'd'):
            opkey = 'd'
        elif cmd.action == 's':
            opkey = 'c'

        if cmd.action is not None and cmd.action in SYNONYMS and opkey is None:
            opkey = SYNONYMS[cmd.action][0]

        if opkey:
            span = self._visual_span()
            self._leave_visual()
            self._apply_op(opkey, span, cmd.register)
            if self._open_group is not None and self._mode is not Mode.INSERT:
                self._end_change()
            return

        # text object extends the selection
        if cmd.tobj:
            tobj_around, tobj_obj = cmd.tobj
            sp = textobj(self._doc, self.cursor, around=tobj_around, obj=tobj_obj, count=cmd.count)
            if sp:
                self._visual_anchor = sp.start
                end = self._retreat_or(sp.end)
                self._set_cursor(clamp_col(self._doc, end))
            return

        # motion moves the free end
        if cmd.motion_key:
            if (mr := self._eval_motion(cmd)) is not None:
                self._move_to(mr)

    def _retreat_or(self, pos: Pos) -> Pos:
        return retreat(self._doc, pos) or pos

    def _set_visual(self, mode: Mode) -> None:
        self._mode = mode
        self._parser.visual = True

    def _leave_visual(self) -> None:
        if self._visual_anchor is not None:
            a, b = sorted((self._visual_anchor.row, self.cursor.row))
            self._last_visual_rows = (a, b)
        self._mode = Mode.NORMAL
        self._visual_anchor = None
        self._parser.visual = False

    def _visual_span(self) -> Span:
        anchor = check.not_none(self._visual_anchor)
        a, b = sorted([anchor, self.cursor])
        if self._mode is Mode.VISUAL_LINE:
            return Span(Kind.LINEWISE, Pos(a.row, 0), Pos(b.row, 0))
        if self._mode is Mode.VISUAL_BLOCK:
            c1 = min(anchor.col, self.cursor.col)
            c2 = max(anchor.col, self.cursor.col) + 1
            return Span(Kind.BLOCK, Pos(a.row, c1), Pos(b.row, c2))
        end = Pos(b.row, min(b.col + 1, llen(self._doc, b.row)))  # incl. cursor char
        return Span(Kind.EXCLUSIVE, a, end)

    ##
    # Command execution

    def _exec(self, cmd: Command) -> bool:
        """Run one parsed command. Returns True iff the document changed."""

        if cmd.action is not None and cmd.action in SYNONYMS:
            op, mkey, doubled = SYNONYMS[cmd.action]
            cmd = Command(
                register=cmd.register,
                count=cmd.count,
                has_count=cmd.has_count,
                op=op,
                motion_key=mkey,
                doubled=doubled,
            )

        if cmd.action:
            return self._exec_action(cmd)

        if cmd.op and cmd.doubled:  # dd yy cc >> <<
            r = self.cursor.row
            r2 = min(r + cmd.count - 1, self._doc.line_count() - 1)
            return self._apply_op(cmd.op, Span(Kind.LINEWISE, Pos(r, 0), Pos(r2, 0)), cmd.register)

        if cmd.op and cmd.tobj:
            tobj_around, tobj_obj = cmd.tobj
            sp = textobj(self._doc, self.cursor, around=tobj_around, obj=tobj_obj, count=cmd.count)
            if sp is None:
                return False
            return self._apply_op(cmd.op, sp, cmd.register)

        if cmd.op and cmd.motion_key:
            mkey = cmd.motion_key
            # vim's `cw` special case: on a non-blank, cw acts like ce
            if cmd.op == 'c' and mkey in 'wW' and char_class(char_at(self._doc, self.cursor), mkey == 'W') != 0:
                cmd = dc.replace(cmd, motion_key='e' if mkey == 'w' else 'E')
            mr = self._eval_motion(cmd)
            if mr is None:
                return False  # motion failed: no-op
            sp = resolve(self._doc, self.cursor, mr)
            if sp is None:
                return False
            return self._apply_op(check.not_none(cmd.op), sp, cmd.register)

        if cmd.motion_key:  # bare motion: move
            if (mr := self._eval_motion(cmd)) is not None:
                self._move_to(mr)
            return False

        return False

    ##
    # Motion evaluation (the nv_cmds table, in miniature)

    def _eval_motion(self, cmd: Command) -> MotionResult | None:  # noqa: C901
        doc, p, n = self._doc, self.cursor, cmd.count
        k, arg = cmd.motion_key, cmd.motion_arg
        exc, inc, lnw = Kind.EXCLUSIVE, Kind.INCLUSIVE, Kind.LINEWISE

        if k == 'h':
            t = Pos(p.row, max(0, p.col - n))
            return None if t == p else MotionResult(t, exc)

        if k == 'l':
            t = Pos(p.row, min(p.col + n, llen(doc, p.row)))
            return None if t == p else MotionResult(t, exc)

        if k in ('j', 'k'):
            d = n if k == 'j' else -n
            t = Pos(max(0, min(p.row + d, doc.line_count() - 1)), p.col)
            return None if t.row == p.row else MotionResult(t, lnw, keeps_curswant=True)

        if k == '0':
            return MotionResult(Pos(p.row, 0), exc)

        if k == '^':
            return MotionResult(Pos(p.row, first_nonblank(doc, p.row)), exc)

        if k == '$':
            row = min(p.row + n - 1, doc.line_count() - 1)
            return MotionResult(Pos(row, max(0, llen(doc, row) - 1)), inc, curswant_eol=True)

        if k == '%':
            # First bracket at-or-after the cursor on this line, jumped to its match.
            line = doc.line(p.row)
            col = next(
                (c for c in range(p.col, len(line)) if line[c] in BRACKET_PAIRS or line[c] in CLOSE_BRACKETS),
                None,
            )
            if col is None:
                return None
            if (mpos := match_bracket(doc, Pos(p.row, col))) is None:
                return None
            return MotionResult(mpos, inc)

        if k and k in 'wW':
            return MotionResult(word_fwd(doc, p, n, k == 'W'), exc)

        if k and k in 'bB':
            return MotionResult(word_back(doc, p, n, k == 'B'), exc)

        if k and k in 'eE':
            return MotionResult(word_end(doc, p, n, k == 'E'), inc)

        if k == 'G':
            row = min(cmd.count - 1, doc.line_count() - 1) if cmd.has_count else doc.line_count() - 1
            return MotionResult(Pos(row, 0), lnw, to_first_nonblank=True)

        if k == 'gg':
            row = min(cmd.count - 1, doc.line_count() - 1) if cmd.has_count else 0
            return MotionResult(Pos(row, 0), lnw, to_first_nonblank=True)

        if k and k in 'nN':
            if self._last_search is None:
                return None
            query, forward = self._last_search
            if k == 'N':
                forward = not forward
            matches = find_matches(doc, query)
            target = p
            for _ in range(n):
                if (m := next_match(matches, target, reverse=not forward)) is None:
                    return None
                target = m.start
            self._search_hl = True
            return MotionResult(target, exc)

        if k and k in MOTION_NEEDS_ARG:  # f t F T
            fwd = k in 'ft'
            till = k in 'tT'
            t_ = find_char(doc, p, check.not_none(arg), n, forward=fwd, till=till)
            if t_ is None:
                return None
            self._last_ft = (k, check.not_none(arg))
            return MotionResult(t_, inc if fwd else exc)

        if k in (';', ','):
            if not self._last_ft:
                return None
            lk, ch = self._last_ft
            if k == ',':
                lk = {'f': 'F', 'F': 'f', 't': 'T', 'T': 't'}[lk]
            fwd, till = lk in 'ft', lk in 'tT'
            t_ = find_char(doc, p, ch, n, forward=fwd, till=till, repeat=True)
            if t_ is None:
                return None
            return MotionResult(t_, inc if fwd else exc)

        return None

    def _move_to(self, mr: MotionResult) -> None:
        doc, t = self._doc, mr.target
        if mr.kind is Kind.LINEWISE:
            if mr.to_first_nonblank:
                col = first_nonblank(doc, t.row)
                self._set_cursor(Pos(t.row, col), want=col)
            elif mr.keeps_curswant:
                col = min(self._want, max(0, llen(doc, t.row) - 1))
                self._set_cursor(Pos(t.row, col))
            else:
                col = min(t.col, max(0, llen(doc, t.row) - 1))
                self._set_cursor(Pos(t.row, col))
            return
        pos = clamp_col(doc, t)
        self._set_cursor(pos, want=WANT_EOL if mr.curswant_eol else pos.col)

    ##
    # Operators

    def _apply_op(self, op: str, span: Span, reg: str | None) -> bool:  # noqa: C901
        doc = self._doc

        if op != 'y':
            self._begin_change()

        if op == 'y':
            pieces, kind = self._extract(span)
            self._regs.set(reg or '"', RegValue(tuple(pieces), kind), is_yank=True)
            if span.kind is not Kind.LINEWISE:
                self._set_cursor(clamp_col(doc, span.start))
            return False

        if op in '><':
            for r in range(span.start.row, span.end.row + 1):
                line = doc.line(r)
                if op == '>':
                    if line:  # vim skips empty lines
                        doc.insert(Pos(r, 0), ' ' * SHIFTWIDTH)
                else:
                    lead = len(line) - len(line.lstrip(' '))
                    if (strip := min(SHIFTWIDTH, lead)):
                        doc.delete(Pos(r, 0), Pos(r, strip))
            col = first_nonblank(doc, span.start.row)
            self._set_cursor(Pos(span.start.row, col), want=col)
            return True

        if op == 'd':
            pieces, kind = self._extract(span)
            self._regs.set(reg or '"', RegValue(tuple(pieces), kind), is_yank=False)
            self._delete_span(span)
            return True

        if op == 'c':
            pieces, kind = self._extract(span)
            self._regs.set(reg or '"', RegValue(tuple(pieces), kind), is_yank=False)
            if span.kind is Kind.BLOCK:
                # A cursor per row: typed text live-replicates onto every block row (vim replays at Esc instead).
                self._delete_span(span)
                self._set_all_cursors([
                    Pos(r, min(span.start.col, llen(doc, r)))
                    for r in range(span.start.row, span.end.row + 1)
                ])
                self._mode = Mode.INSERT
                return True
            if span.kind is Kind.LINEWISE:
                r1, r2 = span.start.row, span.end.row
                doc.replace(Pos(r1, 0), Pos(r2, llen(doc, r2)), '')
                self._set_cursor(Pos(r1, 0))
            else:
                doc.delete(span.start, span.end)
                self._set_cursor(Pos(span.start.row, min(span.start.col, llen(doc, span.start.row))))
            self._mode = Mode.INSERT
            return True

        return False

    def _extract(self, span: Span) -> tuple[list[str], Kind]:
        doc = self._doc
        if span.kind is Kind.LINEWISE:
            return ([doc.line(r) for r in range(span.start.row, span.end.row + 1)], Kind.LINEWISE)
        if span.kind is Kind.BLOCK:
            return (
                [
                    doc.line(r)[span.start.col: min(span.end.col, llen(doc, r))]
                    for r in range(span.start.row, span.end.row + 1)
                ],
                Kind.BLOCK,
            )
        return (doc.get_text(span.start, span.end).split('\n'), Kind.EXCLUSIVE)

    def _delete_span(self, span: Span) -> None:
        doc = self._doc
        if span.kind is Kind.BLOCK:
            # Row-local deletes: column positions on other rows are unaffected, so order doesn't matter.
            for r in range(span.start.row, span.end.row + 1):
                line_len = llen(doc, r)
                a = min(span.start.col, line_len)
                b = min(span.end.col, line_len)
                if b > a:
                    doc.delete(Pos(r, a), Pos(r, b))
            pos = clamp_col(doc, self._doc.clamp(Pos(span.start.row, span.start.col)))
            self._set_cursor(pos, want=pos.col)
            return
        if span.kind is Kind.LINEWISE:
            r1, r2 = span.start.row, span.end.row
            last = doc.line_count() - 1
            if r2 >= last:
                if r1 == 0:
                    doc.set_text('')
                else:
                    doc.delete(Pos(r1 - 1, llen(doc, r1 - 1)), Pos(r2, llen(doc, r2)))
            else:
                doc.delete(Pos(r1, 0), Pos(r2 + 1, 0))
            row = min(r1, doc.line_count() - 1)
            col = first_nonblank(doc, row)
            self._set_cursor(Pos(row, col), want=col)
        else:
            doc.delete(span.start, span.end)
            pos = clamp_col(doc, span.start)
            self._set_cursor(pos, want=pos.col)

    ##
    # Simple actions

    def _exec_action(self, cmd: Command) -> bool:  # noqa: C901
        doc, cur, n = self._doc, self.cursor, cmd.count
        a = cmd.action

        if a in ('p', 'P'):
            rv = self._regs.get(cmd.register or '"')
            if not rv:
                return False
            self._begin_change()
            self._put(rv, n, after=a == 'p')
            return True

        if a and a in 'iIaAoO':
            self._begin_change()
            line = doc.line(cur.row)
            if a == 'i':
                pass
            elif a == 'I':
                self._set_cursor(Pos(cur.row, first_nonblank(doc, cur.row)))
            elif a == 'a':
                self._set_cursor(Pos(cur.row, cur.col + 1 if line else 0))
            elif a == 'A':
                self._set_cursor(Pos(cur.row, len(line)))
            elif a == 'o':
                doc.insert(Pos(cur.row, len(line)), '\n')
                self._set_cursor(Pos(cur.row + 1, 0))
            elif a == 'O':
                doc.insert(Pos(cur.row, 0), '\n')
                self._set_cursor(Pos(cur.row, 0))
            self._mode = Mode.INSERT
            return True

        if a == 'r':
            line = doc.line(cur.row)
            if cur.col + n > len(line):
                return False  # vim fails, no partial
            self._begin_change()
            doc.replace(cur, Pos(cur.row, cur.col + n), check.not_none(cmd.action_arg) * n)
            self._set_cursor(Pos(cur.row, cur.col + n - 1))
            return True

        if a == 'J':
            joins = max(n, 2) - 1
            if cur.row + joins > doc.line_count() - 1:
                joins = doc.line_count() - 1 - cur.row
            if joins <= 0:
                return False
            self._begin_change()
            for _ in range(joins):
                row = self.cursor.row
                first = doc.line(row).rstrip()
                nxt_line = doc.line(row + 1)
                nxt = nxt_line.lstrip()
                sep = '' if (not nxt or not first) else ' '
                doc.replace(
                    Pos(row, len(first)),
                    Pos(row + 1, len(nxt_line) - len(nxt)),
                    sep,
                )
                self._set_cursor(Pos(row, len(first)))
            return True

        if a == '~':
            line = doc.line(cur.row)
            if cur.col >= len(line):
                return False
            end = min(cur.col + n, len(line))
            self._begin_change()
            doc.replace(cur, Pos(cur.row, end), line[cur.col: end].swapcase())
            pos = clamp_col(doc, Pos(cur.row, end))
            self._set_cursor(pos, want=pos.col)
            return True

        if a == 'u':
            self._no_record = True
            if self._undo:
                entry = self._undo.pop()
                self._apply_history(entry, undo=True)
                self._redo.append(entry)
            return True

        if a == '.':
            self._no_record = True
            if self._last_change and not self._replaying:
                seq = list(self._last_change)
                self._keys.clear()
                self._replaying = True
                try:
                    for k in seq:  # (vim also substitutes a new count into the replay; omitted)
                        self.feed(k)
                finally:
                    self._replaying = False
                    self._no_record = True  # nested feeds reset the flag
            return True

        if a in ('v', 'V'):
            self._visual_anchor = self.cursor
            self._set_visual(Mode.VISUAL if a == 'v' else Mode.VISUAL_LINE)
            self._parser.reset()
            return False

        return False

    def redo(self) -> None:
        """ctrl+r equivalent - exposed as a method since ctrl keys arrive as frontend concerns."""

        if self._redo:
            entry = self._redo.pop()
            self._apply_history(entry, undo=False)
            self._undo.append(entry)

    def _put(self, rv: RegValue, count: int, *, after: bool) -> None:  # noqa: C901
        doc, cur = self._doc, self.cursor

        if rv.kind is Kind.BLOCK:
            # Paste the rectangle at the cursor column on successive rows, creating rows / padding as needed.
            # (A count would stack copies; ignored for now, like vim's rarer block-put variants.)
            col = cur.col + 1 if (after and llen(doc, cur.row)) else cur.col
            for i, piece in enumerate(rv.pieces):
                row = cur.row + i
                if row >= doc.line_count():
                    end = doc.end_pos()
                    doc.insert(end, '\n')
                line_len = llen(doc, row)
                if line_len < col:
                    doc.insert(Pos(row, line_len), ' ' * (col - line_len))
                doc.insert(Pos(row, col), piece)
            pos = clamp_col(doc, Pos(cur.row, col))
            self._set_cursor(pos, want=pos.col)
            return

        if rv.kind is Kind.LINEWISE:
            text = '\n'.join(rv.pieces * count)
            last = doc.line_count() - 1
            if after:
                if cur.row >= last:
                    doc.insert(Pos(cur.row, llen(doc, cur.row)), '\n' + text)
                else:
                    doc.insert(Pos(cur.row + 1, 0), text + '\n')
                row = cur.row + 1
            else:
                doc.insert(Pos(cur.row, 0), text + '\n')
                row = cur.row
            col = first_nonblank(doc, row)
            self._set_cursor(Pos(row, col), want=col)
            return

        pieces = pieces_repeat(rv.pieces, count)
        line = doc.line(cur.row)
        col = cur.col + 1 if (after and line) else cur.col
        doc.insert(Pos(cur.row, col), '\n'.join(pieces))

        if len(pieces) == 1:
            pos = Pos(cur.row, max(col, col + len(pieces[0]) - 1))
        else:
            last_row = cur.row + len(pieces) - 1
            pos = Pos(last_row, max(0, len(pieces[-1]) - 1))
        self._set_cursor(pos, want=pos.col)
