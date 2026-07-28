"""
TODO:
 - max buf size
 - max recursion depth
 - mark start pos of tokens, currently returning end
"""
import dataclasses as dc
import io
import json
import typing as ta

from .... import check
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


##


@dc.dataclass()
class JsonStreamLexError(JsonStreamError):
    message: str

    pos: Position


class JsonStreamLexer(GenMachine[str, Token]):
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

        self._char_in_str: str | None = None
        self._char_in_str_len: int = 0
        self._char_in_str_pos: int = 0

        self._ofs = 0
        self._line = 1
        self._col = 0

        self._buf = io.StringIO()

        super().__init__(self._do_main())

    @property
    def pos(self) -> Position:
        return Position(
            self._ofs,
            self._line,
            self._col,
        )

    def _advance_pos(self, c: str) -> str:
        if not c:
            return c

        if len(c) != 1:
            raise JsonStreamError(c)

        self._ofs += 1

        if c == '\n':
            self._line += 1
            self._col = 0
        else:
            self._col += 1

        return c

    def _yield_char_in(self, c: str) -> str:
        if self._char_in_str is not None:
            raise JsonStreamError

        if (cl := len(c)) > 1:
            self._char_in_str = c
            self._char_in_str_len = cl
            self._char_in_str_pos = 1
            c = c[0]

        self._advance_pos(c)

        return c

    def _store_char_in(self, s: str) -> None:
        if self._char_in_str is not None:
            raise JsonStreamError

        self._char_in_str = s
        self._char_in_str_len = len(s)
        self._char_in_str_pos = 0

    def _str_char_in(self) -> str | None:
        if (s := self._char_in_str) is None:
            return None

        if (p := self._char_in_str_pos) >= self._char_in_str_len:
            self._char_in_str = None
            return None

        c = s[p]
        self._char_in_str_pos += 1
        return self._advance_pos(c)

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

    def _flip_buf(self) -> str:
        raw = self._buf.getvalue()
        self._buf.seek(0)
        self._buf.truncate()
        return raw

    def _raise(self, msg: str, src: Exception | None = None) -> ta.NoReturn:
        raise JsonStreamLexError(msg, self.pos) from src

    def _scan_chunk(self, toks: list[Token]) -> str | None:
        """
        Bulk-scans the stored input chunk, appending any tokens completed within it to `toks`. Returns a handoff char -
        already consumed and position-advanced, exactly as if read via `_str_char_in` - which the caller must dispatch
        to the per-char scanners, or None if the chunk was consumed without one. Tokens which may straddle the chunk
        boundary are always handed off - only tokens provably complete within the chunk are emitted here.
        """

        if (s := self._char_in_str) is None:
            return None

        p = self._char_in_str_pos
        sl = self._char_in_str_len

        ofs = self._ofs
        line = self._line
        col = self._col

        include_raw = self._include_raw
        include_space = self._include_space
        space_chars = self._space_chars
        bulk_numbers = self._bulk_numbers
        ext_idents = self._allow_extended_idents
        single_quotes = self._allow_single_quotes
        str_parser = self._string_literal_parser
        ctrl_get = CONTROL_TOKENS.get
        num_match = NUMBER_PAT.match

        try:
            while p < sl:
                c = s[p]

                if c in space_chars:
                    if include_space:
                        p += 1
                        ofs += 1
                        if c == '\n':
                            line += 1
                            col = 0
                        else:
                            col += 1
                        toks.append(Token(
                            'SPACE',
                            c,
                            c if include_raw else None,
                            Position(ofs, line, col),
                        ))
                        continue

                    q = p + 1
                    while q < sl and s[q] in space_chars:
                        q += 1
                    ofs += q - p
                    if (np := s.rfind('\n', p, q)) >= 0:
                        line += s.count('\n', p, q)
                        col = q - np - 1
                    else:
                        col += q - p
                    p = q
                    continue

                if (k := ctrl_get(c)) is not None:
                    p += 1
                    ofs += 1
                    col += 1
                    toks.append(Token(
                        k,
                        c,
                        c if include_raw else None,
                        Position(ofs, line, col),
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
                            # Errors must surface through the per-char scanner so that any already-batched tokens are
                            # flushed to the consumer first - hand off to it to rescan and re-raise.
                            pass
                        else:
                            pos = Position(ofs + 1, line, col + 1)
                            raw = s[p:qp + 1] if include_raw else None
                            tl = qp + 1 - p
                            ofs += tl
                            if (np := s.rfind('\n', p, qp + 1)) >= 0:
                                line += s.count('\n', p, qp + 1)
                                col = qp - np
                            else:
                                col += tl
                            p = qp + 1

                            toks.append(Token(
                                'STRING',
                                sv,
                                raw,
                                pos,
                            ))
                            continue

                    # No closing quote in this chunk (or a bad literal) - hand off to the suspendable scanner.

                elif bulk_numbers and c in '0123456789-':
                    m = num_match(s, p)
                    # A match reaching the chunk end may continue in the next chunk, and one followed by another
                    # number-ish char must be greedily consumed (and rejected) by the per-char scanner as a whole.
                    if m is not None and (e := m.end()) < sl and s[e] not in '0123456789.eE+-':
                        raw = s[p:e]
                        toks.append(Token(
                            'NUMBER',
                            float(raw) if m.lastindex else int(raw),
                            raw if include_raw else None,
                            Position(ofs + 1, line, col + 1),
                        ))
                        tl = e - p
                        ofs += tl
                        col += tl
                        p = e
                        continue

                elif not ext_idents and (ci := _CONST_IDENTS_BY_FIRST_CHAR.get(c)) is not None:
                    # Const idents are prefix-free, so a full match is unambiguous even at the chunk end.
                    if s.startswith(ci, p):
                        toks.append(Token(
                            'IDENT',
                            ci,
                            ci if include_raw else None,
                            Position(ofs + 1, line, col + 1),
                        ))
                        tl = len(ci)
                        ofs += tl
                        col += tl
                        p += tl
                        continue

                p += 1
                ofs += 1
                col += 1
                return c

            return None

        finally:
            self._char_in_str_pos = p
            self._ofs = ofs
            self._line = line
            self._col = col

    def _do_main(self, peek: str | None = None):
        toks: list[Token] = []

        while True:
            c: str | None
            if peek is not None:
                c = peek
                peek = None
            else:
                c = self._scan_chunk(toks)

                # Any batched tokens must be flushed before suspending for input or switching to a per-char scanner.
                if toks:
                    yield toks
                    toks = []

                if c is None and (c := self._str_char_in()) is None:
                    cs = yield None
                    if cs and len(cs) > 1:
                        self._store_char_in(cs)
                        continue
                    c = self._advance_pos(cs)

            if not c:
                return None

            if c in self._space_chars:
                if self._include_space:
                    yield self._make_tok('SPACE', c, c, self.pos)
                continue

            if c in CONTROL_TOKENS:
                yield self._make_tok(CONTROL_TOKENS[c], c, c, self.pos)
                continue

            if c == '"' or (self._allow_single_quotes and c == "'"):
                return self._do_string(c)

            if c in '0123456789-' or (self._allow_extended_number_literals and c in '.+'):
                return self._do_number(c)

            if self._allow_comments and c == '/':
                return self._do_comment()

            if self._allow_extended_idents:
                return self._do_extended_ident(c)

            if c in 'tfnIN':
                return self._do_const(c)

            self._raise(f'Unexpected character: {c}')

    def _do_string(self, q: str):
        check.state(self._buf.tell() == 0)
        self._buf.write(q)

        pos = self.pos

        #

        buf = self._buf

        char_in_str = self._char_in_str
        char_in_str_len = self._char_in_str_len
        char_in_str_pos = self._char_in_str_pos
        ofs = self._ofs
        line = self._line
        col = self._col

        def restore_state():
            self._char_in_str = char_in_str
            self._char_in_str_len = char_in_str_len
            self._char_in_str_pos = char_in_str_pos
            self._ofs = ofs
            self._line = line
            self._col = col

        bs_count = 0  # count of consecutive backslashes immediately preceding the current position

        while True:
            c: str | None = None

            while True:
                if char_in_str is not None:
                    if char_in_str_pos >= char_in_str_len:
                        char_in_str = None
                        continue

                    skip_to = char_in_str_len
                    if (qp := char_in_str.find(q, char_in_str_pos)) >= 0 and qp < skip_to:
                        skip_to = qp
                    if (sp := char_in_str.find('\\', char_in_str_pos)) >= 0 and sp < skip_to:
                        skip_to = sp

                    if skip_to != char_in_str_pos:
                        ofs += skip_to - char_in_str_pos
                        if (np := char_in_str.rfind('\n', char_in_str_pos, skip_to)) >= 0:
                            line += char_in_str.count('\n', char_in_str_pos, skip_to)
                            col = skip_to - np - 1
                        else:
                            col += skip_to - char_in_str_pos
                        buf.write(char_in_str[char_in_str_pos:skip_to])
                        bs_count = 0  # the skipped range contains no backslashes

                        if skip_to >= char_in_str_len:
                            char_in_str = None
                            continue
                        char_in_str_pos = skip_to

                    c = char_in_str[char_in_str_pos]
                    char_in_str_pos += 1

                if c is None:
                    try:
                        c = (yield None)
                    except GeneratorExit:
                        restore_state()
                        self._raise('Unexpected end of input')

                    if len(c) > 1:
                        char_in_str = c
                        char_in_str_len = len(char_in_str)
                        char_in_str_pos = 0
                        c = None
                        continue

                if c is None:
                    raise JsonStreamError

                if c and len(c) != 1:
                    raise JsonStreamError(c)

                break

            if not c:
                restore_state()
                self._raise(f'Unterminated string literal: {buf.getvalue()}')

            ofs += 1

            if c == '\n':
                line += 1
                col = 0
            else:
                col += 1

            buf.write(c)

            if c == q:
                # Quote is escaped only if preceded by an odd number of backslashes
                if not bs_count % 2:
                    break
                bs_count = 0
            elif c == '\\':
                bs_count += 1
            else:
                bs_count = 0

        restore_state()

        #

        raw = self._flip_buf()
        try:
            sv = self._string_literal_parser(raw)
        except json.JSONDecodeError as e:
            self._raise(f'Invalid string literal: {raw!r}', e)

        yield self._make_tok('STRING', sv, raw, pos)

        return self._do_main()

    def _do_number(self, c: str):
        check.state(self._buf.tell() == 0)
        self._buf.write(c)

        pos = self.pos

        while True:
            try:
                if (c := self._str_char_in()) is None:  # type: ignore[assignment]
                    c = self._yield_char_in((yield None))  # noqa
            except GeneratorExit:
                self._raise('Unexpected end of input')

            if not c:
                break

            if not (c in '0123456789.eE+-' or (self._allow_extended_number_literals and c in 'xXabcdefABCDEF')):
                break
            self._buf.write(c)

        raw = self._flip_buf()

        #

        if self._allow_extended_number_literals:
            p = 1 if raw[0] in '+-' else 0
            if (len(raw) - p) > 1 and raw[p] == '0' and raw[p + 1] in '0123456789':
                self._raise('Invalid number literal')

        if raw == '-' or (self._allow_extended_number_literals and raw == '+'):
            for svs in [
                'Infinity',
                *(['NaN'] if self._allow_extended_number_literals else []),
            ]:
                if c != svs[0]:
                    continue

                raw += c
                try:
                    for _ in range(len(svs) - 1):
                        if (c := self._str_char_in()) is None:  # type: ignore[assignment]
                            c = self._yield_char_in((yield None))  # noqa
                        if not c:
                            break
                        raw += c
                except GeneratorExit:
                    self._raise('Unexpected end of input')

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

        #

        if not c:
            return None

        return self._do_main(c)

    def _do_const(self, c: str):
        pos = self.pos
        raw = c
        while True:
            try:
                if (c := self._str_char_in()) is None:  # type: ignore[assignment]
                    c = self._yield_char_in((yield None))  # noqa
            except GeneratorExit:
                self._raise('Unexpected end of input')

            raw += c

            if raw in CONST_IDENT_VALUES:
                break

            if len(raw) > MAX_CONST_IDENT_LEN:
                self._raise(f'Invalid literal: {raw}')

        yield self._make_tok('IDENT', raw, raw, pos)

        return self._do_main()

    def _do_unicode_escape(self):
        try:
            if (c := self._str_char_in()) is None:
                c = self._yield_char_in((yield None))  # noqa
        except GeneratorExit:
            self._raise('Unexpected end of input')

        if c != 'u':
            self._raise('Illegal identifier escape')

        ux = []
        for _ in range(4):
            try:
                if (c := self._str_char_in()) is None:
                    c = self._yield_char_in((yield None))  # noqa
            except GeneratorExit:
                self._raise('Unexpected end of input')

            if c not in '0123456789abcdefABCDEF':
                self._raise('Illegal identifier escape')

            ux.append(c)

        return chr(int(''.join(ux), 16))

    def _do_extended_ident(self, c: str):
        check.state(self._buf.tell() == 0)

        if c == '\\':
            c = yield from self._do_unicode_escape()

        elif not (c in '$_' or unicodedata.category(c).startswith('L')):
            self._raise('Illegal identifier start')

        self._buf.write(c)

        pos = self.pos

        while True:
            try:
                if (c := self._str_char_in()) is None:  # type: ignore[assignment]
                    c = self._yield_char_in((yield None))  # noqa
            except GeneratorExit:
                self._raise('Unexpected end of input')

            if c == '\\':
                c = yield from self._do_unicode_escape()
                self._buf.write(c)
                continue

            if not c:
                break

            if c not in '$_\u200C\u200D':
                uc = unicodedata.category(c)
                if not (uc.startswith(('L', 'M', 'N')) or uc == 'Pc'):
                    break

            self._buf.write(c)

        raw = self._flip_buf()

        yield self._make_tok('IDENT', raw, raw, pos)

        return self._do_main(c)

    def _do_comment(self):
        check.state(self._buf.tell() == 0)

        pos = self.pos
        try:
            if (oc := self._str_char_in()) is None:
                oc = self._yield_char_in((yield None))  # noqa
        except GeneratorExit:
            self._raise('Unexpected end of input')

        if oc == '/':
            while True:
                try:
                    if (ic := self._str_char_in()) is None:
                        ic = self._yield_char_in((yield None))  # noqa
                except GeneratorExit:
                    self._raise('Unexpected end of input')

                if not ic or ic == '\n':
                    break

                if self._include_comments:
                    self._buf.write(ic)

            if self._include_comments:
                cmt = self._flip_buf()
                raw = f'//{cmt}\n' if self._include_raw else None
                yield self._make_tok('COMMENT', cmt, raw, pos)

            if not ic:
                return

        elif oc == '*':
            lc: str | None = None
            while True:
                try:
                    if (ic := self._str_char_in()) is None:
                        ic = self._yield_char_in((yield None))  # noqa
                except GeneratorExit:
                    self._raise('Unexpected end of input')

                if lc == '*' and ic == '/':
                    break

                if lc is not None and self._include_comments:
                    self._buf.write(lc)
                lc = ic

            if self._include_comments:
                cmt = self._flip_buf()
                raw = f'/*{cmt}*/' if self._include_raw else None
                yield self._make_tok('COMMENT', cmt, raw, pos)

        else:
            self._raise(f'Unexpected character after comment start: {oc}')

        return self._do_main()
