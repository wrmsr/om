"""
The 'raw' value literal grammar: a relaxed, json5-ish syntax in which scalars may be bare, deliberately left untyped at
parse time so they may be typed later by the shape of whatever they wind up targeting:

  {lr: 3e-4, betas: [0.9, 0.99], name: adam, note: "quoted, with a comma"}

A quoted scalar is always a string. A bare scalar is just text: it ends at the next `,`, `}` or `]` when nested in a
list or map, and is otherwise the entire value.
"""
import re
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...formats import json5
from .errors import OverrideSyntaxError


##


class RawNode(lang.Abstract, lang.Sealed):
    pass


@dc.dataclass(frozen=True)
class RawScalar(RawNode, lang.Final):
    text: str
    quoted: bool = False

    # Set when the text looked like a list or map but could not be parsed as one, and was thus taken as a bare scalar.
    structure_error: str | None = None


@dc.dataclass(frozen=True)
class RawList(RawNode, lang.Final):
    items: ta.Sequence[RawNode] = dc.xfield(coerce=tuple)

    # The source text, present only on the outermost node of a value.
    text: str | None = None


@dc.dataclass(frozen=True)
class RawMap(RawNode, lang.Final):
    items: ta.Sequence[tuple[str, RawNode]] = dc.xfield(coerce=tuple)

    text: str | None = None


##


# A set, not a string: the empty string is 'in' every string.
QUOTE_CHARS: ta.AbstractSet[str] = frozenset('"\'')


def scan_quoted(s: str, pos: int) -> tuple[str, int]:
    """Parses the quoted string literal beginning at the given position, returning its value and end position."""

    q = s[pos]
    i = pos + 1
    while i < len(s):
        c = s[i]
        if c == '\\':
            i += 2
            continue
        if c == q:
            try:
                return json5.parse_string_literal(s[pos:i + 1]), i + 1
            except json5.Json5Error as e:
                raise OverrideSyntaxError(f'invalid string literal at position {pos}: {s!r}') from e
        i += 1

    raise OverrideSyntaxError(f'unterminated string literal at position {pos}: {s!r}')


##


class _RawParser:
    _STOPS = ',}]'

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

    def _scan_bare(self, stops: str) -> str:
        b = self._p
        while (c := self._peek()) and c not in stops:
            self._p += 1
        if not (t := self._s[b:self._p].strip()):
            raise self._error('expected value')
        return t

    def _parse_items(self, close: str, parse_item: ta.Callable[[], None]) -> None:
        self._p += 1
        while True:
            self._skip_ws()
            if self._peek() == close:
                self._p += 1
                return

            parse_item()

            self._skip_ws()
            if (c := self._peek()) == ',':
                self._p += 1
            elif c != close:
                raise self._error(f"expected ',' or {close!r}")

    def _parse_list(self) -> RawList:
        items: list[RawNode] = []
        self._parse_items(']', lambda: items.append(self._parse_node()))
        return RawList(items)

    def _parse_map(self) -> RawMap:
        items: dict[str, RawNode] = {}

        def parse_item() -> None:
            if self._peek() in QUOTE_CHARS:
                k, self._p = scan_quoted(self._s, self._p)
            else:
                k = self._scan_bare(':' + self._STOPS + '{[')

            self._skip_ws()
            if self._peek() != ':':
                raise self._error("expected ':'")
            self._p += 1

            if k in items:
                raise self._error(f'duplicate key {k!r}')
            items[k] = self._parse_node()

        self._parse_items('}', parse_item)
        return RawMap(list(items.items()))

    def _parse_node(self) -> RawNode:
        self._skip_ws()
        if (c := self._peek()) == '{':
            return self._parse_map()
        elif c == '[':
            return self._parse_list()
        elif c in QUOTE_CHARS:
            t, self._p = scan_quoted(self._s, self._p)
            return RawScalar(t, quoted=True)
        else:
            return RawScalar(self._scan_bare(self._STOPS))

    def parse(self) -> RawNode:
        n = self._parse_node()
        self._skip_ws()
        if self._p != len(self._s):
            raise self._error('unexpected trailing text')
        return n


def parse_raw_value(text: str) -> RawNode:
    """
    Parses the text of an entire value. Never fails: text which is neither a well-formed list or map nor a single
    quoted string is a bare scalar, verbatim.
    """

    text = text.strip()

    if text[:1] in QUOTE_CHARS:
        try:
            t, e = scan_quoted(text, 0)
        except OverrideSyntaxError:
            pass
        else:
            if e == len(text):
                return RawScalar(t, quoted=True)

    elif text[:1] in ('{', '['):
        try:
            n = _RawParser(text).parse()
        except OverrideSyntaxError as e:
            return RawScalar(text, structure_error=str(e))
        return dc.replace(check.isinstance(n, (RawList, RawMap)), text=text)

    return RawScalar(text)


##


_INT_PAT = re.compile(r'[+-]?(0|[1-9]\d*)')
_HEX_PAT = re.compile(r'[+-]?0[xX][0-9a-fA-F]+')
_FLOAT_PAT = re.compile(
    r'[+-]?('
    r'((0|[1-9]\d*)(\.\d*)?|\.\d+)([eE][+-]?\d+)?'
    r'|Infinity'
    r')'
    r'|NaN',
)

_CONST_GUESSES: ta.Mapping[str, ta.Any] = {
    'null': None,
    'true': True,
    'false': False,
}


def guess_scalar(text: str) -> ta.Any:
    """Json5-style: anything which is not a json5 null, boolean, or number is a string."""

    try:
        return _CONST_GUESSES[text]
    except KeyError:
        pass

    if _INT_PAT.fullmatch(text):
        return int(text)
    if _HEX_PAT.fullmatch(text):
        return int(text, 16)
    if _FLOAT_PAT.fullmatch(text):
        return float(text)

    return text


def guess_raw(raw: RawNode) -> ta.Any:
    if isinstance(raw, RawScalar):
        return raw.text if raw.quoted else guess_scalar(raw.text)
    elif isinstance(raw, RawList):
        return [guess_raw(e) for e in raw.items]
    elif isinstance(raw, RawMap):
        return {k: guess_raw(v) for k, v in raw.items}
    else:
        raise TypeError(raw)
