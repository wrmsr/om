# ruff: noqa: UP006 UP007 UP017 UP037 UP045
# @om-lite
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.
#
# PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
# --------------------------------------------
#
# 1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and the Individual or Organization
# ("Licensee") accessing and otherwise using this software ("Python") in source or binary form and its associated
# documentation.
#
# 2. Subject to the terms and conditions of this License Agreement, PSF hereby grants Licensee a nonexclusive,
# royalty-free, world-wide license to reproduce, analyze, test, perform and/or display publicly, prepare derivative
# works, distribute, and otherwise use Python alone or in any derivative version, provided, however, that PSF's License
# Agreement and PSF's notice of copyright, i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
# 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023 Python Software Foundation; All
# Rights Reserved" are retained in Python alone or in any derivative version prepared by Licensee.
#
# 3. In the event Licensee prepares a derivative work that is based on or incorporates Python or any part thereof, and
# wants to make the derivative work available to others as provided herein, then Licensee hereby agrees to include in
# any such work a brief summary of the changes made to Python.
#
# 4. PSF is making Python available to Licensee on an "AS IS" basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES,
# EXPRESS OR IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION OR WARRANTY
# OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT INFRINGE ANY THIRD PARTY
# RIGHTS.
#
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL
# DAMAGES OR LOSS AS A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON, OR ANY DERIVATIVE THEREOF, EVEN IF
# ADVISED OF THE POSSIBILITY THEREOF.
#
# 6. This License Agreement will automatically terminate upon a material breach of its terms and conditions.
#
# 7. Nothing in this License Agreement shall be deemed to create any relationship of agency, partnership, or joint
# venture between PSF and Licensee.  This License Agreement does not grant permission to use PSF trademarks or trade
# name in a trademark sense to endorse or promote products or services of Licensee, or any third party.
#
# 8. By copying, installing or otherwise using Python, Licensee agrees to be bound by the terms and conditions of this
# License Agreement.
#
# https://github.com/python/cpython/blob/9ce90206b7a4649600218cf0bd4826db79c9a312/Lib/tomllib/_parser.py
# https://github.com/python/cpython/blob/bb917d83b16231ad5193731f0405fbc53122d68b/Lib/tomllib/_parser.py
"""
A lite-compatible port of the standard library's tomllib, supporting TOML 1.1 and extended with optional full-fidelity
token emission.

`toml_loads` behaves as `tomllib.loads`. `toml_parse_document` additionally produces a `TomlDocument` whose tokens
partition the source exactly (whitespace, newlines and comments included) and whose nodes map every table, key and
value to its tokens and to its unmarshaled python value, and which supports surgically rewriting the source while
preserving everything not touched. The sibling `writer` module authors new documents through the same rendering.
"""
import bisect
import dataclasses as dc
import datetime
import decimal
import functools
import math
import re
import string
import types
import typing as ta


TomlParseFloat = ta.Callable[[str], ta.Any]  # ta.TypeAlias
TomlKey = ta.Tuple[str, ...]  # ta.TypeAlias
TomlPos = int  # ta.TypeAlias
TomlPathPart = ta.Union[str, int]  # ta.TypeAlias
TomlPath = ta.Tuple[TomlPathPart, ...]  # ta.TypeAlias


##


# No need to limit cache size. This is only ever called on input that matched RE_DATETIME, so there is an implicit bound
# of 24 (hours) * 60 (minutes) * 2 (offset direction) = 2880.
@functools.lru_cache(maxsize=None)  # noqa: UP033
def toml_cached_tz(hour_str: str, minute_str: str, sign_str: str) -> datetime.timezone:
    sign = 1 if sign_str == '+' else -1
    return datetime.timezone(
        datetime.timedelta(
            hours=sign * int(hour_str),
            minutes=sign * int(minute_str),
        ),
    )


def toml_make_safe_parse_float(parse_float: TomlParseFloat) -> TomlParseFloat:
    """
    A decorator to make `parse_float` safe.

    `parse_float` must not return dicts or lists, because these types would be mixed with parsed TOML tables and arrays,
    thus confusing the parser. The returned decorated callable raises `ValueError` instead of returning illegal types.
    """

    # The default `float` callable never returns illegal types. Optimize it.
    if parse_float is float:
        return float

    def safe_parse_float(float_str: str) -> ta.Any:
        float_value = parse_float(float_str)
        if isinstance(float_value, (dict, list)):
            raise ValueError('parse_float must not return dicts or lists')  # noqa
        return float_value

    return safe_parse_float


class TomlDecodeError(ValueError):
    """
    An error raised if a document is not valid TOML.

    Adds the following attributes to ValueError:
     - msg: The unformatted error message
     - doc: The TOML document being parsed
     - pos: The index of doc where parsing failed
     - lineno: The line corresponding to pos
     - colno: The column corresponding to pos
    """

    def __init__(
            self,
            msg: str = '',
            doc: ta.Optional[str] = None,
            pos: ta.Optional[TomlPos] = None,
    ) -> None:
        lineno: ta.Optional[int] = None
        colno: ta.Optional[int] = None

        if doc is None or pos is None:
            super().__init__(msg)

        else:
            lineno = doc.count('\n', 0, pos) + 1
            if lineno == 1:
                colno = pos + 1
            else:
                colno = pos - doc.rindex('\n', 0, pos)

            if pos >= len(doc):
                coord_repr = 'end of document'
            else:
                coord_repr = f'line {lineno}, column {colno}'

            super().__init__(f'{msg} (at {coord_repr})')

        self.msg = msg
        self.doc = doc
        self.pos = pos
        self.lineno = lineno
        self.colno = colno


class TomlDocumentError(Exception):
    """An error raised when a `TomlDocument` cannot be inspected or rewritten as requested."""


##


class TomlFlags:
    """Flags that map to parsed keys/namespaces."""

    # Marks an immutable namespace (inline array or inline table).
    FROZEN = 0
    # Marks a nest that has been explicitly created and can no longer be opened using the "[table]" syntax.
    EXPLICIT_NEST = 1

    def __init__(self) -> None:
        super().__init__()

        self._flags: ta.Dict[str, dict] = {}
        self._pending_flags: ta.Set[ta.Tuple[TomlKey, int]] = set()

    def add_pending(self, key: TomlKey, flag: int) -> None:
        self._pending_flags.add((key, flag))

    def finalize_pending(self) -> None:
        for key, flag in self._pending_flags:
            self.set(key, flag, recursive=False)
        self._pending_flags.clear()

    def unset_all(self, key: TomlKey) -> None:
        cont = self._flags
        for k in key[:-1]:
            if k not in cont:
                return
            cont = cont[k]['nested']
        cont.pop(key[-1], None)

    def set(self, key: TomlKey, flag: int, *, recursive: bool) -> None:  # noqa: A003
        cont = self._flags
        key_parent, key_stem = key[:-1], key[-1]

        for k in key_parent:
            if k not in cont:
                cont[k] = {'flags': set(), 'recursive_flags': set(), 'nested': {}}
            cont = cont[k]['nested']

        if key_stem not in cont:
            cont[key_stem] = {'flags': set(), 'recursive_flags': set(), 'nested': {}}

        cont[key_stem]['recursive_flags' if recursive else 'flags'].add(flag)

    def is_(self, key: TomlKey, flag: int) -> bool:
        if not key:
            return False  # document root has no flags

        cont = self._flags
        for k in key[:-1]:
            if k not in cont:
                return False

            inner_cont = cont[k]
            if flag in inner_cont['recursive_flags']:
                return True

            cont = inner_cont['nested']

        key_stem = key[-1]
        if key_stem in cont:
            inner_cont = cont[key_stem]
            return flag in inner_cont['flags'] or flag in inner_cont['recursive_flags']

        return False


class TomlNestedDict:
    def __init__(self) -> None:
        super().__init__()

        # The parsed content of the TOML document
        self.dict: ta.Dict[str, ta.Any] = {}

    def get_or_create_nest(
            self,
            key: TomlKey,
            *,
            access_lists: bool = True,
    ) -> dict:
        cont: ta.Any = self.dict

        for k in key:
            if k not in cont:
                cont[k] = {}

            cont = cont[k]

            if access_lists and isinstance(cont, list):
                cont = cont[-1]

            if not isinstance(cont, dict):
                raise KeyError('There is no nest behind this key')

        return cont

    def append_nest_to_list(self, key: TomlKey) -> dict:
        cont = self.get_or_create_nest(key[:-1])

        nest: dict = {}

        last_key = key[-1]
        if last_key in cont:
            list_ = cont[last_key]
            if not isinstance(list_, list):
                raise KeyError('An object other than list found behind this key')
            list_.append(nest)

        else:
            cont[last_key] = [nest]

        return nest


##


class TomlTokenKinds:
    """
    The kinds of tokens emitted by `TomlParser` when building a document. Tokens partition the source exactly: the
    concatenation of the `raw` text of every token is the original source.
    """

    # Trivia
    WS = 'WS'
    NEWLINE = 'NEWLINE'
    COMMENT = 'COMMENT'

    # Punctuation
    EQUALS = 'EQUALS'
    DOT = 'DOT'
    COMMA = 'COMMA'
    ARRAY_OPEN = 'ARRAY_OPEN'
    ARRAY_CLOSE = 'ARRAY_CLOSE'
    INLINE_TABLE_OPEN = 'INLINE_TABLE_OPEN'
    INLINE_TABLE_CLOSE = 'INLINE_TABLE_CLOSE'
    TABLE_OPEN = 'TABLE_OPEN'
    TABLE_CLOSE = 'TABLE_CLOSE'
    ARRAY_TABLE_OPEN = 'ARRAY_TABLE_OPEN'
    ARRAY_TABLE_CLOSE = 'ARRAY_TABLE_CLOSE'

    # Keys
    BARE_KEY = 'BARE_KEY'

    # Strings - used both as values and as quoted key parts. Their token value is the unescaped string.
    BASIC_STRING = 'BASIC_STRING'
    LITERAL_STRING = 'LITERAL_STRING'
    ML_BASIC_STRING = 'ML_BASIC_STRING'
    ML_LITERAL_STRING = 'ML_LITERAL_STRING'

    # Other scalars. Their token value is the parsed python value.
    BOOL = 'BOOL'
    INTEGER = 'INTEGER'
    FLOAT = 'FLOAT'
    OFFSET_DATETIME = 'OFFSET_DATETIME'
    LOCAL_DATETIME = 'LOCAL_DATETIME'
    LOCAL_DATE = 'LOCAL_DATE'
    LOCAL_TIME = 'LOCAL_TIME'

    TRIVIA = frozenset([WS, NEWLINE, COMMENT])

    STRINGS = frozenset([BASIC_STRING, LITERAL_STRING, ML_BASIC_STRING, ML_LITERAL_STRING])

    SCALARS = STRINGS | frozenset([
        BOOL,
        INTEGER,
        FLOAT,
        OFFSET_DATETIME,
        LOCAL_DATETIME,
        LOCAL_DATE,
        LOCAL_TIME,
    ])

    KEY_PARTS = frozenset([BARE_KEY, BASIC_STRING, LITERAL_STRING])


class TomlToken(ta.NamedTuple):
    """
    A lexical token. `raw` is the exact original source text of the token (a NEWLINE token's raw is '\\r\\n' when the
    source used that line ending), and `ofs` is its offset in that original source. `line` and `col` are 1-based, as in
    `TomlDecodeError` messages. `value` is the parsed python value of scalar tokens and the unquoted string of key part
    tokens, and is None otherwise.
    """

    kind: str
    raw: str
    value: ta.Any
    ofs: int
    line: int
    col: int

    @property
    def end(self) -> int:
        return self.ofs + len(self.raw)


##


@dc.dataclass(frozen=True)
class TomlNode:
    """
    A half-open range of token indices in a parsed document, referencing the document's token sequence. Nodes belong to
    the document which produced them: edits produce a new document with new nodes.
    """

    start: int
    end: int
    tokens: ta.Sequence[TomlToken] = dc.field(repr=False, compare=False)

    @property
    def span(self) -> ta.Sequence[TomlToken]:
        return self.tokens[self.start:self.end]

    def _empty_ofs(self) -> int:
        if self.start < len(self.tokens):
            return self.tokens[self.start].ofs
        if self.tokens:
            return self.tokens[-1].end
        return 0

    @property
    def ofs(self) -> int:
        if self.start < self.end:
            return self.tokens[self.start].ofs
        return self._empty_ofs()

    @property
    def end_ofs(self) -> int:
        if self.start < self.end:
            return self.tokens[self.end - 1].end
        return self._empty_ofs()

    @property
    def raw(self) -> str:
        return ''.join(t.raw for t in self.span)

    def children(self) -> ta.Sequence['TomlNode']:
        return ()

    def walk(self) -> ta.Iterator['TomlNode']:
        yield self
        for c in self.children():
            yield from c.walk()


@dc.dataclass(frozen=True)
class TomlKeyNode(TomlNode):
    """
    A possibly dotted key, as written in a key/value pair or a table header. Its span excludes surrounding whitespace.
    """

    key: TomlKey


@dc.dataclass(frozen=True)
class TomlValueNode(TomlNode):
    """
    A node which corresponds to an unmarshaled python value: `value` is that object (for tables, arrays, and inline
    tables it is the very dict or list in the document's data), and `path` is its absolute path within that data.
    """

    path: TomlPath
    value: ta.Any = dc.field(compare=False)


@dc.dataclass(frozen=True)
class TomlScalarNode(TomlValueNode):
    @property
    def token(self) -> TomlToken:
        return self.tokens[self.start]


@dc.dataclass(frozen=True)
class TomlArrayNode(TomlValueNode):
    items: ta.Tuple[TomlValueNode, ...]

    def children(self) -> ta.Sequence[TomlNode]:
        return self.items


@dc.dataclass(frozen=True)
class TomlKeyValueNode(TomlNode):
    """
    A `key = value` pair, either a top-level statement or a member of an inline table. Its span is key through value.
    """

    key: TomlKeyNode
    value: TomlValueNode

    @property
    def path(self) -> TomlPath:
        return self.value.path

    def children(self) -> ta.Sequence[TomlNode]:
        return (self.key, self.value)


@dc.dataclass(frozen=True)
class TomlInlineTableNode(TomlValueNode):
    pairs: ta.Tuple[TomlKeyValueNode, ...]

    def children(self) -> ta.Sequence[TomlNode]:
        return self.pairs


@dc.dataclass(frozen=True)
class TomlTableHeaderNode(TomlNode):
    """A `[key]` or `[[key]]` header, spanning its brackets."""

    key: TomlKeyNode
    is_array: bool

    def children(self) -> ta.Sequence[TomlNode]:
        return (self.key,)


@dc.dataclass(frozen=True)
class TomlTableNode(TomlValueNode):
    """
    A table section: a header (absent only for the implicit root table, which is always the document's first table)
    followed by the key/value statements up to the next header. Its span ends with its last statement (or its header)
    so trailing blank lines and comments are not included. For `[[key]]` headers `value` is the newly appended array
    element and `path` ends with its index.
    """

    header: ta.Optional[TomlTableHeaderNode]
    pairs: ta.Tuple[TomlKeyValueNode, ...]

    @property
    def is_root(self) -> bool:
        return self.header is None

    @property
    def is_array(self) -> bool:
        return self.header is not None and self.header.is_array

    def children(self) -> ta.Sequence[TomlNode]:
        if self.header is not None:
            return (self.header, *self.pairs)
        return self.pairs


##


@dc.dataclass(frozen=True)
class TomlStyle:
    """
    Rendering preferences for values written by document edits and by the writer. The defaults reproduce the historical
    `TomlWriter` output: single quoted (literal) strings and keys where possible, every non-empty array laid out one
    element per line with trailing commas, four space indentation, and unpadded inline tables.
    """

    # The preferred quoting of new strings and quoted keys: 'literal', falling back to basic strings for values which
    # cannot be literal strings, or 'basic'.
    quotes: str = 'literal'

    indent: str = '    '

    # How arrays are laid out: 'multiline' (one element per line), 'inline' (a single line), or 'auto' (inline when the
    # array contains no nested arrays or tables and its inline rendering fits within `max_inline_width`).
    array_layout: str = 'multiline'
    max_inline_width: int = 80

    # The whitespace inside the braces of a non-empty inline table, for example ' ' for '{ a = 1 }'.
    inline_table_padding: str = ''

    blank_lines_between_tables: int = 1

    # Permits emitting syntax new in TOML 1.1 (multi-line inline tables), which many consumers cannot yet read.
    toml_1_1: bool = False


@dc.dataclass(frozen=True)
class TomlRaw:
    """Verbatim TOML source text, written in place of a value or key part."""

    text: str


@dc.dataclass(frozen=True)
class TomlInline:
    """Marks an array or table value to be rendered on a single line, regardless of style."""

    value: ta.Any


@dc.dataclass(frozen=True)
class TomlMultiline:
    """Marks an array (or, with TOML 1.1 enabled, an inline table) to be rendered one element per line."""

    value: ta.Any


class TomlValueRenderer:
    """Renders python values as TOML source text, for use in rewriting and writing documents."""

    def __init__(self, style: ta.Optional[TomlStyle] = None, *, newline: str = '\n') -> None:
        super().__init__()

        if style is None:
            style = TomlStyle()
        if style.quotes not in ('literal', 'basic'):
            raise TomlDocumentError(f'Unknown quote style {style.quotes!r}')
        if style.array_layout not in ('multiline', 'inline', 'auto'):
            raise TomlDocumentError(f'Unknown array layout {style.array_layout!r}')

        self._style = style
        self._newline = newline

    @property
    def style(self) -> TomlStyle:
        return self._style

    # Bare keys may legally consist only of digits, but keys not starting with a letter or underscore are quoted for
    # clarity.
    BARE_KEY_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_-]*')

    BASIC_STR_ESCAPES: ta.Mapping[str, str] = types.MappingProxyType({
        '\\': '\\\\',
        '"': '\\"',
        '\u0008': '\\b',
        '\u0009': '\\t',
        '\u000A': '\\n',
        '\u000C': '\\f',
        '\u000D': '\\r',
    })

    @classmethod
    def is_control_char(cls, c: str) -> bool:
        return c < ' ' or c == '\u007F'

    def render_key_part(self, k: ta.Any) -> str:
        if isinstance(k, TomlRaw):
            return k.text
        if isinstance(k, bool) or not isinstance(k, (str, int)):
            raise TomlDocumentError(f'Cannot render key of type {type(k).__name__}')
        s = str(k)
        if s and self.BARE_KEY_RE.fullmatch(s):
            return s
        return self.render_str(s)

    def render_key(self, key: ta.Iterable[ta.Any]) -> str:
        return '.'.join(self.render_key_part(p) for p in key)

    @classmethod
    def render_comment(cls, text: str) -> str:
        """Renders a comment line: text already starting with '#' is kept as is, otherwise it is prefixed."""

        if not text:
            return '#'
        if text.startswith('#'):
            return text
        return '# ' + text

    def render_basic_str(self, s: str, *, multiline: bool = False) -> str:
        escape_quotes = not multiline or '"""' in s
        buf = []
        for c in s:
            if multiline and c in ('\n', '\t'):
                buf.append(c)
            elif c == '"' and not escape_quotes:
                buf.append(c)
            elif c in self.BASIC_STR_ESCAPES:
                buf.append(self.BASIC_STR_ESCAPES[c])
            elif self.is_control_char(c):
                buf.append(f'\\u{ord(c):04X}')
            else:
                buf.append(c)
        body = ''.join(buf)
        if multiline:
            return '"""' + self._newline + body + '"""'
        return '"' + body + '"'

    def can_be_literal_str(self, s: str, *, multiline: bool = False) -> bool:
        if multiline:
            return "'''" not in s and not any(self.is_control_char(c) and c not in '\t\n' for c in s)
        return "'" not in s and not any(self.is_control_char(c) and c != '\t' for c in s)

    def render_str(self, s: str, *, like: ta.Optional[str] = None) -> str:
        """
        Renders a string, preferring the quoting style of the token kind `like` it is replacing where possible, and
        otherwise the style's preferred quoting.
        """

        if like in (TomlTokenKinds.ML_BASIC_STRING, TomlTokenKinds.ML_LITERAL_STRING) and '\n' in s:
            if like == TomlTokenKinds.ML_LITERAL_STRING and self.can_be_literal_str(s, multiline=True):
                return "'''" + self._newline + s + "'''"
            return self.render_basic_str(s, multiline=True)

        if like is None:
            literal = self._style.quotes == 'literal'
        else:
            literal = like in (TomlTokenKinds.LITERAL_STRING, TomlTokenKinds.ML_LITERAL_STRING)
        if literal and self.can_be_literal_str(s):
            return "'" + s + "'"

        return self.render_basic_str(s)

    def render_int(self, v: int, *, like: ta.Optional[TomlToken] = None) -> str:
        if like is not None and like.kind == TomlTokenKinds.INTEGER and v >= 0:
            raw = like.raw
            if raw.startswith('0x'):
                return f'0x{v:X}' if raw[2:] != raw[2:].lower() else f'0x{v:x}'
            if raw.startswith('0o'):
                return f'0o{v:o}'
            if raw.startswith('0b'):
                return f'0b{v:b}'
        return str(v)

    def render_float(self, v: float) -> str:
        if math.isnan(v):
            return 'nan'
        if math.isinf(v):
            return 'inf' if v > 0 else '-inf'
        return repr(v)

    def render_decimal(self, v: decimal.Decimal) -> str:
        if v.is_nan():
            return 'nan'
        if v.is_infinite():
            return 'inf' if v > 0 else '-inf'
        s = str(v)
        if not any(c in s for c in '.eE'):
            s += '.0'
        return s

    @classmethod
    def is_container(cls, v: ta.Any) -> bool:
        if isinstance(v, (TomlInline, TomlMultiline)):
            v = v.value
        return isinstance(v, (list, tuple, ta.Mapping))

    def _render_inline_array(self, v: ta.Sequence[ta.Any]) -> str:
        return '[' + ', '.join(self.render_value(e, inline_only=True) for e in v) + ']'

    def _render_multiline_array(self, v: ta.Sequence[ta.Any], indent: str) -> str:
        nl = self._newline
        inner = indent + self._style.indent
        return '[' + nl + ''.join(inner + self.render_value(e, indent=inner) + ',' + nl for e in v) + indent + ']'

    def render_array(
            self,
            v: ta.Sequence[ta.Any],
            *,
            layout: ta.Optional[str] = None,
            like: ta.Optional[TomlNode] = None,
            indent: str = '',
            inline_only: bool = False,
    ) -> str:
        if not v:
            return '[]'

        if inline_only:
            layout = 'inline'
        elif layout is None:
            if like is not None:
                layout = 'multiline' if '\n' in like.raw else 'inline'
            else:
                layout = self._style.array_layout

        if layout == 'auto':
            if any(self.is_container(e) for e in v):
                layout = 'multiline'
            else:
                text = self._render_inline_array(v)
                if len(text) <= self._style.max_inline_width:
                    return text
                layout = 'multiline'

        if layout == 'inline':
            return self._render_inline_array(v)
        return self._render_multiline_array(v, indent)

    def render_table(
            self,
            v: ta.Mapping[ta.Any, ta.Any],
            *,
            layout: ta.Optional[str] = None,
            like: ta.Optional[TomlNode] = None,
            indent: str = '',
            inline_only: bool = False,
    ) -> str:
        if not v:
            return '{}'

        if inline_only:
            layout = 'inline'
        elif layout is None:
            if like is not None and '\n' in like.raw and self._style.toml_1_1:
                layout = 'multiline'
            else:
                layout = 'inline'

        if layout == 'multiline':
            if not self._style.toml_1_1:
                raise TomlDocumentError('Multi-line inline tables require TOML 1.1 (see TomlStyle.toml_1_1)')
            nl = self._newline
            inner = indent + self._style.indent
            return '{' + nl + ''.join(
                inner + self.render_key_part(k) + ' = ' + self.render_value(e, indent=inner) + ',' + nl
                for k, e in v.items()
            ) + indent + '}'

        pad = self._style.inline_table_padding
        return '{' + pad + ', '.join(
            self.render_key_part(k) + ' = ' + self.render_value(e, inline_only=True)
            for k, e in v.items()
        ) + pad + '}'

    def render_value(  # noqa: C901
            self,
            v: ta.Any,
            *,
            like: ta.Optional[ta.Union[TomlToken, TomlNode]] = None,
            indent: str = '',
            inline_only: bool = False,
    ) -> str:
        """
        Renders a value. `like` is the scalar token or container node being replaced, if any, whose quoting or layout
        is preferred where possible. `indent` is the indentation of the line the value starts on, and `inline_only`
        forces containers onto a single line, as required within single-line arrays and inline tables.
        """

        layout: ta.Optional[str] = None
        if isinstance(v, TomlRaw):
            return v.text
        if isinstance(v, TomlInline):
            v = v.value
            layout = 'inline'
        elif isinstance(v, TomlMultiline):
            v = v.value
            layout = 'multiline'

        node = like if isinstance(like, (TomlArrayNode, TomlInlineTableNode)) else None
        tok = like if isinstance(like, TomlToken) else None

        if isinstance(v, (list, tuple)):
            return self.render_array(v, layout=layout, like=node, indent=indent, inline_only=inline_only)

        if isinstance(v, ta.Mapping):
            return self.render_table(v, layout=layout, like=node, indent=indent, inline_only=inline_only)

        if isinstance(v, bool):
            return 'true' if v else 'false'

        if isinstance(v, int):
            return self.render_int(v, like=tok)

        if isinstance(v, float):
            return self.render_float(v)

        if isinstance(v, decimal.Decimal):
            return self.render_decimal(v)

        if isinstance(v, str):
            return self.render_str(v, like=tok.kind if tok is not None else None)

        if isinstance(v, datetime.datetime):
            return v.isoformat()

        if isinstance(v, datetime.date):
            return v.isoformat()

        if isinstance(v, datetime.time):
            if v.tzinfo is not None:
                raise TomlDocumentError('TOML local times cannot have a timezone')
            return v.isoformat()

        raise TomlDocumentError(f'Cannot render value of type {type(v).__name__}')


##


class TomlDocument:
    """
    A parsed TOML document retaining full source fidelity. `tokens` partition `src` exactly, and `tables` (with their
    headers, statements, keys and values) map spans of those tokens to and from paths into `data`, which is the same
    object `toml_loads` would have returned.

    Paths are tuples of table and key names (str) and array indices (int) addressing values within `data`, such as
    `('servers', 'ports', 0)`. The root table has the empty path. Tables created only implicitly (by dotted keys or by
    sub-table headers) have no node of their own.

    Documents are immutable: editing methods return new documents, re-parsed from the edited source so that every edit
    is validated, and nodes obtained from one document must not be used with another. New values are rendered per the
    document's `style`, except that replacements keep the quoting and layout of what they replace, and insertions into
    arrays and inline tables mimic their neighbors, wherever possible.
    """

    def __init__(
            self,
            src: str,
            data: ta.Dict[str, ta.Any],
            tokens: ta.Sequence[TomlToken],
            tables: ta.Sequence[TomlTableNode],
            *,
            parse_float: TomlParseFloat = float,
            style: ta.Optional[TomlStyle] = None,
    ) -> None:
        super().__init__()

        self._src = src
        self._data = data
        self._tokens = tuple(tokens)
        self._tables = tuple(tables)
        self._parse_float = parse_float
        self._style = style

        by_path: ta.Dict[TomlPath, TomlValueNode] = {}
        kvs_by_path: ta.Dict[TomlPath, TomlKeyValueNode] = {}
        by_id: ta.Dict[int, TomlValueNode] = {}
        parents: ta.Dict[int, TomlNode] = {}

        for tbl in self._tables:
            for n in tbl.walk():
                for c in n.children():
                    parents[id(c)] = n
                if isinstance(n, TomlValueNode):
                    by_path[n.path] = n
                    if isinstance(n.value, (dict, list)):
                        by_id[id(n.value)] = n
                elif isinstance(n, TomlKeyValueNode):
                    kvs_by_path[n.path] = n

        self._by_path = by_path
        self._kvs_by_path = kvs_by_path
        self._by_id = by_id
        self._parents = parents

    @property
    def src(self) -> str:
        return self._src

    @property
    def data(self) -> ta.Dict[str, ta.Any]:
        return self._data

    @property
    def tokens(self) -> ta.Sequence[TomlToken]:
        return self._tokens

    @property
    def tables(self) -> ta.Sequence[TomlTableNode]:
        return self._tables

    @property
    def root(self) -> TomlTableNode:
        return self._tables[0]

    @property
    def style(self) -> ta.Optional[TomlStyle]:
        return self._style

    @property
    def newline(self) -> str:
        """The document's newline sequence, as used by its first line break (defaulting to a bare linefeed)."""

        for t in self._tokens:
            if t.kind == TomlTokenKinds.NEWLINE:
                return t.raw
        return '\n'

    # Lookups

    def node_at_path(self, path: ta.Iterable[TomlPathPart]) -> ta.Optional[TomlValueNode]:
        """Returns the scalar, array, inline table, or table node holding the value at `path`, if one exists."""

        return self._by_path.get(tuple(path))

    def key_value_at_path(self, path: ta.Iterable[TomlPathPart]) -> ta.Optional[TomlKeyValueNode]:
        """Returns the key/value pair (statement or inline table member) whose value is at `path`, if one exists."""

        return self._kvs_by_path.get(tuple(path))

    def table_at_path(self, path: ta.Iterable[TomlPathPart]) -> ta.Optional[TomlTableNode]:
        n = self._by_path.get(tuple(path))
        if isinstance(n, TomlTableNode):
            return n
        return None

    def node_for_value(self, obj: ta.Any) -> ta.Optional[TomlValueNode]:
        """Returns the node whose value is the given dict or list object from `data`, if one exists."""

        n = self._by_id.get(id(obj))
        if n is not None and n.value is obj:
            return n
        return None

    def parent_of(self, node: TomlNode) -> ta.Optional[TomlNode]:
        return self._parents.get(id(node))

    def node_at_offset(self, ofs: int) -> ta.Optional[TomlNode]:
        """Returns the innermost node whose source span contains the given offset, if any."""

        def rec(n: TomlNode) -> TomlNode:
            for c in n.children():
                if c.ofs <= ofs < c.end_ofs:
                    return rec(c)
            return n

        for tbl in self._tables:
            if tbl.ofs <= ofs < tbl.end_ofs:
                return rec(tbl)

        return None

    # Editing

    def _reparse(self, src: str) -> 'TomlDocument':
        return toml_parse_document(src, parse_float=self._parse_float, style=self._style)

    def splice(self, start: int, end: int, text: str) -> 'TomlDocument':
        """Replaces the source text in [start, end) with `text` and returns the re-parsed document."""

        if not (0 <= start <= end <= len(self._src)):
            raise TomlDocumentError(f'Invalid splice range [{start}, {end}) for source of length {len(self._src)}')
        return self._reparse(self._src[:start] + text + self._src[end:])

    def _splice_removals(self, spans: ta.Iterable[ta.Tuple[int, int]]) -> 'TomlDocument':
        parts = []
        prev = 0
        for start, end in sorted(spans):
            if start > prev:
                parts.append(self._src[prev:start])
            prev = max(prev, end)
        parts.append(self._src[prev:])
        return self._reparse(''.join(parts))

    def _splice_inserts(self, inserts: ta.Iterable[ta.Tuple[int, str]]) -> 'TomlDocument':
        parts = []
        prev = 0
        for ofs, text in sorted(inserts, key=lambda t: t[0]):
            parts.append(self._src[prev:ofs])
            parts.append(text)
            prev = ofs
        parts.append(self._src[prev:])
        return self._reparse(''.join(parts))

    def replace_node(self, node: TomlNode, text: str) -> 'TomlDocument':
        """Replaces the source text of a node with the given (raw TOML) text and returns the re-parsed document."""

        return self.splice(node.ofs, node.end_ofs, text)

    def _renderer(self) -> TomlValueRenderer:
        return TomlValueRenderer(self._style, newline=self.newline)

    #

    def _line_first_idx(self, idx: int) -> ta.Optional[int]:
        """The index of the first token on token `idx`'s line, if `idx` is that line's first non-whitespace token."""

        toks = self._tokens
        if idx == 0:
            return 0
        if toks[idx - 1].kind == TomlTokenKinds.NEWLINE:
            return idx
        if toks[idx - 1].kind == TomlTokenKinds.WS and (idx == 1 or toks[idx - 2].kind == TomlTokenKinds.NEWLINE):
            return idx - 1
        return None

    def _indent_of(self, idx: int) -> str:
        """The whitespace preceding token `idx` on its line, if it is the first non-whitespace token of the line."""

        first = self._line_first_idx(idx)
        if first is not None and first < idx:
            return self._tokens[first].raw
        return ''

    def _line_indent(self, idx: int) -> str:
        """The leading whitespace of the line containing token `idx`."""

        toks = self._tokens
        i = idx
        while i > 0 and toks[i - 1].kind != TomlTokenKinds.NEWLINE:
            i -= 1
        if i < len(toks) and toks[i].kind == TomlTokenKinds.WS:
            return toks[i].raw
        return ''

    def _line_start_ofs(self, idx: int) -> int:
        """The offset of the start of token `idx`'s line if only whitespace precedes it, else the token's own offset."""

        first = self._line_first_idx(idx)
        return self._tokens[idx if first is None else first].ofs

    def _line_end(self, idx: int, *, skip_comma: bool = False) -> ta.Tuple[int, ta.Optional[int]]:
        """
        Scans past any whitespace and comments (and, optionally, commas) following token `idx` on its line, returning
        the offset of the end of that content and the index of the terminating NEWLINE token, if there is one.
        """

        toks = self._tokens
        skip = [TomlTokenKinds.WS, TomlTokenKinds.COMMENT]
        if skip_comma:
            skip.append(TomlTokenKinds.COMMA)
        i = idx + 1
        while i < len(toks) and toks[i].kind in skip:
            i += 1
        if i < len(toks) and toks[i].kind == TomlTokenKinds.NEWLINE:
            return toks[i].ofs, i
        return toks[i - 1].end, None

    def _is_single_line(self, node: TomlNode) -> bool:
        return not any(t.kind == TomlTokenKinds.NEWLINE for t in node.span)

    def _enclosing_container(self, node: TomlNode) -> ta.Optional[TomlNode]:
        """The innermost array or inline table containing `node`, if any."""

        p = self._parents.get(id(node))
        while p is not None:
            if isinstance(p, (TomlArrayNode, TomlInlineTableNode)):
                return p
            p = self._parents.get(id(p))
        return None

    def _statement_removal_span(self, kv: TomlKeyValueNode) -> ta.Tuple[int, int]:
        start = self._line_start_ofs(kv.start)
        content_end, nl_idx = self._line_end(kv.end - 1)
        if nl_idx is not None:
            return start, self._tokens[nl_idx].end
        return start, content_end

    def _table_removal_span(self, tbl: TomlTableNode) -> ta.Tuple[int, int]:
        if tbl.header is None:
            raise TomlDocumentError('Cannot delete the root table')

        toks = self._tokens
        src = self._src
        start = self._line_start_ofs(tbl.header.start)
        content_end, nl_idx = self._line_end(tbl.end - 1)

        if nl_idx is None:
            end = content_end
        else:
            # Also swallow any blank lines following the table.
            end = toks[nl_idx].end
            i = nl_idx + 1
            while True:
                j = i
                if j < len(toks) and toks[j].kind == TomlTokenKinds.WS:
                    j += 1
                if j < len(toks) and toks[j].kind == TomlTokenKinds.NEWLINE:
                    end = toks[j].end
                    i = j + 1
                else:
                    break

        if end >= len(src):
            # The table ends the document: swallow the blank lines preceding it instead.
            while True:
                prev = src[:start]
                if prev.endswith('\r\n\r\n'):
                    start -= 2
                elif prev.endswith('\n\n'):
                    start -= 1
                else:
                    break

        return start, end

    def _inline_removal_span(
            self,
            container: TomlNode,
            elements: ta.Sequence[TomlNode],
            idx: int,
    ) -> ta.Tuple[int, int]:
        toks = self._tokens
        node = elements[idx]

        if len(elements) == 1:
            return toks[container.start].end, toks[container.end - 1].ofs

        if idx < len(elements) - 1:
            # Remove through the start of the next element, taking the separating comma and trivia with it.
            return node.ofs, elements[idx + 1].ofs

        if self._line_first_idx(node.start) is not None:
            # The last element, on its own line: remove the whole line, including its comma and any comment.
            start = self._line_start_ofs(node.start)
            content_end, nl_idx = self._line_end(node.end - 1, skip_comma=True)
            if nl_idx is not None:
                return start, toks[nl_idx].end
            return start, content_end

        # The last element, sharing a line with the previous: remove from the end of the previous element through this
        # one, its comma, and any comment on its line.
        i = node.end
        last = i
        while i < container.end - 1 and toks[i].kind in (TomlTokenKinds.WS, TomlTokenKinds.COMMA, TomlTokenKinds.COMMENT):  # noqa: E501
            if toks[i].kind != TomlTokenKinds.WS:
                last = i + 1
            i += 1
        return elements[idx - 1].end_ofs, toks[last - 1].end

    def _removal_span(self, node: TomlValueNode) -> ta.Tuple[int, int]:
        if isinstance(node, TomlTableNode):
            return self._table_removal_span(node)

        parent = self._parents[id(node)]

        if isinstance(parent, TomlKeyValueNode):
            gp = self._parents[id(parent)]
            if isinstance(gp, TomlTableNode):
                return self._statement_removal_span(parent)
            if isinstance(gp, TomlInlineTableNode):
                return self._inline_removal_span(gp, gp.pairs, gp.pairs.index(parent))

        elif isinstance(parent, TomlArrayNode):
            return self._inline_removal_span(parent, parent.items, parent.items.index(node))

        raise TomlDocumentError(f'Cannot delete {node.path!r}')

    def _container_insert(
            self,
            container: TomlNode,
            elements: ta.Sequence[TomlNode],
            key_text: ta.Optional[str],
            value: ta.Any,
            r: TomlValueRenderer,
    ) -> 'TomlDocument':
        toks = self._tokens
        opener_end = toks[container.start].end
        closer_ofs = toks[container.end - 1].ofs
        single_line = self._is_single_line(container)

        def render(indent: str, like: ta.Optional[TomlToken]) -> str:
            text = r.render_value(value, like=like, indent=indent, inline_only=single_line)
            if key_text is not None:
                text = key_text + ' = ' + text
            return text

        if not elements:
            text = render(self._line_indent(container.start), None)
            if isinstance(container, TomlInlineTableNode):
                pad = r.style.inline_table_padding
                text = pad + text + pad
            return self.splice(opener_end, closer_ofs, text)

        last = elements[-1]

        # Mimic the quoting or number base of the preceding sibling where the new value is of a like type.
        like: ta.Optional[TomlToken] = None
        sib = last.value if isinstance(last, TomlKeyValueNode) else last
        if isinstance(sib, TomlScalarNode):
            st = sib.token
            if isinstance(value, str) and st.kind in TomlTokenKinds.STRINGS:
                like = st
            elif isinstance(value, int) and not isinstance(value, bool) and st.kind == TomlTokenKinds.INTEGER:
                like = st

        text = render(self._line_indent(last.start), like)

        if self._line_first_idx(last.start) is not None:
            # Elements are laid out one per line: add a line after the last element's, ensuring it has a trailing comma.
            has_comma = False
            i = last.end
            while i < container.end - 1 and toks[i].kind in (TomlTokenKinds.WS, TomlTokenKinds.COMMA, TomlTokenKinds.COMMENT):  # noqa: E501
                if toks[i].kind == TomlTokenKinds.COMMA:
                    has_comma = True
                i += 1
            if i < container.end - 1 and toks[i].kind == TomlTokenKinds.NEWLINE:
                inserts = []
                if not has_comma:
                    inserts.append((last.end_ofs, ','))
                inserts.append((toks[i].end, self._indent_of(last.start) + text + ',' + toks[i].raw))
                return self._splice_inserts(inserts)

        # Elements share lines: insert directly after the last element, separated as the last two elements are.
        sep: ta.Optional[str] = None
        if len(elements) >= 2:
            between = toks[elements[-2].end:last.start]
            if not any(t.kind == TomlTokenKinds.COMMENT for t in between):
                sep = ''.join(t.raw for t in between)
        if sep is None:
            sep = ', '

        return self.splice(last.end_ofs, last.end_ofs, sep + text)

    def _append_statement(
            self,
            table: TomlTableNode,
            key_text: str,
            value: ta.Any,
            r: TomlValueRenderer,
    ) -> 'TomlDocument':
        toks = self._tokens
        nl = self.newline

        anchor: ta.Optional[int]
        if table.pairs:
            last = table.pairs[-1]
            anchor = last.end - 1
            indent = self._indent_of(last.start)
            eq = self._src[last.key.end_ofs:last.value.ofs]
        elif table.header is not None:
            anchor = table.header.end - 1
            indent = ''
            eq = ' = '
        else:
            anchor = None
            indent = ''
            eq = ' = '

        stmt = indent + key_text + eq + r.render_value(value, indent=indent)

        if anchor is not None:
            content_end, nl_idx = self._line_end(anchor)
            if nl_idx is not None:
                nl = toks[nl_idx].raw
                ofs = toks[nl_idx].end
                return self.splice(ofs, ofs, stmt + nl)
            return self.splice(content_end, content_end, nl + stmt)

        # The root table is empty.
        if len(self._tables) > 1:
            hdr = self._tables[1].header
            if hdr is None:
                raise TomlDocumentError('Non-root table has no header')
            ofs = self._line_start_ofs(hdr.start)
            return self.splice(ofs, ofs, stmt + nl + nl)

        src = self._src
        if not src:
            return self.splice(0, 0, stmt + nl)
        if src.endswith('\n'):
            return self.splice(len(src), len(src), stmt + nl)
        return self.splice(len(src), len(src), nl + stmt)

    #

    def set_value(self, path: ta.Iterable[TomlPathPart], value: ta.Any) -> 'TomlDocument':
        """
        Sets the value at `path`, returning the re-parsed document.

        An existing value is replaced in place, preserving its quoting, number base, or layout where possible. A new
        value is inserted as a `key = value` statement at the end of the nearest enclosing table present in the source
        (using a dotted key for any intermediate tables not present in the source), as a new pair at the end of an
        inline table, or as a new item at the end of an array when the path's last element equals the array's length.
        Values may be wrapped in `TomlInline`, `TomlMultiline`, or `TomlRaw` to control their rendering.
        """

        path = tuple(path)
        if not path:
            raise TomlDocumentError('Cannot set the root table')

        r = self._renderer()

        node = self._by_path.get(path)
        if node is not None:
            if isinstance(node, TomlTableNode):
                raise TomlDocumentError(f'Cannot replace table {path!r} with a value')
            like: ta.Union[TomlToken, TomlNode] = node.token if isinstance(node, TomlScalarNode) else node
            enc = self._enclosing_container(node)
            text = r.render_value(
                value,
                like=like,
                indent=self._line_indent(node.start),
                inline_only=enc is not None and self._is_single_line(enc),
            )
            return self.replace_node(node, text)

        # Find the innermost node on the path which is present in the source. The root table always is.
        i = len(path) - 1
        parent: ta.Optional[TomlValueNode] = None
        while i >= 0:
            parent = self._by_path.get(path[:i])
            if parent is not None:
                break
            i -= 1
        if parent is None:
            raise TomlDocumentError('No root table')
        rest = path[i:]

        if isinstance(parent, TomlArrayNode):
            if len(rest) != 1 or rest[0] != len(parent.items):
                raise TomlDocumentError(f'Can only append to array {parent.path!r} at index {len(parent.items)}')
            return self._container_insert(parent, parent.items, None, value, r)

        if not all(isinstance(p, str) for p in rest):
            raise TomlDocumentError(f'Cannot address into an array of tables at {path!r}')
        key_text = r.render_key(rest)

        if isinstance(parent, TomlInlineTableNode):
            return self._container_insert(parent, parent.pairs, key_text, value, r)

        if isinstance(parent, TomlTableNode):
            return self._append_statement(parent, key_text, value, r)

        raise TomlDocumentError(f'Cannot set {path!r} within the value at {parent.path!r}')

    def delete_path(self, path: ta.Iterable[TomlPathPart]) -> 'TomlDocument':
        """
        Deletes the value at `path`, and everything beneath it, from the source, returning the re-parsed document.
        Key/value statements are removed with their lines, table sections with their trailing blank lines, and inline
        table pairs and array items with their separating commas.
        """

        path = tuple(path)
        if not path:
            raise TomlDocumentError('Cannot delete the root table')

        n = len(path)
        spans = [
            self._removal_span(node)
            for p, node in self._by_path.items()
            if p[:n] == path
        ]
        if not spans:
            raise TomlDocumentError(f'No value at {path!r}')

        return self._splice_removals(spans)

    def add_table(
            self,
            path: ta.Iterable[ta.Any],
            values: ta.Optional[ta.Mapping[ta.Any, ta.Any]] = None,
            *,
            array: bool = False,
            after: ta.Optional[ta.Iterable[TomlPathPart]] = None,
            comments: ta.Optional[ta.Sequence[str]] = None,
    ) -> 'TomlDocument':
        """
        Adds a `[path]` (or, if `array`, a `[[path]]`) section with the given key/value statements, preceded by any
        given comment lines, and returns the re-parsed document. The section is placed directly after the table at
        `after` if given, else at the end of the document, separated from its neighbors by the style's blank lines
        between tables.
        """

        key = tuple(path)
        if not key or not all(isinstance(p, (str, TomlRaw)) for p in key):
            raise TomlDocumentError('Table paths must be non-empty sequences of strings')

        r = self._renderer()
        nl = self.newline
        sep = nl * r.style.blank_lines_between_tables

        lines = [r.render_comment(c) for c in (comments or ())]
        lines.append(('[[' if array else '[') + r.render_key(key) + (']]' if array else ']'))
        for k, v in (values or {}).items():
            lines.append(f'{r.render_key_part(k)} = {r.render_value(v)}')
        text = nl.join(lines) + nl

        src = self._src

        if after is not None:
            tbl = self.table_at_path(after)
            if tbl is None:
                raise TomlDocumentError(f'No table at {tuple(after)!r}')

            if tbl.start < tbl.end:
                content_end, nl_idx = self._line_end(tbl.end - 1)
                if nl_idx is not None:
                    ofs = self._tokens[nl_idx].end
                    return self.splice(ofs, ofs, sep + text)
                return self.splice(content_end, content_end, nl + sep + text)

            # The root table is empty: place the section before the first header, if there is one.
            if len(self._tables) > 1:
                hdr = self._tables[1].header
                if hdr is None:
                    raise TomlDocumentError('Non-root table has no header')
                ofs = self._line_start_ofs(hdr.start)
                return self.splice(ofs, ofs, text + sep)

        if not src.strip():
            return self.splice(len(src), len(src), text)

        tail = 0
        s = src
        while s.endswith(nl):
            s = s[:-len(nl)]
            tail += 1
        if tail == 0:
            prefix = nl + sep
        else:
            prefix = nl * max(0, 1 + r.style.blank_lines_between_tables - tail)
        return self.splice(len(src), len(src), prefix + text)


##


class TomlDocumentBuilder:
    """
    Receives tokens and structural events from a `TomlParser` and assembles the nodes of a `TomlDocument`.

    Scalar value nodes are inferred from tokens: a scalar-kinded token arriving while the innermost open structure is a
    key/value pair (whose key must then be complete, keys being parsed within their own structure) or an array is that
    structure's value.
    """

    class _Frame:
        def __init__(self, kind: str, start: int, path: TomlPath = ()) -> None:
            super().__init__()

            self.kind = kind
            self.start = start
            self.path = path

            self.key: ta.Optional[TomlKeyNode] = None
            self.header: ta.Optional[TomlTableHeaderNode] = None
            self.value: ta.Any = None
            self.node: ta.Optional[TomlValueNode] = None
            self.children: ta.List[ta.Any] = []

    def __init__(self, data: ta.Dict[str, ta.Any]) -> None:
        super().__init__()

        self._data = data
        self.tokens: ta.List[TomlToken] = []
        self.tables: ta.List[TomlTableNode] = []
        self.is_done = False

        root = self._Frame('table', 0)
        root.value = data
        self._stack: ta.List[TomlDocumentBuilder._Frame] = [root]

    def _child_path(self, fr: '_Frame') -> TomlPath:
        if fr.kind == 'array':
            return (*fr.path, len(fr.children))
        return fr.path

    def _add_value(self, fr: '_Frame', node: TomlValueNode) -> None:
        if fr.kind == 'array':
            fr.children.append(node)
        else:
            fr.node = node

    def _resolve_table_path(self, key: TomlKey) -> TomlPath:
        path: ta.List[TomlPathPart] = []
        cont: ta.Any = self._data
        for k in key:
            path.append(k)
            cont = cont[k]
            if isinstance(cont, list):
                idx = len(cont) - 1
                path.append(idx)
                cont = cont[idx]
        return tuple(path)

    #

    def token(self, tok: TomlToken) -> None:
        self.tokens.append(tok)

        if tok.kind in TomlTokenKinds.SCALARS:
            fr = self._stack[-1]
            if fr.kind in ('kv', 'array'):
                idx = len(self.tokens) - 1
                node = TomlScalarNode(
                    start=idx,
                    end=idx + 1,
                    tokens=self.tokens,
                    path=self._child_path(fr),
                    value=tok.value,
                )
                self._add_value(fr, node)

    def begin_key(self) -> None:
        self._stack.append(self._Frame('key', len(self.tokens)))

    def end_key(self, key: TomlKey) -> None:
        fr = self._stack.pop()
        end = len(self.tokens)
        while end > fr.start and self.tokens[end - 1].kind in TomlTokenKinds.TRIVIA:
            end -= 1
        node = TomlKeyNode(start=fr.start, end=end, tokens=self.tokens, key=key)
        parent = self._stack[-1]
        parent.key = node
        if parent.kind == 'kv':
            parent.path = (*parent.path, *key)

    def begin_key_value(self) -> None:
        container = self._stack[-1]
        self._stack.append(self._Frame('kv', len(self.tokens), container.path))

    def end_key_value(self, key: TomlKey, value: ta.Any) -> None:
        fr = self._stack.pop()
        if fr.key is None or fr.node is None:
            raise TomlDocumentError('Incomplete key/value pair')
        node = TomlKeyValueNode(start=fr.start, end=len(self.tokens), tokens=self.tokens, key=fr.key, value=fr.node)
        self._stack[-1].children.append(node)

    def begin_array(self) -> None:
        fr = self._stack[-1]
        self._stack.append(self._Frame('array', len(self.tokens), self._child_path(fr)))

    def end_array(self, value: list) -> None:
        fr = self._stack.pop()
        node = TomlArrayNode(
            start=fr.start,
            end=len(self.tokens),
            tokens=self.tokens,
            path=fr.path,
            value=value,
            items=tuple(fr.children),
        )
        self._add_value(self._stack[-1], node)

    def begin_inline_table(self) -> None:
        fr = self._stack[-1]
        self._stack.append(self._Frame('inline_table', len(self.tokens), self._child_path(fr)))

    def end_inline_table(self, value: dict) -> None:
        fr = self._stack.pop()
        node = TomlInlineTableNode(
            start=fr.start,
            end=len(self.tokens),
            tokens=self.tokens,
            path=fr.path,
            value=value,
            pairs=tuple(fr.children),
        )
        self._add_value(self._stack[-1], node)

    def _finish_table(self) -> None:
        fr = self._stack.pop()
        if fr.header is None and fr.children:
            start = fr.children[0].start
        else:
            start = fr.start
        if fr.children:
            end = fr.children[-1].end
        elif fr.header is not None:
            end = fr.header.end
        else:
            end = start
        self.tables.append(TomlTableNode(
            start=start,
            end=end,
            tokens=self.tokens,
            path=fr.path,
            value=fr.value,
            header=fr.header,
            pairs=tuple(fr.children),
        ))

    def begin_table_header(self) -> None:
        self._finish_table()
        self._stack.append(self._Frame('header', len(self.tokens)))

    def end_table_header(self, key: TomlKey, value: dict, *, is_array: bool) -> None:
        fr = self._stack.pop()
        if fr.key is None:
            raise TomlDocumentError('Incomplete table header')
        hdr = TomlTableHeaderNode(start=fr.start, end=len(self.tokens), tokens=self.tokens, key=fr.key, is_array=is_array)  # noqa: E501
        tf = self._Frame('table', hdr.start, self._resolve_table_path(key))
        tf.header = hdr
        tf.value = value
        self._stack.append(tf)

    def end_document(self) -> None:
        self._finish_table()
        self.is_done = True


##


class TomlParser:
    def __init__(
            self,
            src: str,
            *,
            parse_float: TomlParseFloat = float,
            build_document: bool = False,
    ) -> None:
        super().__init__()

        self.raw_src = src

        # The spec allows converting "\r\n" to "\n", even in string literals. Let's do so to simplify parsing. The
        # normalized positions of the removed carriage returns are remembered so that emitted tokens can map back to,
        # and quote exactly, the original source.
        cr_positions: ta.List[int] = []
        i = src.find('\r\n')
        while i >= 0:
            cr_positions.append(i - len(cr_positions))
            i = src.find('\r\n', i + 2)
        self._cr_positions = cr_positions
        self.src = src.replace('\r\n', '\n') if cr_positions else src

        self.parse_float = toml_make_safe_parse_float(parse_float)
        self._raw_parse_float = parse_float

        self.data = TomlNestedDict()
        self.flags = TomlFlags()
        self.pos = 0

        self._builder: ta.Optional[TomlDocumentBuilder] = None
        if build_document:
            self._builder = TomlDocumentBuilder(self.data.dict)
        self._tok_line = 1
        self._tok_line_start = 0

    ASCII_CTRL = frozenset(chr(i) for i in range(32)) | frozenset(chr(127))

    # Neither of these sets include quotation mark or backslash. They are currently handled as separate cases in the
    # parser functions.
    ILLEGAL_BASIC_STR_CHARS = ASCII_CTRL - frozenset('\t')
    ILLEGAL_MULTILINE_BASIC_STR_CHARS = ASCII_CTRL - frozenset('\t\n')

    ILLEGAL_LITERAL_STR_CHARS = ILLEGAL_BASIC_STR_CHARS
    ILLEGAL_MULTILINE_LITERAL_STR_CHARS = ILLEGAL_MULTILINE_BASIC_STR_CHARS

    ILLEGAL_COMMENT_CHARS = ILLEGAL_BASIC_STR_CHARS

    WS = frozenset(' \t')
    WS_AND_NEWLINE = WS | frozenset('\n')
    BARE_KEY_CHARS = frozenset(string.ascii_letters + string.digits + '-_')
    KEY_INITIAL_CHARS = BARE_KEY_CHARS | frozenset("\"'")
    HEXDIGIT_CHARS = frozenset(string.hexdigits)

    BASIC_STR_ESCAPE_REPLACEMENTS = types.MappingProxyType({
        '\\b': '\u0008',  # backspace
        '\\t': '\u0009',  # tab
        '\\n': '\u000A',  # linefeed
        '\\f': '\u000C',  # form feed
        '\\r': '\u000D',  # carriage return
        '\\e': '\u001B',  # escape
        '\\"': '\u0022',  # quote
        '\\\\': '\u005C',  # backslash
    })

    #

    def document(self, *, style: ta.Optional[TomlStyle] = None) -> TomlDocument:
        """Returns the built `TomlDocument`. Only valid after `parse` on a parser constructed with `build_document`."""

        b = self._builder
        if b is None:
            raise TomlDocumentError('Parser was not constructed with build_document')
        if not b.is_done:
            raise TomlDocumentError('Document has not been parsed')
        return TomlDocument(
            self.raw_src,
            self.data.dict,
            b.tokens,
            b.tables,
            parse_float=self._raw_parse_float,
            style=style,
        )

    def raw_ofs(self, pos: TomlPos) -> int:
        """Maps a position in the normalized source to the corresponding offset in the original source."""

        if not self._cr_positions:
            return pos
        return pos + bisect.bisect_left(self._cr_positions, pos)

    def _emit(self, kind: str, start: TomlPos, end: TomlPos, value: ta.Any = None) -> None:
        b = self._builder
        if b is None:
            return

        ofs = self.raw_ofs(start)
        raw = self.raw_src[ofs:self.raw_ofs(end)]
        b.token(TomlToken(kind, raw, value, ofs, self._tok_line, start - self._tok_line_start + 1))

        nls = self.src.count('\n', start, end)
        if nls:
            self._tok_line += nls
            self._tok_line_start = self.src.rindex('\n', start, end) + 1

    def _consume(self, n: int, kind: str, value: ta.Any = None) -> None:
        start = self.pos
        self.pos += n
        self._emit(kind, start, self.pos, value)

    #

    def parse(self) -> ta.Dict[str, ta.Any]:  # noqa: C901
        header: TomlKey = ()

        # Parse one statement at a time (typically means one line in TOML source)
        while True:
            # 1. Skip line leading whitespace
            self.skip_ws()

            # 2. Parse rules. Expect one of the following:
            #    - end of file
            #    - end of line
            #    - comment
            #    - key/value pair
            #    - append dict to list (and move to its namespace)
            #    - create dict (and move to its namespace)
            # Skip trailing whitespace when applicable.
            try:
                char = self.src[self.pos]
            except IndexError:
                break

            if char == '\n':
                self._consume(1, TomlTokenKinds.NEWLINE)
                continue

            if char in self.KEY_INITIAL_CHARS:
                self.key_value_rule(header)
                self.skip_ws()

            elif char == '[':
                try:
                    second_char: ta.Optional[str] = self.src[self.pos + 1]
                except IndexError:
                    second_char = None

                self.flags.finalize_pending()

                if second_char == '[':
                    header = self.create_list_rule()
                else:
                    header = self.create_dict_rule()

                self.skip_ws()

            elif char != '#':
                raise self.suffixed_err('Invalid statement')

            # 3. Skip comment
            self.skip_comment()

            # 4. Expect end of line or end of file
            try:
                char = self.src[self.pos]
            except IndexError:
                break

            if char != '\n':
                raise self.suffixed_err('Expected newline or end of document after a statement')

            self._consume(1, TomlTokenKinds.NEWLINE)

        b = self._builder
        if b is not None:
            b.end_document()

        return self.data.dict

    def skip_chars(self, chars: ta.Iterable[str]) -> None:
        try:
            while self.src[self.pos] in chars:
                self.pos += 1
        except IndexError:
            pass

    def skip_ws(self) -> None:
        start = self.pos
        try:
            while self.src[self.pos] in self.WS:
                self.pos += 1
        except IndexError:
            pass
        if self.pos != start:
            self._emit(TomlTokenKinds.WS, start, self.pos)

    def skip_until(
            self,
            expect: str,
            *,
            error_on: ta.FrozenSet[str],
            error_on_eof: bool,
    ) -> None:
        try:
            new_pos = self.src.index(expect, self.pos)
        except ValueError:
            new_pos = len(self.src)
            if error_on_eof:
                raise self.suffixed_err(f'Expected {expect!r}', pos=new_pos) from None

        if not error_on.isdisjoint(self.src[self.pos:new_pos]):
            while self.src[self.pos] not in error_on:
                self.pos += 1

            raise self.suffixed_err(f'Found invalid character {self.src[self.pos]!r}')

        self.pos = new_pos

    def skip_comment(self) -> None:
        try:
            char: ta.Optional[str] = self.src[self.pos]
        except IndexError:
            char = None

        if char == '#':
            start = self.pos
            self.pos += 1
            self.skip_until(
                '\n',
                error_on=self.ILLEGAL_COMMENT_CHARS,
                error_on_eof=False,
            )
            self._emit(TomlTokenKinds.COMMENT, start, self.pos)

    def skip_comments_and_array_ws(self) -> None:
        # Kept shallow (no helper calling another helper) to preserve the recursion budget of deeply nested arrays.
        while True:
            pos_before_skip = self.pos
            self.skip_ws()
            if self.src.startswith('\n', self.pos):
                self._consume(1, TomlTokenKinds.NEWLINE)
                continue
            self.skip_comment()
            if self.pos == pos_before_skip:
                return

    def create_dict_rule(self) -> TomlKey:
        b = self._builder
        if b is not None:
            b.begin_table_header()

        self._consume(1, TomlTokenKinds.TABLE_OPEN)  # Skip "["
        self.skip_ws()
        key = self.parse_key()

        if self.flags.is_(key, TomlFlags.EXPLICIT_NEST) or self.flags.is_(key, TomlFlags.FROZEN):
            raise self.suffixed_err(f'Cannot declare {key} twice')

        self.flags.set(key, TomlFlags.EXPLICIT_NEST, recursive=False)

        try:
            nest = self.data.get_or_create_nest(key)
        except KeyError:
            raise self.suffixed_err('Cannot overwrite a value') from None

        if not self.src.startswith(']', self.pos):
            raise self.suffixed_err("Expected ']' at the end of a table declaration")

        self._consume(1, TomlTokenKinds.TABLE_CLOSE)

        if b is not None:
            b.end_table_header(key, nest, is_array=False)

        return key

    def create_list_rule(self) -> TomlKey:
        b = self._builder
        if b is not None:
            b.begin_table_header()

        self._consume(2, TomlTokenKinds.ARRAY_TABLE_OPEN)  # Skip "[["
        self.skip_ws()

        key = self.parse_key()

        if self.flags.is_(key, TomlFlags.FROZEN):
            raise self.suffixed_err(f'Cannot mutate immutable namespace {key}')

        # Free the namespace now that it points to another empty list item...
        self.flags.unset_all(key)

        # ...but this key precisely is still prohibited from table declaration
        self.flags.set(key, TomlFlags.EXPLICIT_NEST, recursive=False)

        try:
            nest = self.data.append_nest_to_list(key)
        except KeyError:
            raise self.suffixed_err('Cannot overwrite a value') from None

        if not self.src.startswith(']]', self.pos):
            raise self.suffixed_err("Expected ']]' at the end of an array declaration")

        self._consume(2, TomlTokenKinds.ARRAY_TABLE_CLOSE)

        if b is not None:
            b.end_table_header(key, nest, is_array=True)

        return key

    def key_value_rule(self, header: TomlKey) -> None:
        b = self._builder
        if b is not None:
            b.begin_key_value()

        key, value = self.parse_key_value_pair()
        key_parent, key_stem = key[:-1], key[-1]
        abs_key_parent = header + key_parent

        relative_path_cont_keys = (header + key[:i] for i in range(1, len(key)))
        for cont_key in relative_path_cont_keys:
            # Check that dotted key syntax does not redefine an existing table
            if self.flags.is_(cont_key, TomlFlags.EXPLICIT_NEST):
                raise self.suffixed_err(f'Cannot redefine namespace {cont_key}')

            # Containers in the relative path can't be opened with the table syntax or dotted key/value syntax in
            # following table sections.
            self.flags.add_pending(cont_key, TomlFlags.EXPLICIT_NEST)

        if self.flags.is_(abs_key_parent, TomlFlags.FROZEN):
            raise self.suffixed_err(f'Cannot mutate immutable namespace {abs_key_parent}')

        try:
            nest = self.data.get_or_create_nest(abs_key_parent)
        except KeyError:
            raise self.suffixed_err('Cannot overwrite a value') from None

        if key_stem in nest:
            raise self.suffixed_err('Cannot overwrite a value')

        # Mark inline table and array namespaces recursively immutable
        if isinstance(value, (dict, list)):
            self.flags.set(header + key, TomlFlags.FROZEN, recursive=True)

        nest[key_stem] = value

        if b is not None:
            b.end_key_value(key, value)

    def parse_key_value_pair(self) -> ta.Tuple[TomlKey, ta.Any]:
        key = self.parse_key()

        try:
            char: ta.Optional[str] = self.src[self.pos]
        except IndexError:
            char = None

        if char != '=':
            raise self.suffixed_err("Expected '=' after a key in a key/value pair")

        self._consume(1, TomlTokenKinds.EQUALS)
        self.skip_ws()

        value = self.parse_value()
        return key, value

    def parse_key(self) -> TomlKey:
        b = self._builder
        if b is not None:
            b.begin_key()

        key_part = self.parse_key_part()
        key: TomlKey = (key_part,)

        self.skip_ws()

        while True:
            try:
                char: ta.Optional[str] = self.src[self.pos]
            except IndexError:
                char = None

            if char != '.':
                break

            self._consume(1, TomlTokenKinds.DOT)
            self.skip_ws()

            key_part = self.parse_key_part()
            key += (key_part,)

            self.skip_ws()

        if b is not None:
            b.end_key(key)

        return key

    def parse_key_part(self) -> str:
        try:
            char: ta.Optional[str] = self.src[self.pos]
        except IndexError:
            char = None

        if char in self.BARE_KEY_CHARS:
            start_pos = self.pos
            self.skip_chars(self.BARE_KEY_CHARS)
            key_part = self.src[start_pos:self.pos]
            self._emit(TomlTokenKinds.BARE_KEY, start_pos, self.pos, key_part)
            return key_part

        if char == "'":
            return self.parse_literal_str()

        if char == '"':
            return self.parse_one_line_basic_str()

        raise self.suffixed_err('Invalid initial character for a key part')

    def parse_one_line_basic_str(self) -> str:
        start = self.pos
        self.pos += 1
        result = self.parse_basic_str(multiline=False)
        self._emit(TomlTokenKinds.BASIC_STRING, start, self.pos, result)
        return result

    def parse_array(self) -> list:
        b = self._builder
        if b is not None:
            b.begin_array()

        self._consume(1, TomlTokenKinds.ARRAY_OPEN)
        array: list = []

        self.skip_comments_and_array_ws()
        if self.src.startswith(']', self.pos):
            self._consume(1, TomlTokenKinds.ARRAY_CLOSE)
            return self._end_array(array)

        while True:
            val = self.parse_value()
            array.append(val)
            self.skip_comments_and_array_ws()

            c = self.src[self.pos:self.pos + 1]
            if c == ']':
                self._consume(1, TomlTokenKinds.ARRAY_CLOSE)
                return self._end_array(array)

            if c != ',':
                raise self.suffixed_err('Unclosed array')

            self._consume(1, TomlTokenKinds.COMMA)

            self.skip_comments_and_array_ws()

            if self.src.startswith(']', self.pos):
                self._consume(1, TomlTokenKinds.ARRAY_CLOSE)
                return self._end_array(array)

    def _end_array(self, array: list) -> list:
        b = self._builder
        if b is not None:
            b.end_array(array)
        return array

    def parse_inline_table(self) -> dict:  # noqa: C901
        b = self._builder
        if b is not None:
            b.begin_inline_table()

        self._consume(1, TomlTokenKinds.INLINE_TABLE_OPEN)
        nested_dict = TomlNestedDict()
        flags = TomlFlags()

        self.skip_comments_and_array_ws()

        if self.src.startswith('}', self.pos):
            self._consume(1, TomlTokenKinds.INLINE_TABLE_CLOSE)
            return self._end_inline_table(nested_dict.dict)

        while True:
            if b is not None:
                b.begin_key_value()

            key, value = self.parse_key_value_pair()
            key_parent, key_stem = key[:-1], key[-1]

            if flags.is_(key, TomlFlags.FROZEN):
                raise self.suffixed_err(f'Cannot mutate immutable namespace {key}')

            try:
                nest = nested_dict.get_or_create_nest(key_parent, access_lists=False)
            except KeyError:
                raise self.suffixed_err('Cannot overwrite a value') from None

            if key_stem in nest:
                raise self.suffixed_err(f'Duplicate inline table key {key_stem!r}')

            nest[key_stem] = value

            if b is not None:
                b.end_key_value(key, value)

            self.skip_comments_and_array_ws()

            c = self.src[self.pos:self.pos + 1]
            if c == '}':
                self._consume(1, TomlTokenKinds.INLINE_TABLE_CLOSE)
                return self._end_inline_table(nested_dict.dict)

            if c != ',':
                raise self.suffixed_err('Unclosed inline table')

            self._consume(1, TomlTokenKinds.COMMA)
            self.skip_comments_and_array_ws()

            if self.src.startswith('}', self.pos):
                self._consume(1, TomlTokenKinds.INLINE_TABLE_CLOSE)
                return self._end_inline_table(nested_dict.dict)

            if isinstance(value, (dict, list)):
                flags.set(key, TomlFlags.FROZEN, recursive=True)

    def _end_inline_table(self, dct: dict) -> dict:
        b = self._builder
        if b is not None:
            b.end_inline_table(dct)
        return dct

    def parse_basic_str_escape(self, multiline: bool = False) -> str:
        escape_id = self.src[self.pos:self.pos + 2]
        self.pos += 2

        if multiline and escape_id in {'\\ ', '\\\t', '\\\n'}:
            # Skip whitespace until next non-whitespace character or end of the doc. Error if non-whitespace is found
            # before newline.
            if escape_id != '\\\n':
                self.skip_chars(self.WS)

                try:
                    char = self.src[self.pos]
                except IndexError:
                    return ''

                if char != '\n':
                    raise self.suffixed_err("Unescaped '\\' in a string")

                self.pos += 1

            self.skip_chars(self.WS_AND_NEWLINE)
            return ''

        if escape_id == '\\x':
            return self.parse_hex_char(2)

        if escape_id == '\\u':
            return self.parse_hex_char(4)

        if escape_id == '\\U':
            return self.parse_hex_char(8)

        try:
            return self.BASIC_STR_ESCAPE_REPLACEMENTS[escape_id]
        except KeyError:
            raise self.suffixed_err("Unescaped '\\' in a string") from None

    def parse_basic_str_escape_multiline(self) -> str:
        return self.parse_basic_str_escape(multiline=True)

    @classmethod
    def is_unicode_scalar_value(cls, codepoint: int) -> bool:
        return (0 <= codepoint <= 55295) or (57344 <= codepoint <= 1114111)

    def parse_hex_char(self, hex_len: int) -> str:
        hex_str = self.src[self.pos:self.pos + hex_len]

        if len(hex_str) != hex_len or not self.HEXDIGIT_CHARS.issuperset(hex_str):
            raise self.suffixed_err('Invalid hex value')

        self.pos += hex_len
        hex_int = int(hex_str, 16)

        if not self.is_unicode_scalar_value(hex_int):
            raise self.suffixed_err('Escaped character is not a Unicode scalar value')

        return chr(hex_int)

    def parse_literal_str(self) -> str:
        start = self.pos
        self.pos += 1  # Skip starting apostrophe
        start_pos = self.pos
        self.skip_until("'", error_on=self.ILLEGAL_LITERAL_STR_CHARS, error_on_eof=True)
        end_pos = self.pos
        self.pos += 1  # Skip ending apostrophe
        result = self.src[start_pos:end_pos]
        self._emit(TomlTokenKinds.LITERAL_STRING, start, self.pos, result)
        return result

    def parse_multiline_str(self, *, literal: bool) -> str:
        start = self.pos
        self.pos += 3
        if self.src.startswith('\n', self.pos):
            self.pos += 1

        if literal:
            delim = "'"
            start_pos = self.pos
            self.skip_until(
                "'''",
                error_on=self.ILLEGAL_MULTILINE_LITERAL_STR_CHARS,
                error_on_eof=True,
            )
            result = self.src[start_pos:self.pos]
            self.pos += 3

        else:
            delim = '"'
            result = self.parse_basic_str(multiline=True)

        # Add at maximum two extra apostrophes/quotes if the end sequence is 4 or 5 chars long instead of just 3.
        if self.src.startswith(delim, self.pos):
            self.pos += 1
            if self.src.startswith(delim, self.pos):
                self.pos += 1
                result += delim * 2
            else:
                result += delim

        self._emit(
            TomlTokenKinds.ML_LITERAL_STRING if literal else TomlTokenKinds.ML_BASIC_STRING,
            start,
            self.pos,
            result,
        )
        return result

    def parse_basic_str(self, *, multiline: bool) -> str:
        if multiline:
            error_on = self.ILLEGAL_MULTILINE_BASIC_STR_CHARS
            parse_escapes = self.parse_basic_str_escape_multiline
        else:
            error_on = self.ILLEGAL_BASIC_STR_CHARS
            parse_escapes = self.parse_basic_str_escape

        result = ''
        start_pos = self.pos
        while True:
            try:
                char = self.src[self.pos]
            except IndexError:
                raise self.suffixed_err('Unterminated string') from None

            if char == '"':
                if not multiline:
                    end_pos = self.pos
                    self.pos += 1
                    return result + self.src[start_pos:end_pos]

                if self.src.startswith('"""', self.pos):
                    end_pos = self.pos
                    self.pos += 3
                    return result + self.src[start_pos:end_pos]

                self.pos += 1
                continue

            if char == '\\':
                result += self.src[start_pos:self.pos]
                parsed_escape = parse_escapes()
                result += parsed_escape
                start_pos = self.pos
                continue

            if char in error_on:
                raise self.suffixed_err(f'Illegal character {char!r}')

            self.pos += 1

    def parse_value(self) -> ta.Any:  # noqa: C901
        try:
            char: ta.Optional[str] = self.src[self.pos]
        except IndexError:
            char = None

        # IMPORTANT: order conditions based on speed of checking and likelihood

        # Basic strings
        if char == '"':
            if self.src.startswith('"""', self.pos):
                return self.parse_multiline_str(literal=False)
            return self.parse_one_line_basic_str()

        # Literal strings
        if char == "'":
            if self.src.startswith("'''", self.pos):
                return self.parse_multiline_str(literal=True)
            return self.parse_literal_str()

        # Booleans
        if char == 't':
            if self.src.startswith('true', self.pos):
                self._consume(4, TomlTokenKinds.BOOL, True)
                return True

        if char == 'f':
            if self.src.startswith('false', self.pos):
                self._consume(5, TomlTokenKinds.BOOL, False)
                return False

        # Arrays
        if char == '[':
            return self.parse_array()

        # Inline tables
        if char == '{':
            return self.parse_inline_table()

        # Dates and times
        datetime_match = self.RE_DATETIME.match(self.src, self.pos)
        if datetime_match:
            try:
                datetime_obj = self.match_to_datetime(datetime_match)
            except ValueError as e:
                raise self.suffixed_err('Invalid date or datetime') from e

            if isinstance(datetime_obj, datetime.datetime):
                if datetime_obj.tzinfo is not None:
                    kind = TomlTokenKinds.OFFSET_DATETIME
                else:
                    kind = TomlTokenKinds.LOCAL_DATETIME
            else:
                kind = TomlTokenKinds.LOCAL_DATE

            self._consume(datetime_match.end() - self.pos, kind, datetime_obj)
            return datetime_obj

        localtime_match = self.RE_LOCALTIME.match(self.src, self.pos)
        if localtime_match:
            localtime_obj = self.match_to_localtime(localtime_match)
            self._consume(localtime_match.end() - self.pos, TomlTokenKinds.LOCAL_TIME, localtime_obj)
            return localtime_obj

        # Integers and "normal" floats. The regex will greedily match any type starting with a decimal char, so needs to
        # be located after handling of dates and times.
        number_match = self.RE_NUMBER.match(self.src, self.pos)
        if number_match:
            number_obj = self.match_to_number(number_match, self.parse_float)
            self._consume(
                number_match.end() - self.pos,
                TomlTokenKinds.FLOAT if number_match.group('floatpart') else TomlTokenKinds.INTEGER,
                number_obj,
            )
            return number_obj

        # Special floats
        first_three = self.src[self.pos:self.pos + 3]
        if first_three in {'inf', 'nan'}:
            float_obj = self.parse_float(first_three)
            self._consume(3, TomlTokenKinds.FLOAT, float_obj)
            return float_obj

        first_four = self.src[self.pos:self.pos + 4]
        if first_four in {'-inf', '+inf', '-nan', '+nan'}:
            float_obj = self.parse_float(first_four)
            self._consume(4, TomlTokenKinds.FLOAT, float_obj)
            return float_obj

        raise self.suffixed_err('Invalid value')

    def suffixed_err(self, msg: str, *, pos: ta.Optional[TomlPos] = None) -> TomlDecodeError:
        """Return a `TomlDecodeError` where error message is suffixed with coordinates in source."""

        if pos is None:
            pos = self.pos
        return TomlDecodeError(msg, self.src, pos)

    _TIME_RE_STR = r"""
        ([01][0-9]|2[0-3])             # hours
        :([0-5][0-9])                  # minutes
        (?:
            :([0-5][0-9])              # optional seconds
            (?:\.([0-9]{1,6})[0-9]*)?  # optional fractions of a second
        )?
    """

    RE_NUMBER = re.compile(
        r"""
        0
        (?:
            x[0-9A-Fa-f](?:_?[0-9A-Fa-f])*   # hex
            |
            b[01](?:_?[01])*                 # bin
            |
            o[0-7](?:_?[0-7])*               # oct
        )
        |
        [+-]?(?:0|[1-9](?:_?[0-9])*)         # dec, integer part
        (?P<floatpart>
            (?:\.[0-9](?:_?[0-9])*)?         # optional fractional part
            (?:[eE][+-]?[0-9](?:_?[0-9])*)?  # optional exponent part
        )
        """,
        flags=re.VERBOSE,
    )

    RE_LOCALTIME = re.compile(_TIME_RE_STR, flags=re.VERBOSE)

    RE_DATETIME = re.compile(
        rf"""
        ([0-9]{{4}})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])  # date, e.g. 1988-10-27
        (?:
            [Tt ]
            {_TIME_RE_STR}
            (?:([Zz])|([+-])([01][0-9]|2[0-3]):([0-5][0-9]))?  # optional time offset
        )?
        """,
        flags=re.VERBOSE,
    )

    @classmethod
    def match_to_datetime(cls, match: re.Match) -> ta.Union[datetime.datetime, datetime.date]:
        """
        Convert a `RE_DATETIME` match to `datetime.datetime` or `datetime.date`.

        Raises ValueError if the match does not correspond to a valid date or datetime.
        """

        (
            year_str,
            month_str,
            day_str,
            hour_str,
            minute_str,
            sec_str,
            micros_str,
            zulu_time,
            offset_sign_str,
            offset_hour_str,
            offset_minute_str,
        ) = match.groups()

        year, month, day = int(year_str), int(month_str), int(day_str)

        if hour_str is None:
            return datetime.date(year, month, day)

        hour, minute = int(hour_str), int(minute_str)
        sec = int(sec_str) if sec_str else 0

        micros = int(micros_str.ljust(6, '0')) if micros_str else 0

        if offset_sign_str:
            tz: ta.Optional[datetime.tzinfo] = toml_cached_tz(
                offset_hour_str, offset_minute_str, offset_sign_str,
            )
        elif zulu_time:
            tz = datetime.timezone.utc
        else:  # local date-time
            tz = None

        return datetime.datetime(year, month, day, hour, minute, sec, micros, tzinfo=tz)

    @classmethod
    def match_to_localtime(cls, match: re.Match) -> datetime.time:
        hour_str, minute_str, sec_str, micros_str = match.groups()
        sec = int(sec_str) if sec_str else 0
        micros = int(micros_str.ljust(6, '0')) if micros_str else 0
        return datetime.time(int(hour_str), int(minute_str), sec, micros)

    @classmethod
    def match_to_number(cls, match: re.Match, parse_float: TomlParseFloat) -> ta.Any:
        if match.group('floatpart'):
            return parse_float(match.group())
        return int(match.group(), 0)


##


def toml_load(fp: ta.BinaryIO, /, *, parse_float: TomlParseFloat = float) -> ta.Dict[str, ta.Any]:
    """Parse TOML from a binary file object."""

    b = fp.read()
    try:
        s = b.decode()
    except AttributeError:
        raise TypeError("File must be opened in binary mode, e.g. use `open('foo.toml', 'rb')`") from None
    return toml_loads(s, parse_float=parse_float)


def toml_loads(s: str, /, *, parse_float: TomlParseFloat = float) -> ta.Dict[str, ta.Any]:
    """Parse TOML from a string."""

    if not isinstance(s, str):
        raise TypeError(f"Expected str object, not '{type(s).__qualname__}'")

    return TomlParser(s, parse_float=parse_float).parse()


def toml_parse_document(
        s: str,
        /,
        *,
        parse_float: TomlParseFloat = float,
        style: ta.Optional[TomlStyle] = None,
) -> TomlDocument:
    """Parse TOML from a string into a full-fidelity `TomlDocument`, whose edits render new values per `style`."""

    if not isinstance(s, str):
        raise TypeError(f"Expected str object, not '{type(s).__qualname__}'")

    parser = TomlParser(s, parse_float=parse_float, build_document=True)
    parser.parse()
    return parser.document(style=style)
