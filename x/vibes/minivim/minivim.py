"""
mini_vim -- a small, vim-inspired modal editing engine over an abstract buffer.

Architecture (mirrors real vim's shape, cleaned up):

    keys ──> Parser (modal state machine; "operator-pending" is parser state)
                 │  emits a complete Command:
                 │    ["reg][count] {op [count]} {motion|textobj} | action
                 ▼
             eval_motion:  (buffer, pos, count) -> MotionResult(target, KIND)
                 │         KIND is charwise-EXCLUSIVE / charwise-INCLUSIVE / LINEWISE
                 ▼
             resolve():    (start, MotionResult) -> Span
                 │         applies vim's `:help exclusive` adjustment rules --
                 │         these two rules alone are why `dw` behaves sanely
                 ▼
             operators:    d / c / y / > / <  edit via the Buffer protocol,
                           write typed registers (charwise vs linewise)

Cross-cutting, exactly like vim:
  * `.` repeat is a *keystroke recorder + replayer* (vim's "redo buffer"), not a semantic diff -- this is why
    `ciwfoo<Esc>` repeats with new text.
  * curswant: j/k remember the column you *want*, `$` pins it to end-of-line.
  * Many "commands" are synonyms compiled to op+motion: x=dl, D=d$, C=c$, s=cl, S=cc, Y=yy. (vim does the same
    internally.)
  * Registers carry a kind; linewise `p` opens lines, charwise `p` splices.

The engine talks to documents only through the `Buffer` protocol (5 methods), so adapting a rope / piece table / GUI
text store means implementing those five methods and pumping decoded keys into `Engine.feed()`. See demo_tty.py for a
~60-line curses frontend.

Deliberately out of scope (noted where relevant): ex commands (`:`), search (`/ ? n N`), marks/jumplist, macros (`q`),
blockwise visual, undo *tree* (we keep a linear snapshot stack), multibyte/virtual columns.
"""
import dataclasses as dc
import enum
import typing as ta


##


ESC = '\x1b'
BACKSPACES = ('\x7f', '\x08')
INF = 10**9  # curswant value meaning "end of line, whatever that is"
SHIFTWIDTH = 4


##
# Positions and range kinds


@dc.dataclass(frozen=True, order=True)
class Pos:
    row: int
    col: int


class Kind(enum.Enum):
    """How a motion characterizes the text it covers (vim: :help inclusive)."""

    EXCLUSIVE = enum.auto()  # charwise, target char NOT covered (w, b, h, 0, F, T)
    INCLUSIVE = enum.auto()  # charwise, target char covered     (e, f, t, $)
    LINEWISE = enum.auto()   # whole lines                       (j, k, G, gg, dd)


##
# The abstract document interface. This is the entire adapter surface.


class Buffer(ta.Protocol):
    def line_count(self) -> int: ...

    def get_line(self, row: int) -> str: ...
    def set_line(self, row: int, text: str) -> None: ...

    def insert_line(self, row: int, text: str) -> None: ...
    def delete_line(self, row: int) -> None: ...


class ListBuffer:
    """Reference Buffer: a plain list of lines. Swap in anything you like."""

    def __init__(self, text: str = '') -> None:
        self._lines = text.split('\n') if text else ['']

    def line_count(self) -> int:
        return len(self._lines)

    def get_line(self, row: int) -> str:
        return self._lines[row]

    def set_line(self, row: int, text: str) -> None:
        self._lines[row] = text

    def insert_line(self, row: int, text: str) -> None:
        self._lines.insert(row, text)

    def delete_line(self, row: int) -> None:
        del self._lines[row]

    # convenience for tests/undo (not part of the protocol)
    def snapshot(self) -> list[str]:
        return list(self._lines)

    def restore(self, lines: ta.Iterable[str]) -> None:
        self._lines = list(lines)

    def text(self) -> str:
        return '\n'.join(self._lines)


##
# Scan space: iterate a buffer as if lines ended in a virtual "newline slot" at col == len(line). That slot is
# blank-class, which is exactly why word runs never merge across lines. Empty lines are a single newline slot.


def _llen(buf: Buffer, row: int) -> int:
    return len(buf.get_line(row))


def _char(buf: Buffer, p: Pos) -> str | None:
    line = buf.get_line(p.row)
    return line[p.col] if p.col < len(line) else None  # None == newline slot


def _advance(buf: Buffer, p: Pos) -> Pos | None:
    if p.col < _llen(buf, p.row):
        return Pos(p.row, p.col + 1)
    if p.row + 1 < buf.line_count():
        return Pos(p.row + 1, 0)
    return None


def _retreat(buf: Buffer, p: Pos) -> Pos | None:
    if p.col > 0:
        return Pos(p.row, p.col - 1)
    if p.row > 0:
        return Pos(p.row - 1, _llen(buf, p.row - 1))
    return None


def _first_nonblank(buf: Buffer, row: int) -> int:
    line = buf.get_line(row)
    stripped = line.lstrip(' \t')
    return len(line) - len(stripped) if stripped else 0


def _clamp_col(buf: Buffer, p: Pos) -> Pos:
    """Normal-mode cursor may not rest on the newline slot."""

    return Pos(p.row, min(p.col, max(0, _llen(buf, p.row) - 1)))


##
# Word machinery. vim's three char classes: 0 blank, 1 punctuation, 2 word.
# For W/B/E ("big" words) every non-blank is one class.


def _cls(ch: str | None, big: bool) -> int:
    if ch is None or ch in ' \t':
        return 0
    if big:
        return 2
    return 2 if (ch == '_' or ch.isalnum()) else 1


def word_fwd(buf: Buffer, p: Pos, count: int, big: bool) -> Pos:
    """`w`/`W`: start of next word. An empty line counts as a word."""

    for _ in range(count):
        c0 = _cls(_char(buf, p), big)
        q = p
        if c0 != 0:  # step off the current word run first
            while True:
                nq = _advance(buf, q)
                if nq is None:
                    return q
                q = nq
                if _cls(_char(buf, q), big) != c0:
                    break
        else:
            nq = _advance(buf, q)
            if nq is None:
                return q
            q = nq
        while _cls(_char(buf, q), big) == 0:  # skip blanks...
            if _llen(buf, q.row) == 0:  # ...but an empty line is a word
                break
            nq = _advance(buf, q)
            if nq is None:
                break
            q = nq
        p = q
    return p


def word_end(buf: Buffer, p: Pos, count: int, big: bool) -> Pos:
    """`e`/`E`: end of word, inclusive. (Skips empty lines, as vim's e does.)"""

    for _ in range(count):
        q = p
        while True:  # move at least one, skip blanks
            nq = _advance(buf, q)
            if nq is None:
                return q
            q = nq
            if _cls(_char(buf, q), big) != 0:
                break
        c0 = _cls(_char(buf, q), big)
        while True:  # run to end of this class run
            nq = _advance(buf, q)
            if nq is None or _cls(_char(buf, nq), big) != c0:
                break
            q = nq
        p = q
    return p


def word_back(buf: Buffer, p: Pos, count: int, big: bool) -> Pos:
    """`b`/`B`: back to start of word. Empty line counts as a word."""

    for _ in range(count):
        q = _retreat(buf, p)
        if q is None:
            return p
        while _cls(_char(buf, q), big) == 0:
            if _llen(buf, q.row) == 0:
                break
            nq = _retreat(buf, q)
            if nq is None:
                return q
            q = nq
        if _llen(buf, q.row) == 0:
            p = q
            continue
        c0 = _cls(_char(buf, q), big)
        while True:
            nq = _retreat(buf, q)
            if nq is None or _cls(_char(buf, nq), big) != c0:
                break
            q = nq
        p = q
    return p


def find_char(
        buf: Buffer,
        p: Pos,
        ch: str,
        count: int,
        forward: bool,
        till: bool,
        repeat: bool = False,
) -> Pos | None:
    """
    `f t F T` (current line only, like vim). `repeat` handles the classic `;`-after-`t` stickiness: skip a target we're
    already sitting against.
    """

    line = buf.get_line(p.row)
    col = p.col
    if repeat and till:
        col = col + 1 if forward else col - 1
    for _ in range(count):
        i = line.find(ch, col + 1) if forward else line.rfind(ch, 0, max(col, 0))
        if i < 0:
            return None
        col = i
    if till:
        col += -1 if forward else 1
    if col < 0 or col >= max(len(line), 1):
        return None
    return Pos(p.row, col)


##
# Motions. A motion never edits: it *describes* -- target + kind + hints.


@dc.dataclass()
class MotionResult:
    target: Pos
    kind: Kind
    keeps_curswant: bool = False     # j/k: reuse remembered column
    to_first_nonblank: bool = False  # G/gg place cursor at first non-blank
    curswant_eol: bool = False       # $ pins curswant to "always end of line"


# motion key -> needs a trailing character argument? (vim's NV_NCH flag)
MOTION_NEEDS_ARG = {'f', 't', 'F', 'T'}
MOTION_KEYS = set('hljk0^$wWbBeEG;,') | {'gg'} | MOTION_NEEDS_ARG


##
# Resolving (start, motion) into an operable Span. Charwise spans use [start, end) with end.col allowed to equal
# len(line) ("through end of line, not the newline"). Linewise spans are row ranges.


@dc.dataclass()
class Span:
    kind: Kind  # LINEWISE or EXCLUSIVE (charwise, end-exclusive)
    start: Pos
    end: Pos    # charwise: exclusive; linewise: end.row inclusive


def resolve(buf: Buffer, start: Pos, mr: MotionResult) -> Span | None:
    if mr.kind is Kind.LINEWISE:
        r1, r2 = sorted((start.row, mr.target.row))
        return Span(Kind.LINEWISE, Pos(r1, 0), Pos(r2, 0))

    a, b = (start, mr.target) if start <= mr.target else (mr.target, start)
    if mr.kind is Kind.INCLUSIVE:
        b = Pos(b.row, min(b.col + 1, _llen(buf, b.row)))
    else:
        # vim's two `:help exclusive` adjustments. Together they produce the behavior everyone knows without w/b
        # special-casing anything:
        #   * `dw` on the last word of a line deletes to EOL, no line join
        #   * `dw` at/before the first non-blank of a line goes linewise
        if b.col == 0 and b.row > a.row:
            if a.col <= _first_nonblank(buf, a.row):
                return Span(Kind.LINEWISE, Pos(a.row, 0), Pos(b.row - 1, 0))
            b = Pos(b.row - 1, _llen(buf, b.row - 1))
    if not (a < b):
        return None
    return Span(Kind.EXCLUSIVE, a, b)


##
# Registers. Contents are stored as a list of line-pieces plus a kind; the kind decides whether `p` opens new lines or
# splices into the current.


@dc.dataclass()
class RegValue:
    pieces: list  # list[str]; linewise: whole lines
    kind: Kind    # EXCLUSIVE (charwise) or LINEWISE


class Registers:
    def __init__(self) -> None:
        self._regs: dict[str, RegValue] = {}

    def get(self, name: str) -> RegValue | None:
        return self._regs.get(name)

    def set(self, name: str, val: RegValue, *, is_yank: bool):
        if name.isalpha() and name.isupper():      # "A appends to "a
            old = self._regs.get(name.lower())
            if old:
                val = _reg_append(old, val)
            name = name.lower()
        self._regs[name] = val
        self._regs['"'] = val  # unnamed always mirrors
        if is_yank and name == '"':
            self._regs['0'] = val  # yank register
        # (vim also shifts deletes through "1-"9 and keeps "- ; omitted.)


def _reg_append(old: RegValue, new: RegValue) -> RegValue:
    if old.kind is Kind.LINEWISE or new.kind is Kind.LINEWISE:
        return RegValue(list(old.pieces) + list(new.pieces), Kind.LINEWISE)
    joined = old.pieces[:-1] + [old.pieces[-1] + new.pieces[0]] + new.pieces[1:]
    return RegValue(joined, Kind.EXCLUSIVE)


def _pieces_repeat(pieces: list, count: int) -> list:
    out = list(pieces)
    for _ in range(count - 1):
        out = out[:-1] + [out[-1] + pieces[0]] + pieces[1:]
    return out


##
# Text objects. Unlike motions they yield a Span directly -- there is no "start position + direction", just "the thing
# under the cursor".


PAIRS = {
    '(': '()',
    ')': '()',
    'b': '()',
    '{': '{}',
    '}': '{}',
    'B': '{}',
    '[': '[]',
    ']': '[]',
    '<': '<>',
    '>': '<>',
}

QUOTES = {'"', "'", '`'}

TEXTOBJ_KEYS = set('wW') | set(PAIRS) | QUOTES


def textobj(buf: Buffer, p: Pos, around: bool, obj: str, count: int) -> Span | None:
    if obj in 'wW':
        return _obj_word(buf, p, around, big=(obj == 'W'), count=count)
    if obj in PAIRS:
        return _obj_pair(buf, p, around, *PAIRS[obj])
    if obj in QUOTES:
        return _obj_quote(buf, p, around, obj)
    return None


def _obj_word(buf, p, around, big, count):
    line = buf.get_line(p.row)
    if not line:
        return None

    col = min(p.col, len(line) - 1)

    def run(c):  # (start, end_exclusive) of the class run containing col c
        k = _cls(line[c], big)
        a = c
        while a > 0 and _cls(line[a - 1], big) == k:
            a -= 1
        b = c + 1
        while b < len(line) and _cls(line[b], big) == k:
            b += 1
        return a, b

    a, b = run(col)

    if around:
        # word + trailing blanks (or leading blanks if none trail) -- per word
        for _ in range(count):
            if b < len(line) and _cls(line[b], big) == 0:
                _, b = run(b)
            elif count == 1 and a > 0 and _cls(line[a - 1], big) == 0:
                a, _ = run(a - 1)
            if count > 1 and b < len(line):  # extend over next word too
                _, b = run(b)

    else:
        for _ in range(count - 1):  # 2iw = word + space = 2 runs
            if b < len(line):
                _, b = run(b)

    return Span(Kind.EXCLUSIVE, Pos(p.row, a), Pos(p.row, b))


def _obj_pair(buf, p, around, open_ch, close_ch):
    # Backward for the unmatched open (cursor sitting ON open matches itself), forward for the unmatched close.
    # Multi-line.
    depth, q, open_pos = 0, p, None
    while q is not None:
        ch = _char(buf, q)
        if ch == close_ch and q != p:
            depth += 1
        elif ch == open_ch:
            if depth == 0:
                open_pos = q
                break
            depth -= 1
        q = _retreat(buf, q)

    if open_pos is None:
        return None

    depth, q, close_pos = 0, p, None
    while q is not None:
        ch = _char(buf, q)
        if ch == open_ch and q != p and q != open_pos:
            depth += 1
        elif ch == close_ch and q != p or (ch == close_ch and q == p and p != open_pos):
            if depth == 0:
                close_pos = q
                break
            depth -= 1
        q = _advance(buf, q)

    if close_pos is None:
        return None

    if around:
        end = _advance(buf, close_pos) or Pos(close_pos.row, close_pos.col + 1)
        return Span(Kind.EXCLUSIVE, open_pos, end)

    # vim promotes the *inner* object to linewise when the open bracket ends its line and only whitespace precedes the
    # close bracket on its line -- this is why `di{` on a code block keeps the braces on their own lines.
    if (
            open_pos.col == _llen(buf, open_pos.row) - 1 and
            close_pos.col <= _first_nonblank(buf, close_pos.row) and
            close_pos.row > open_pos.row + 1
    ):
        return Span(Kind.LINEWISE, Pos(open_pos.row + 1, 0), Pos(close_pos.row - 1, 0))

    inner = _advance(buf, open_pos)
    return Span(Kind.EXCLUSIVE, inner, close_pos)


def _obj_quote(buf, p, around, q):
    # Current line only, like vim. Pair quotes left-to-right; take the pair containing the cursor, else the next pair
    # to the right.
    line = buf.get_line(p.row)
    idx = [i for i, ch in enumerate(line) if ch == q]
    pairs = list(zip(idx[0::2], idx[1::2]))
    chosen = (
            next((ab for ab in pairs if ab[0] <= p.col <= ab[1]), None) or
            next((ab for ab in pairs if ab[0] > p.col), None)
    )
    if not chosen:
        return None
    a, b = chosen

    if around:  # (vim also swallows trailing whitespace here; omitted)
        return Span(Kind.EXCLUSIVE, Pos(p.row, a), Pos(p.row, b + 1))

    return Span(Kind.EXCLUSIVE, Pos(p.row, a + 1), Pos(p.row, b))


##
# The command grammar and parser.
#
#   command := ["reg] [count] ( motion
#                             | operator [count] (motion | i/a obj | operator)
#                             | action )
#
# feed() consumes one key and returns ("more" | "cmd" | "abort", Command?). This incremental shape is what lets a real
# frontend drive it key-by-key.


OPERATORS = set('dcy><')
ACTIONS = set('xXDCsSYpPiIaAoOuJrvV.')
ACTION_NEEDS_ARG = {'r'}


@dc.dataclass()
class Command:
    register: str | None = None
    count: int = 1
    has_count: bool = False
    op: str | None = None
    doubled: bool = False  # dd / yy / cc / >> / <<
    motion_key: str | None = None
    motion_arg: str | None = None
    tobj: tuple | None = None  # (around: bool, obj: str)
    action: str | None = None
    action_arg: str | None = None


class Parser:
    def __init__(self) -> None:
        # in visual mode the grammar inverts: the range already exists, so an operator key *terminates*
        self.visual = False
        self.reset()

    def reset(self):
        self.register: str | None = None
        self.count1 = 0
        self.count2 = 0
        self.op: str | None = None
        self.wait: tuple | None = None  # ("reg",) ("char",key) ("obj",ia) ("g",) ("achar",key)

    # helpers

    def _cmd(self, **kw) -> Command:
        c = Command(
            register=self.register,
            count=max(1, self.count1) * max(1, self.count2),
            has_count=(self.count1 > 0 or self.count2 > 0),
            op=self.op,
            **kw,
        )
        self.reset()
        return c

    def _abort(self):
        self.reset()
        return ('abort', None)

    # one key in

    def feed(self, key: str):
        if self.wait:
            tag = self.wait[0]

            if tag == 'reg':
                self.wait = None
                self.register = key
                return ('more', None)

            if tag == 'char':
                mkey = self.wait[1]
                self.wait = None
                return ('cmd', self._cmd(motion_key=mkey, motion_arg=key))

            if tag == 'achar':
                akey = self.wait[1]
                self.wait = None
                return ('cmd', self._cmd(action=akey, action_arg=key))

            if tag == 'g':
                self.wait = None
                if key == 'g':
                    return ('cmd', self._cmd(motion_key='gg'))
                return self._abort()  # (real vim: gU gu g~ g_ ge ... omitted)

            if tag == 'obj':
                around = self.wait[1] == 'a'
                self.wait = None
                if key in TEXTOBJ_KEYS:
                    return ('cmd', self._cmd(tobj=(around, key)))
                return self._abort()

        if key == ESC:
            return self._abort()

        if key.isdigit():
            active = self.count2 if self.op else self.count1

            if key == '0' and active == 0:
                return ('cmd', self._cmd(motion_key='0'))

            if self.op:
                self.count2 = self.count2 * 10 + int(key)
            else:
                self.count1 = self.count1 * 10 + int(key)

            return ('more', None)

        if key == '"' and self.register is None and self.op is None:
            self.wait = ('reg',)
            return ('more', None)

        if key == 'g':
            self.wait = ('g',)
            return ('more', None)

        if key in OPERATORS:
            if self.visual:
                self.op = key
                return ('cmd', self._cmd())

            if self.op is None:
                self.op = key
                return ('more', None)

            if key == self.op:
                return ('cmd', self._cmd(doubled=True))

            return self._abort()

        if (self.op or self.visual) and key in ('i', 'a'):
            self.wait = ('obj', key)
            return ('more', None)

        if key in MOTION_KEYS:
            if key in MOTION_NEEDS_ARG:
                self.wait = ('char', key)
                return ('more', None)

            return ('cmd', self._cmd(motion_key=key))

        if self.op is None and key in ACTIONS:
            if key in ACTION_NEEDS_ARG:
                self.wait = ('achar', key)
                return ('more', None)

            return ('cmd', self._cmd(action=key))

        return self._abort()


##
# Editor state + Engine


class Mode(enum.Enum):
    NORMAL = enum.auto()
    INSERT = enum.auto()
    VISUAL = enum.auto()
    VISUAL_LINE = enum.auto()


# Synonym commands compile straight to op+motion / doubled op, like vim.
SYNONYMS = {
    'x': ('d', 'l', False),
    'X': ('d', 'h', False),
    'D': ('d', '$', False),
    'C': ('c', '$', False),
    's': ('c', 'l', False),
    'S': ('c', None, True),
    'Y': ('y', None, True),
}


class Engine:
    def __init__(self, buf: Buffer, text: str | None = None) -> None:
        self.buf: Buffer = buf if text is None else ListBuffer(text)
        self.cursor = Pos(0, 0)
        self.mode = Mode.NORMAL
        self.curswant = 0
        self.regs = Registers()
        self.last_ft: tuple | None = None       # (key, char) for ; ,
        self.visual_anchor: Pos | None = None
        self.parser = Parser()
        self.status = ''
        # dot-repeat: tap the raw key stream (vim's redo buffer)
        self._keys: list[str] = []
        self._last_change: list[str] = []
        self._rec_insert = False
        self._replaying = False
        self._no_record = False
        # undo: linear snapshot stack (vim has a full undo *tree*)
        self._undo: list[tuple] = []

    # public API

    def feed(self, key: str):
        if self.mode is Mode.INSERT:
            self._feed_insert(key)
        elif self.mode in (Mode.VISUAL, Mode.VISUAL_LINE):
            self._feed_visual(key)
        else:
            self._feed_normal(key)

    def send(self, keys: str):
        for k in keys:
            self.feed(k)

    def render(self) -> str:
        return '\n'.join(self.buf.get_line(r) for r in range(self.buf.line_count()))

    # normal mode

    def _feed_normal(self, key: str):
        if not self._replaying:
            self._keys.append(key)

        state, cmd = self.parser.feed(key)

        if state == 'more':
            return

        if state == 'abort':
            self._keys.clear()
            return

        self._no_record = False
        changed = self._exec(cmd)
        if self._replaying:
            return

        if changed and not self._no_record:
            if self.mode is Mode.INSERT:
                self._rec_insert = True  # keep taping until Esc
            else:
                self._last_change = self._keys.copy()
                self._keys.clear()

        else:
            self._keys.clear()

    # insert mode

    def _feed_insert(self, key: str):
        if self._rec_insert and not self._replaying:
            self._keys.append(key)

        buf, cur = self.buf, self.cursor

        if key == ESC:
            self.mode = Mode.NORMAL
            self.cursor = Pos(cur.row, max(0, cur.col - 1))
            self.curswant = self.cursor.col
            if self._rec_insert:
                self._last_change = self._keys.copy()
                self._keys.clear()
                self._rec_insert = False
            return

        if key in ('\r', '\n'):
            line = buf.get_line(cur.row)
            buf.set_line(cur.row, line[:cur.col])
            buf.insert_line(cur.row + 1, line[cur.col:])
            self.cursor = Pos(cur.row + 1, 0)
            return

        if key in BACKSPACES:
            if cur.col > 0:
                line = buf.get_line(cur.row)
                buf.set_line(cur.row, line[:cur.col - 1] + line[cur.col:])
                self.cursor = Pos(cur.row, cur.col - 1)

            elif cur.row > 0:
                prev = buf.get_line(cur.row - 1)
                buf.set_line(cur.row - 1, prev + buf.get_line(cur.row))
                buf.delete_line(cur.row)
                self.cursor = Pos(cur.row - 1, len(prev))

            return

        line = buf.get_line(cur.row)
        buf.set_line(cur.row, line[:cur.col] + key + line[cur.col:])
        self.cursor = Pos(cur.row, cur.col + 1)

    # visual mode (charwise + linewise)
    # Operators work on a Span exactly as in normal mode -- selections and operator-pending ranges unify. (Not
    # dot-recorded; vim approximates visual `.` by reapplying to a same-sized region.)

    def _feed_visual(self, key: str):
        state, cmd = self.parser.feed(key)

        if state == 'more':
            return

        if state == 'abort':
            if key == ESC:
                self._leave_visual()
            return

        # exits / toggles
        if cmd.action == 'v':
            self._leave_visual() if self.mode is Mode.VISUAL else self._set_visual(Mode.VISUAL)
            return

        if cmd.action == 'V':
            self._leave_visual() if self.mode is Mode.VISUAL_LINE else self._set_visual(Mode.VISUAL_LINE)
            return

        if cmd.action == 'o':
            self.visual_anchor, self.cursor = self.cursor, self.visual_anchor
            return

        # operator (or synonym) applies to the selection
        opkey = cmd.op

        if cmd.action in ('x', 'd'):
            opkey = 'd'
        elif cmd.action == 's':
            opkey = 'c'

        if cmd.action in SYNONYMS and opkey is None:
            opkey = SYNONYMS[cmd.action][0]

        if opkey:
            span = self._visual_span()
            self._leave_visual()
            self._apply_op(opkey, span, cmd.register)
            return

        # text object extends the selection
        if cmd.tobj:
            sp = textobj(self.buf, self.cursor, *cmd.tobj, cmd.count)
            if sp:
                self.visual_anchor = sp.start
                self.cursor = _clamp_col(self.buf, _retreat(self.buf, sp.end) or sp.end)
            return

        # motion moves the free end
        if cmd.motion_key:
            mr = self._eval_motion(cmd, op_pending=False)
            if mr:
                self._move_to(mr)

    def _set_visual(self, mode):
        self.mode = mode
        self.parser.visual = True

    def _leave_visual(self):
        self.mode = Mode.NORMAL
        self.visual_anchor = None
        self.parser.visual = False

    def _visual_span(self) -> Span:
        a, b = sorted((self.visual_anchor, self.cursor))
        if self.mode is Mode.VISUAL_LINE:
            return Span(Kind.LINEWISE, Pos(a.row, 0), Pos(b.row, 0))
        end = Pos(b.row, min(b.col + 1, _llen(self.buf, b.row)))  # incl. cursor char
        return Span(Kind.EXCLUSIVE, a, end)

    # command execution

    def _exec(self, cmd: Command) -> bool:
        """Run one parsed command. Returns True iff the buffer changed."""

        if cmd.action in SYNONYMS:
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
            r2 = min(r + cmd.count - 1, self.buf.line_count() - 1)
            return self._apply_op(cmd.op, Span(Kind.LINEWISE, Pos(r, 0), Pos(r2, 0)), cmd.register)

        if cmd.op and cmd.tobj:
            sp = textobj(self.buf, self.cursor, *cmd.tobj, cmd.count)
            if sp is None:
                return False
            return self._apply_op(cmd.op, sp, cmd.register)

        if cmd.op and cmd.motion_key:
            mkey = cmd.motion_key
            # vim's `cw` special case: on a non-blank, cw acts like ce
            if cmd.op == 'c' and mkey in 'wW' \
                    and _cls(_char(self.buf, self.cursor), mkey == 'W') != 0:
                mkey = 'e' if mkey == 'w' else 'E'
                cmd = Command(**{**cmd.__dict__, 'motion_key': mkey})
            mr = self._eval_motion(cmd, op_pending=True)
            if mr is None:
                return False  # motion failed: beep
            sp = resolve(self.buf, self.cursor, mr)
            if sp is None:
                return False
            return self._apply_op(cmd.op, sp, cmd.register)

        if cmd.motion_key:  # bare motion: move
            mr = self._eval_motion(cmd, op_pending=False)
            if mr:
                self._move_to(mr)
            return False

        return False

    # motion evaluation (the nv_cmds table, in miniature)

    def _eval_motion(self, cmd: Command, op_pending: bool) -> MotionResult | None:
        buf, p, n = self.buf, self.cursor, cmd.count
        k, arg = cmd.motion_key, cmd.motion_arg
        EX, IN, LI = Kind.EXCLUSIVE, Kind.INCLUSIVE, Kind.LINEWISE

        if k == 'h':
            t = Pos(p.row, max(0, p.col - n))
            return None if t == p else MotionResult(t, EX)

        if k == 'l':
            t = Pos(p.row, min(p.col + n, _llen(buf, p.row)))
            return None if t == p else MotionResult(t, EX)

        if k in ('j', 'k'):
            d = n if k == 'j' else -n
            t = Pos(max(0, min(p.row + d, buf.line_count() - 1)), p.col)
            return None if t.row == p.row else MotionResult(t, LI, keeps_curswant=True)

        if k == '0':
            return MotionResult(Pos(p.row, 0), EX)

        if k == '^':
            return MotionResult(Pos(p.row, _first_nonblank(buf, p.row)), EX)

        if k == '$':
            row = min(p.row + n - 1, buf.line_count() - 1)
            return MotionResult(Pos(row, max(0, _llen(buf, row) - 1)), IN, curswant_eol=True)

        if k in 'wW':
            return MotionResult(word_fwd(buf, p, n, k == 'W'), EX)

        if k in 'bB':
            return MotionResult(word_back(buf, p, n, k == 'B'), EX)

        if k in 'eE':
            return MotionResult(word_end(buf, p, n, k == 'E'), IN)

        if k == 'G':
            row = min(cmd.count - 1, buf.line_count() - 1) if cmd.has_count else buf.line_count() - 1
            return MotionResult(Pos(row, 0), LI, to_first_nonblank=True)

        if k == 'gg':
            row = min(cmd.count - 1, buf.line_count() - 1) if cmd.has_count else 0
            return MotionResult(Pos(row, 0), LI, to_first_nonblank=True)

        if k in MOTION_NEEDS_ARG:                         # f t F T
            fwd, till = k in 'ft', k in 'tT'
            t = find_char(buf, p, arg, n, fwd, till)
            if t is None:
                return None
            self.last_ft = (k, arg)
            return MotionResult(t, IN if fwd else EX)

        if k in (';', ','):
            if not self.last_ft:
                return None
            lk, ch = self.last_ft
            if k == ',':
                lk = {'f': 'F', 'F': 'f', 't': 'T', 'T': 't'}[lk]
            fwd, till = lk in 'ft', lk in 'tT'
            t = find_char(buf, p, ch, n, fwd, till, repeat=True)
            if t is None:
                return None
            return MotionResult(t, IN if fwd else EX)

        return None

    def _move_to(self, mr: MotionResult):
        buf, t = self.buf, mr.target
        if mr.kind is Kind.LINEWISE:
            if mr.to_first_nonblank:
                col = _first_nonblank(buf, t.row)
                self.curswant = col
            elif mr.keeps_curswant:
                col = min(self.curswant, max(0, _llen(buf, t.row) - 1))
            else:
                col = min(t.col, max(0, _llen(buf, t.row) - 1))
            self.cursor = Pos(t.row, col)
            return
        self.cursor = _clamp_col(buf, t)
        self.curswant = INF if mr.curswant_eol else self.cursor.col

    # operators

    def _apply_op(self, op: str, span: Span, reg: str | None) -> bool:
        if op != 'y':
            self._snapshot()

        if op == 'y':
            pieces, kind = self._extract(span)
            self.regs.set(reg or '"', RegValue(pieces, kind), is_yank=True)
            if span.kind is not Kind.LINEWISE:
                self.cursor = _clamp_col(self.buf, span.start)
            return False

        if op in '><':
            for r in range(span.start.row, span.end.row + 1):
                line = self.buf.get_line(r)
                if op == '>':
                    if line:                              # vim skips empty lines
                        self.buf.set_line(r, ' ' * SHIFTWIDTH + line)
                else:
                    lead = len(line) - len(line.lstrip(' '))
                    self.buf.set_line(r, line[min(SHIFTWIDTH, lead):])
            self.cursor = Pos(span.start.row, _first_nonblank(self.buf, span.start.row))
            return True

        if op == 'd':
            pieces, kind = self._extract(span)
            self.regs.set(reg or '"', RegValue(pieces, kind), is_yank=False)
            self._delete_span(span)
            return True

        if op == 'c':
            pieces, kind = self._extract(span)
            self.regs.set(reg or '"', RegValue(pieces, kind), is_yank=False)
            if span.kind is Kind.LINEWISE:
                for _ in range(span.end.row - span.start.row + 1):
                    self.buf.delete_line(span.start.row)
                self.buf.insert_line(span.start.row, '')
                self.cursor = Pos(span.start.row, 0)
            else:
                self._delete_charwise(span)
                self.cursor = Pos(span.start.row, min(span.start.col, _llen(self.buf, span.start.row)))
            self.mode = Mode.INSERT
            return True

        return False

    def _extract(self, span: Span):
        buf = self.buf
        if span.kind is Kind.LINEWISE:
            return ([buf.get_line(r) for r in range(span.start.row, span.end.row + 1)], Kind.LINEWISE)
        a, b = span.start, span.end
        if a.row == b.row:
            return ([buf.get_line(a.row)[a.col:b.col]], Kind.EXCLUSIVE)
        pieces = [buf.get_line(a.row)[a.col:]]
        pieces += [buf.get_line(r) for r in range(a.row + 1, b.row)]
        pieces.append(buf.get_line(b.row)[:b.col])
        return (pieces, Kind.EXCLUSIVE)

    def _delete_span(self, span: Span):
        if span.kind is Kind.LINEWISE:
            for _ in range(span.end.row - span.start.row + 1):
                self.buf.delete_line(span.start.row)
            if self.buf.line_count() == 0:
                self.buf.insert_line(0, '')  # a buffer is never empty
            row = min(span.start.row, self.buf.line_count() - 1)
            self.cursor = Pos(row, _first_nonblank(self.buf, row))
        else:
            self._delete_charwise(span)
            self.cursor = _clamp_col(self.buf, span.start)
        self.curswant = self.cursor.col

    def _delete_charwise(self, span: Span):
        buf, a, b = self.buf, span.start, span.end
        if a.row == b.row:
            line = buf.get_line(a.row)
            buf.set_line(a.row, line[:a.col] + line[b.col:])
        else:
            merged = buf.get_line(a.row)[:a.col] + buf.get_line(b.row)[b.col:]
            buf.set_line(a.row, merged)
            for _ in range(b.row - a.row):
                buf.delete_line(a.row + 1)

    # simple actions

    def _exec_action(self, cmd: Command) -> bool:
        buf, cur, n = self.buf, self.cursor, cmd.count
        a = cmd.action

        if a in ('p', 'P'):
            rv = self.regs.get(cmd.register or '"')
            if not rv:
                return False
            self._snapshot()
            self._put(rv, n, after=(a == 'p'))
            return True

        if a in 'iIaAoO':
            self._snapshot()
            line = buf.get_line(cur.row)
            if a == 'i':
                pass
            elif a == 'I':
                self.cursor = Pos(cur.row, _first_nonblank(buf, cur.row))
            elif a == 'a':
                self.cursor = Pos(cur.row, cur.col + 1 if line else 0)
            elif a == 'A':
                self.cursor = Pos(cur.row, len(line))
            elif a == 'o':
                buf.insert_line(cur.row + 1, '')
                self.cursor = Pos(cur.row + 1, 0)
            elif a == 'O':
                buf.insert_line(cur.row, '')
                self.cursor = Pos(cur.row, 0)
            self.mode = Mode.INSERT
            return True

        if a == 'r':
            line = buf.get_line(cur.row)
            if cur.col + n > len(line):
                return False  # vim fails, no partial
            self._snapshot()
            buf.set_line(cur.row, line[:cur.col] + cmd.action_arg * n + line[cur.col + n:])
            self.cursor = Pos(cur.row, cur.col + n - 1)
            return True

        if a == 'J':
            joins = max(n, 2) - 1
            if cur.row + joins > buf.line_count() - 1:
                joins = buf.line_count() - 1 - cur.row
            if joins <= 0:
                return False
            self._snapshot()
            for _ in range(joins):
                first = buf.get_line(cur.row).rstrip()
                nxt = buf.get_line(cur.row + 1).lstrip()
                sep = '' if (not nxt or not first) else ' '
                self.cursor = Pos(cur.row, len(first))
                buf.set_line(cur.row, first + sep + nxt)
                buf.delete_line(cur.row + 1)
            return True

        if a == 'u':
            self._no_record = True
            if self._undo:
                lines, pos = self._undo.pop()
                _restore_lines(buf, lines)
                self.cursor = _clamp_col(buf, Pos(min(pos.row, buf.line_count() - 1), pos.col))
            return True

        if a == '.':
            self._no_record = True
            if self._last_change and not self._replaying:
                seq = list(self._last_change)
                self._keys.clear()
                self._replaying = True
                try:
                    for k in seq:  # (vim also substitutes a new
                        self.feed(k)  #  count into the replay; omitted)
                finally:
                    self._replaying = False
                    self._no_record = True  # nested feeds reset the flag
            return True

        if a in ('v', 'V'):
            self.visual_anchor = self.cursor
            self._set_visual(Mode.VISUAL if a == 'v' else Mode.VISUAL_LINE)
            self.parser.reset()
            return False

        return False

    def _put(self, rv: RegValue, count: int, after: bool):
        buf, cur = self.buf, self.cursor
        if rv.kind is Kind.LINEWISE:
            row = cur.row + 1 if after else cur.row
            lines = rv.pieces * count
            for i, ln in enumerate(lines):
                buf.insert_line(row + i, ln)
            self.cursor = Pos(row, _first_nonblank(buf, row))
            return

        pieces = _pieces_repeat(rv.pieces, count)
        line = buf.get_line(cur.row)
        col = cur.col + 1 if (after and line) else cur.col
        left, right = line[:col], line[col:]

        if len(pieces) == 1:
            buf.set_line(cur.row, left + pieces[0] + right)
            self.cursor = Pos(cur.row, max(col, col + len(pieces[0]) - 1))

        else:
            buf.set_line(cur.row, left + pieces[0])
            for i, mid in enumerate(pieces[1:-1], start=1):
                buf.insert_line(cur.row + i, mid)
            last_row = cur.row + len(pieces) - 1
            buf.insert_line(last_row, pieces[-1] + right)
            self.cursor = Pos(last_row, max(0, len(pieces[-1]) - 1))

    # undo plumbing

    # One snapshot per change *command*; a c-op's insert phase edits the buffer directly without snapshotting, so
    # `cwfoo<Esc>` is one undo unit, matching vim. (vim keeps a full undo tree; we keep a linear stack.)
    def _snapshot(self):
        lines = [self.buf.get_line(r) for r in range(self.buf.line_count())]
        self._undo.append((lines, self.cursor))
        if len(self._undo) > 200:
            self._undo.pop(0)


def _restore_lines(buf: Buffer, lines: list):
    while buf.line_count() > 0:
        buf.delete_line(0)
    for i, ln in enumerate(lines):
        buf.insert_line(i, ln)


##


if __name__ == '__main__':
    eng = Engine(ListBuffer('The quick brown fox\njumps over\nthe lazy dog'))
    for keys in ['wdw', 'j', 'dd', 'p', 'ciwHOP' + ESC, 'u', '.']:
        eng.send(keys)
        print(f'after {keys!r:14}: {eng.render()!r}  cursor={eng.cursor}')
