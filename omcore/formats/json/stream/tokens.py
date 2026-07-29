import re
import typing as ta

from .... import check


##


IdentTokenKind: ta.TypeAlias = ta.Literal['IDENT']

ValueTokenKind: ta.TypeAlias = ta.Literal[
    'STRING',
    'NUMBER',
]

VALUE_TOKEN_KINDS = frozenset(check.isinstance(a, str) for a in ta.get_args(ValueTokenKind))

ControlTokenKind: ta.TypeAlias = ta.Literal[
    'LBRACE',
    'RBRACE',
    'LBRACKET',
    'RBRACKET',
    'COMMA',
    'COLON',
]

SpaceTokenKind: ta.TypeAlias = ta.Literal['SPACE']

CommentTokenKind: ta.TypeAlias = ta.Literal['COMMENT']

TokenKind: ta.TypeAlias = ta.Union[  # noqa
    IdentTokenKind,
    ValueTokenKind,
    ControlTokenKind,
    SpaceTokenKind,
    CommentTokenKind,
]


#

ScalarValue: ta.TypeAlias = str | float | int | None

SCALAR_VALUE_TYPES: tuple[type, ...] = tuple(
    check.isinstance(e, type) if e is not None else type(None)
    for e in ta.get_args(ScalarValue)
)


##


# Field order matches Position - the bare tuple form is what the lexer stores on Tokens, as its construction is
# significantly cheaper than that of the NamedTuple (a single BUILD_TUPLE op, eligible for the freelist).
type PackedPosition = tuple[
    int,  # ofs
    int,  # line
    int,  # col
]


class Position(ta.NamedTuple):
    ofs: int
    line: int
    col: int


def unpack_position(p: PackedPosition) -> Position:
    return Position(*p)


class Token(ta.NamedTuple):
    kind: TokenKind
    value: ScalarValue
    raw: str | None

    packed_pos: PackedPosition

    @property
    def position(self) -> Position:
        return unpack_position(self.packed_pos)

    def __iter__(self):
        raise TypeError


##


# A match with any group present is a float, otherwise an int. Note: \d must be avoided as it matches unicode digits.
NUMBER_PAT = re.compile(r'-?(?:0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?')

CONTROL_TOKENS: ta.Mapping[str, TokenKind] = {
    '{': 'LBRACE',
    '}': 'RBRACE',
    '[': 'LBRACKET',
    ']': 'RBRACKET',
    ',': 'COMMA',
    ':': 'COLON',
}

CONST_IDENT_VALUES: ta.Mapping[str, str | float | None] = {
    'NaN': float('nan'),
    '-NaN': float('-nan'),  # distinguished in parsing even if indistinguishable in value
    'Infinity': float('inf'),
    '-Infinity': float('-inf'),

    'true': True,
    'false': False,
    'null': None,
}

MAX_CONST_IDENT_LEN = max(map(len, CONST_IDENT_VALUES))


##


SPACE_CHARS = ' \t\n\r'

EXPANDED_SPACE_CHARS = (
    '\u0009'
    '\u000A'
    '\u000B'
    '\u000C'
    '\u000D'
    '\u0020'
    '\u00A0'
    '\u2028'
    '\u2029'
    '\uFEFF'
    '\u1680'
    '\u2000'
    '\u2001'
    '\u2002'
    '\u2003'
    '\u2004'
    '\u2005'
    '\u2006'
    '\u2007'
    '\u2008'
    '\u2009'
    '\u200A'
    '\u202F'
    '\u205F'
    '\u3000'
)
