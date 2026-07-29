"""
TODO:
 - max buf size
 - max recursion depth
 - mark start pos of tokens, currently returning end
"""
import dataclasses as dc
import json
import typing as ta

from .... import lang
from ....funcs.genmachine import GenMachine
from .errors import JsonStreamError
from .tokens import CONST_IDENT_VALUES
from .tokens import CONTROL_TOKENS
from .tokens import EXPANDED_SPACE_CHARS
from .tokens import MAX_CONST_IDENT_LEN
from .tokens import NUMBER_PAT
from .tokens import SPACE_CHARS
from .tokens import Position
from .tokens import ScalarValue
from .tokens import Token
from .tokens import TokenKind


if ta.TYPE_CHECKING:
    import unicodedata
else:
    unicodedata = lang.proxy_import('unicodedata')


##


_CONST_IDENTS_BY_FIRST_CHAR: ta.Mapping[str, str] = {
    s[0]: s
    for s in CONST_IDENT_VALUES
    if not s.startswith('-')
}

_CONTROL_TOKENS_GET = CONTROL_TOKENS.get
_NUMBER_PAT_MATCH = NUMBER_PAT.match


##


@dc.dataclass()
class JsonStreamLexError(JsonStreamError):
    message: str

    pos: Position


class JsonStreamLexer(GenMachine[str, Token]):
    """
    Input is held in a single buffer `_s` with consumption index `_i` - received chunks (of any size, including single
    chars) replace the buffer once it is fully consumed. Tokens spanning chunk boundaries accumulate their raw text in
    scanner-local part lists.

    Position is tracked as the absolute offset of the buffer start plus the current line and the absolute offset of its
    first char - columns are derived only when a `Position` is built, and line tracking is updated in bulk when
    consuming ranges which may contain newlines.
    """

    def __init__(
            self,
            *,
            include_raw: bool = False,

            allow_extended_space: bool = False,
            include_space: bool = False,

            allow_comments: bool = False,
            include_comments: bool = False,

            allow_single_quotes: bool = False,
            string_literal_parser: ta.Callable[[str], str] | None = None,

            allow_extended_number_literals: bool = False,
            number_literal_parser: ta.Callable[[str], ta.Any] | None = None,

            allow_extended_idents: bool = False,
    ) -> None:
        self._include_raw = include_raw

        self._allow_extended_space = allow_extended_space
        self._include_space = include_space

        self._allow_comments = allow_comments
        self._include_comments = include_comments

        self._allow_single_quotes = allow_single_quotes
        if string_literal_parser is None:
            if allow_single_quotes:
                # The default json.loads will always reject single-quoted raw literals.
                raise TypeError('allow_single_quotes requires a string_literal_parser')
            string_literal_parser = json.loads  # noqa
        self._string_literal_parser = string_literal_parser

        self._allow_extended_number_literals = allow_extended_number_literals
        self._number_literal_parser = number_literal_parser

        self._allow_extended_idents = allow_extended_idents

        self._space_chars = SPACE_CHARS + (EXPANDED_SPACE_CHARS if allow_extended_space else '')
        # Bulk number scanning requires standard literals - NUMBER_PAT does not describe the extended forms.
        self._bulk_numbers = not allow_extended_number_literals and number_literal_parser is None

        self._s = ''
        self._i = 0
        self._eof = False

        self._base_ofs = 0
        self._line = 1
        self._line_start = 0

        super().__init__(self._do_main())

    @property
    def pos(self) -> Position:
        o = self._base_ofs + self._i
        return Position(
            o,
            self._line,
            o - self._line_start,
        )

    def _consume_to(self, j: int) -> None:
        """Advances `_i` to buffer index `j`, updating line tracking for any newlines in the consumed range."""

        if (np := self._s.rfind('\n', self._i, j)) >= 0:
            self._line += self._s.count('\n', self._i, j)
            self._line_start = self._base_ofs + np + 1
        self._i = j

    def _more(self):
        """
        Suspends for the next input chunk mid-token, returning False once EOF has been signalled by an empty chunk.
        Callers must have fully consumed the buffer. Closing the machine mid-token is an error.
        """

        if self._eof:
            return False

        try:
            cs = yield None
        except GeneratorExit:
            self._raise('Unexpected end of input')

        if not cs:
            self._eof = True
            return False

        self._base_ofs += len(self._s)
        self._s = cs
        self._i = 0
        return True

    def _read_chars(self, n: int):
        """Consumes and returns up to `n` chars, suspending as needed - fewer are returned only at EOF."""

        parts: list[str] = []
        need = n
        while need > 0:
            s = self._s
            i = self._i
            if i >= len(s):
                if not (yield from self._more()):
                    break
                continue

            j = min(len(s), i + need)
            parts.append(s[i:j])
            self._consume_to(j)
            need -= j - i

        return ''.join(parts)

    def _make_tok(
            self,
            kind: TokenKind,
            value: ScalarValue,
            raw: str | None,
            pos: Position,
    ) -> ta.Sequence[Token]:
        tok = Token(
            kind,
            value,
            raw if self._include_raw else None,
            pos,
        )
        return (tok,)

    def _raise(self, msg: str, src: Exception | None = None) -> ta.NoReturn:
        raise JsonStreamLexError(msg, self.pos) from src

    def _scan(self, toks: list[Token]) -> str | None:
        """
        Bulk-scans the buffer, appending any tokens completed within it to `toks`. Returns a handoff char - left
        unconsumed at `_i` - which the caller must dispatch to the suspendable scanners, or None if the buffer was
        consumed without one. Tokens which may straddle the buffer end are always handed off - only tokens provably
        complete within the buffer are emitted here.

        NOTE: `_do_main`'s single-char fast path deliberately duplicates the space and control token handling here -
        changes to either must be mirrored in the other.
        """

        s = self._s
        p = self._i
        sl = len(s)
        if p >= sl:
            return None

        base = self._base_ofs
        line = self._line
        line_start = self._line_start

        include_raw = self._include_raw
        include_space = self._include_space
        space_chars = self._space_chars
        bulk_numbers = self._bulk_numbers
        ext_idents = self._allow_extended_idents
        single_quotes = self._allow_single_quotes
        str_parser = self._string_literal_parser
        ctrl_get = _CONTROL_TOKENS_GET
        num_match = _NUMBER_PAT_MATCH

        try:
            while p < sl:
                c = s[p]

                if c in space_chars:
                    if include_space:
                        p += 1
                        o = base + p
                        if c == '\n':
                            line += 1
                            line_start = o
                        toks.append(Token(
                            'SPACE',
                            c,
                            c if include_raw else None,
                            Position(o, line, o - line_start),
                        ))
                        continue

                    q = p + 1
                    while q < sl and s[q] in space_chars:
                        q += 1
                    if (np := s.rfind('\n', p, q)) >= 0:
                        line += s.count('\n', p, q)
                        line_start = base + np + 1
                    p = q
                    continue

                if (k := ctrl_get(c)) is not None:
                    p += 1
                    o = base + p
                    toks.append(Token(
                        k,
                        c,
                        c if include_raw else None,
                        Position(o, line, o - line_start),
                    ))
                    continue

                if c == '"' or (single_quotes and c == "'"):
                    e = p + 1
                    while (qp := s.find(c, e)) >= 0:
                        b = qp - 1
                        while b > p and s[b] == '\\':
                            b -= 1
                        # Quote is escaped only if preceded by an odd number of backslashes
                        if (qp - 1 - b) % 2 == 0:
                            break
                        e = qp + 1

                    if qp >= 0:
                        try:
                            sv = str_parser(s[p:qp + 1])
                        except Exception:  # noqa
                            # Errors must surface through the suspendable scanner so that any already-batched tokens
                            # are flushed to the consumer first - hand off to it to rescan and re-raise.
                            pass
                        else:
                            o = base + p + 1
                            pos = Position(o, line, o - line_start)
                            raw = s[p:qp + 1] if include_raw else None
                            if (np := s.rfind('\n', p, qp + 1)) >= 0:
                                line += s.count('\n', p, qp + 1)
                                line_start = base + np + 1
                            p = qp + 1

                            toks.append(Token(
                                'STRING',
                                sv,
                                raw,
                                pos,
                            ))
                            continue

                    # No closing quote in this buffer (or a bad literal) - hand off.

                elif bulk_numbers and c in '0123456789-':
                    m = num_match(s, p)
                    # A match reaching the buffer end may continue in the next chunk, and one followed by another
                    # number-ish char must be greedily consumed (and rejected) by the suspendable scanner as a whole.
                    if m is not None and (e := m.end()) < sl and s[e] not in '0123456789.eE+-':
                        o = base + p + 1
                        raw = s[p:e]
                        toks.append(Token(
                            'NUMBER',
                            float(raw) if m.lastindex else int(raw),
                            raw if include_raw else None,
                            Position(o, line, o - line_start),
                        ))
                        p = e
                        continue

                elif not ext_idents and (ci := _CONST_IDENTS_BY_FIRST_CHAR.get(c)) is not None:
                    # Const idents are prefix-free, so a full match is unambiguous even at the buffer end.
                    if s.startswith(ci, p):
                        o = base + p + 1
                        toks.append(Token(
                            'IDENT',
                            ci,
                            ci if include_raw else None,
                            Position(o, line, o - line_start),
                        ))
                        p += len(ci)
                        continue

                return c

            return None

        finally:
            self._i = p
            self._line = line
            self._line_start = line_start

    def _do_main(self):
        toks: list[Token] = []

        while True:
            s = self._s
            i = self._i

            # Fast path for single-char buffers - that is, per-char feeding, where _scan's setup cost dwarfs its work.
            # On one char _scan can only ever skip a space, emit a control token, or hand off, so this DELIBERATELY
            # DUPLICATES its space and control handling (keep the two in sync!) and lets everything else fall through
            # to the shared dispatch below.
            c: str | None
            if i + 1 == len(s):
                cc = s[i]
                c = cc
                if cc in self._space_chars:
                    self._i = i + 1
                    if cc == '\n':
                        self._line += 1
                        self._line_start = self._base_ofs + self._i
                    if self._include_space:
                        o = self._base_ofs + self._i
                        yield self._make_tok('SPACE', cc, cc, Position(o, self._line, o - self._line_start))
                    c = None

                elif (k := _CONTROL_TOKENS_GET(cc)) is not None:
                    self._i = i + 1
                    o = self._base_ofs + self._i
                    yield self._make_tok(k, cc, cc, Position(o, self._line, o - self._line_start))
                    c = None

            else:
                c = self._scan(toks)

                # Any batched tokens must be flushed before suspending for input or switching to another scanner.
                if toks:
                    yield toks
                    toks = []

            if c is None:
                # Inline of _recv - this is hit once per chunk, which under per-char feeding means once per char.
                if self._eof:
                    return None
                cs = yield None
                if not cs:
                    self._eof = True
                    return None
                self._base_ofs += len(self._s)
                self._s = cs
                self._i = 0
                continue

            if c == '"' or (self._allow_single_quotes and c == "'"):
                return self._do_string(c)

            if c in '0123456789-' or (self._allow_extended_number_literals and c in '.+'):
                return self._do_number()

            if self._allow_comments and c == '/':
                return self._do_comment()

            if self._allow_extended_idents:
                return self._do_extended_ident()

            if c in 'tfnIN':
                return self._do_const()

            self._i += 1
            self._raise(f'Unexpected character: {c}')

    def _do_string(self, q: str):
        o = self._base_ofs + self._i + 1
        pos = Position(o, self._line, o - self._line_start)

        parts: list[str] = []
        bs_count = 0
        skip = 1  # the opening quote, on the first pass only

        while True:
            s = self._s
            sl = len(s)
            j = self._i + skip
            skip = 0
            end = -1

            while j < sl:
                qp = s.find(q, j)
                sp = s.find('\\', j)

                if sp >= 0 and (qp < 0 or sp < qp):
                    # A backslash run comes first
                    if sp > j:
                        bs_count = 0
                    k = sp + 1
                    while k < sl and s[k] == '\\':
                        k += 1
                    bs_count += k - sp
                    j = k

                elif qp >= 0:
                    # A quote comes first - it terminates only if preceded by an even number of backslashes
                    if qp > j:
                        bs_count = 0
                    if not bs_count % 2:
                        end = qp
                        break
                    bs_count = 0
                    j = qp + 1

                else:
                    # Neither present - the rest is plain content
                    bs_count = 0
                    j = sl

            if end >= 0:
                piece = s[self._i:end + 1]
                self._consume_to(end + 1)
                raw = ''.join([*parts, piece]) if parts else piece

                try:
                    sv = self._string_literal_parser(raw)
                except json.JSONDecodeError as e:
                    self._raise(f'Invalid string literal: {raw!r}', e)

                yield self._make_tok('STRING', sv, raw, pos)

                return self._do_main()

            parts.append(s[self._i:])
            self._consume_to(sl)

            # Inline of _more - this is the hottest refill point, hit once per char under per-char feeding
            if self._eof:
                self._raise(f'Unterminated string literal: {"".join(parts)}')

            try:
                cs = yield None
            except GeneratorExit:
                self._raise('Unexpected end of input')

            if not cs:
                self._eof = True
                self._raise(f'Unterminated string literal: {"".join(parts)}')

            self._base_ofs += sl
            self._s = cs
            self._i = 0

    def _do_number(self):
        o = self._base_ofs + self._i + 1
        pos = Position(o, self._line, o - self._line_start)

        parts: list[str] = []
        while True:
            s = self._s
            sl = len(s)
            i = j = self._i
            while j < sl and (
                    s[j] in '0123456789.eE+-' or
                    (self._allow_extended_number_literals and s[j] in 'xXabcdefABCDEF')
            ):
                j += 1

            if j > i:
                parts.append(s[i:j])
                self._i = j  # number chars are never newlines

            if j < sl:
                break

            if not (yield from self._more()):
                break

        raw = ''.join(parts)

        #

        if self._allow_extended_number_literals:
            p = 1 if raw[0] in '+-' else 0
            if (len(raw) - p) > 1 and raw[p] == '0' and raw[p + 1] in '0123456789':
                self._raise('Invalid number literal')

        if raw == '-' or (self._allow_extended_number_literals and raw == '+'):
            nc = self._s[self._i] if self._i < len(self._s) else ''
            for svs in [
                'Infinity',
                *(['NaN'] if self._allow_extended_number_literals else []),
            ]:
                if nc != svs[0]:
                    continue

                rest = yield from self._read_chars(len(svs))
                raw += rest

                if raw[1:] != svs:
                    self._raise(f'Invalid number format: {raw}')

                if raw[0] == '+':
                    raw = raw[1:]

                yield self._make_tok('IDENT', raw, raw, pos)

                return self._do_main()

        #

        nv: ta.Any

        if (np := self._number_literal_parser) is not None:
            nv = np(raw)

        else:
            if (m := NUMBER_PAT.fullmatch(raw)) is None:
                self._raise(f'Invalid number format: {raw}')

            if m.lastindex:
                nv = float(raw)
            else:
                nv = int(raw)

        yield self._make_tok('NUMBER', nv, raw, pos)

        return self._do_main()

    def _do_const(self):
        o = self._base_ofs + self._i + 1
        pos = Position(o, self._line, o - self._line_start)

        raw = ''
        while True:
            if (i := self._i) >= len(self._s):
                if not (yield from self._more()):
                    self._raise('Unexpected end of input')
                continue

            raw += self._s[i]
            self._consume_to(i + 1)

            if raw in CONST_IDENT_VALUES:
                break

            if len(raw) > MAX_CONST_IDENT_LEN:
                self._raise(f'Invalid literal: {raw}')

        yield self._make_tok('IDENT', raw, raw, pos)

        return self._do_main()

    def _do_unicode_escape(self):
        if (yield from self._read_chars(1)) != 'u':
            self._raise('Illegal identifier escape')

        ux = yield from self._read_chars(4)
        if len(ux) != 4 or any(c not in '0123456789abcdefABCDEF' for c in ux):
            self._raise('Illegal identifier escape')

        return chr(int(ux, 16))

    def _do_extended_ident(self):
        parts: list[str] = []

        c = self._s[self._i]
        if c == '\\':
            self._i += 1
            c = yield from self._do_unicode_escape()
        elif not (c in '$_' or unicodedata.category(c).startswith('L')):
            self._raise('Illegal identifier start')
        else:
            self._i += 1
        parts.append(c)

        pos = self.pos

        while True:
            if (i := self._i) >= len(self._s):
                if not (yield from self._more()):
                    break
                continue

            c = self._s[i]

            if c == '\\':
                self._i = i + 1
                c = yield from self._do_unicode_escape()
                parts.append(c)
                continue

            if c not in '$_\u200C\u200D':
                uc = unicodedata.category(c)
                if not (uc.startswith(('L', 'M', 'N')) or uc == 'Pc'):
                    break

            parts.append(c)
            self._i = i + 1

        raw = ''.join(parts)

        yield self._make_tok('IDENT', raw, raw, pos)

        return self._do_main()

    def _do_comment(self):
        o = self._base_ofs + self._i + 1
        pos = Position(o, self._line, o - self._line_start)
        self._i += 1  # the opening '/'

        include = self._include_comments
        parts: list[str] = []

        oc = yield from self._read_chars(1)
        if oc == '/':
            terminated = False
            while True:
                s = self._s
                i = self._i
                if i >= len(s):
                    if not (yield from self._more()):
                        break
                    continue

                if (nl := s.find('\n', i)) >= 0:
                    if include:
                        parts.append(s[i:nl])
                    self._consume_to(nl + 1)
                    terminated = True
                    break

                if include:
                    parts.append(s[i:])
                self._consume_to(len(s))

            if include:
                cmt = ''.join(parts)
                raw = f'//{cmt}\n' if self._include_raw else None
                yield self._make_tok('COMMENT', cmt, raw, pos)

            if not terminated:
                return None

            return self._do_main()

        elif oc == '*':
            star = False  # a '*' held back at a buffer boundary
            while True:
                s = self._s
                i = self._i
                sl = len(s)
                if i >= sl:
                    if not (yield from self._more()):
                        self._raise('Unexpected end of input')
                    continue

                if star:
                    if s[i] == '/':
                        self._i = i + 1
                        break
                    if include:
                        parts.append('*')
                    star = False
                    continue

                if (fp := s.find('*/', i)) >= 0:
                    if include:
                        parts.append(s[i:fp])
                    self._consume_to(fp + 2)
                    break

                e = sl
                if s[sl - 1] == '*':
                    e = sl - 1
                    star = True
                if include:
                    parts.append(s[i:e])
                self._consume_to(sl)

            if include:
                cmt = ''.join(parts)
                raw = f'/*{cmt}*/' if self._include_raw else None
                yield self._make_tok('COMMENT', cmt, raw, pos)

            return self._do_main()

        else:
            self._raise(f'Unexpected character after comment start: {oc}')
