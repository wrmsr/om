"""
The override statement grammar:

  model.opt.lr=3e-4                         replace
  model.opt+={lr: 3e-4, betas: [0.9, 0.99]} deep-merge a map / extend a list
  data.transforms[+]={kind: flip}           append one element (or `data.transforms.+=...`)
  data.transforms[-1].p=0.2                 index, negatives ok (or `data.transforms.-1.p=...`)
  layers[name=enc].dim=3                    the single element with a matching value
  /model.dropout                            remove / reset to default
  model.encoder=@enc.json                   value from a file
  @experiment.json                          merge a file at the root

Values are not parsed here - they are carried as text until applied.
"""
import typing as ta

from .errors import OverrideSyntaxError
from .literals import QUOTE_CHARS
from .literals import RawScalar
from .literals import scan_quoted
from .ops import FileOpValue
from .ops import MergeOp
from .ops import OpValue
from .ops import OverrideOp
from .ops import RawOpValue
from .ops import RemoveOp
from .ops import SetOp
from .paths import BARE_KEY_PAT
from .paths import INT_PAT
from .paths import AppendSegment
from .paths import IndexSegment
from .paths import KeySegment
from .paths import OverridePath
from .paths import PathSegment
from .paths import SelectSegment


##


REMOVE_PREFIX = '/'
FILE_PREFIX = '@'


class _Parser:
    def __init__(self, s: str) -> None:
        super().__init__()

        self._s = s
        self._p = 0

    def _error(self, msg: str) -> OverrideSyntaxError:
        return OverrideSyntaxError(f'{msg} at position {self._p}: {self._s!r}')

    def _peek(self) -> str:
        return self._s[self._p] if self._p < len(self._s) else ''

    def _skip_ws(self) -> None:
        while self._peek().isspace():
            self._p += 1

    def _expect(self, c: str) -> None:
        if self._peek() != c:
            raise self._error(f'expected {c!r}')
        self._p += 1

    #

    def _parse_key(self) -> tuple[str, bool]:
        if self._peek() in QUOTE_CHARS:
            k, self._p = scan_quoted(self._s, self._p)
            return k, True

        if (m := BARE_KEY_PAT.match(self._s, self._p)) is None:
            raise self._error('expected key')
        self._p = m.end()
        return m.group(), False

    def _parse_select_segment(self, first_key: str | None = None) -> SelectSegment:
        keys = [first_key if first_key is not None else self._parse_key()[0]]
        while self._peek() == '.':
            self._p += 1
            keys.append(self._parse_key()[0])

        self._skip_ws()
        self._expect('=')
        self._skip_ws()

        if self._peek() in QUOTE_CHARS:
            t, self._p = scan_quoted(self._s, self._p)
            return SelectSegment(keys, RawScalar(t, quoted=True))

        b = self._p
        while (c := self._peek()) and c != ']':
            self._p += 1
        if not (t := self._s[b:self._p].strip()):
            raise self._error('expected value')
        return SelectSegment(keys, RawScalar(t))

    def _parse_bracket_segment(self) -> PathSegment:
        self._expect('[')
        self._skip_ws()

        seg: PathSegment
        if (c := self._peek()) == '+':
            self._p += 1
            seg = AppendSegment()

        elif (m := INT_PAT.match(self._s, self._p)) is not None and self._s[m.end():].lstrip()[:1] == ']':
            self._p = m.end()
            seg = IndexSegment(int(m.group()))

        elif c in QUOTE_CHARS:
            k, _ = self._parse_key()
            self._skip_ws()
            if self._peek() == ']':
                seg = KeySegment(k, quoted=True)
            else:
                seg = self._parse_select_segment(k)

        else:
            seg = self._parse_select_segment()

        self._skip_ws()
        self._expect(']')
        return seg

    def _parse_dot_segment(self) -> PathSegment:
        self._expect('.')
        if self._peek() == '+':
            self._p += 1
            return AppendSegment()
        return KeySegment(*self._parse_key())

    def parse_path(self) -> OverridePath:
        segs: list[PathSegment] = []
        while True:
            if (c := self._peek()) == '.':
                segs.append(self._parse_dot_segment())
            elif c == '[':
                segs.append(self._parse_bracket_segment())
            elif not segs and c and (c in QUOTE_CHARS or BARE_KEY_PAT.match(c)):
                segs.append(KeySegment(*self._parse_key()))
            else:
                return tuple(segs)

    def expect_end(self) -> None:
        self._skip_ws()
        if self._p != len(self._s):
            raise self._error('unexpected text')

    #

    def _parse_value(self) -> OpValue:
        if (t := self._s[self._p:].strip()).startswith(FILE_PREFIX):
            return self._parse_file_value(t)
        return RawOpValue(t)

    def _parse_file_value(self, t: str) -> FileOpValue:
        if not (f := t[len(FILE_PREFIX):].strip()):
            raise self._error('expected file path')
        return FileOpValue(f)

    def parse_statement(self) -> OverrideOp:
        self._skip_ws()

        if self._s.startswith(FILE_PREFIX, self._p):
            return MergeOp((), self._parse_file_value(self._s[self._p:].strip()))

        if self._s.startswith(REMOVE_PREFIX, self._p):
            self._p += len(REMOVE_PREFIX)
            if not (path := self.parse_path()):
                raise self._error('expected path')
            self.expect_end()
            return RemoveOp(path)

        path = self.parse_path()
        self._skip_ws()

        op_cls: ta.Any
        if self._s.startswith('+=', self._p):
            op_cls = MergeOp
            self._p += 2
        elif self._s.startswith('=', self._p):
            op_cls = SetOp
            self._p += 1
        else:
            raise self._error("expected '=' or '+='")

        return op_cls(path, self._parse_value())


##


def parse_path(s: str) -> OverridePath:
    p = _Parser(s)
    path = p.parse_path()
    p.expect_end()
    return path


def parse_override(s: str) -> OverrideOp:
    return _Parser(s).parse_statement()
