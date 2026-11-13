# ruff: noqa: A002
# Copyright © 2009/2023 Andrey Vlasovskikh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""A regexp-based tokenizer producing sequences of `Token` objects for the parsing combinators to consume."""
import re
import typing as ta

from omcore import check
from omcore import dataclasses as dc


# A (line, column) position.
_Place: ta.TypeAlias = tuple[int, int]

# A token type and the positional arguments to `re.compile()`.
_LegacyTokenSpec: ta.TypeAlias = tuple[str, tuple]


##


class LexerError(Exception):
    def __init__(self, place: _Place, msg: str) -> None:
        super().__init__(place, msg)

        self.place = place
        self.msg = msg

    def __str__(self) -> str:
        line, pos = self.place
        return f'cannot tokenize data: {line},{pos}: "{self.msg}"'


@dc.dataclass(frozen=True, repr=False)
class TokenSpec:
    """
    A token specification for generating a lexer via `make_tokenizer()`: a user-defined token `type` (e.g. `"name"`,
    `"number"`, `"operator"`), the regexp `pattern` matching it, and the regexp `flags` to compile the pattern with.
    """

    type: str
    pattern: str
    flags: int = 0

    def __repr__(self) -> str:
        return f'TokenSpec({self.type!r}, {self.pattern!r}, {self.flags!r})'


@dc.dataclass(frozen=True, eq=False, repr=False)
class Token:  # noqa: PLW1641
    """
    A token object that represents a substring of certain type in your text: its user-defined `type` (e.g. `"name"`,
    `"number"`, `"operator"`), its text `value`, and optionally its `start` and `end` positions.

    Tokens compare equal by their type and value alone, regardless of their positions.
    """

    type: str
    value: str
    start: _Place | None = None
    end: _Place | None = None

    def __repr__(self) -> str:
        return f'Token({self.type!r}, {self.value!r})'

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Token) and
            self.type == other.type and
            self.value == other.value
        )

    def _pos_str(self) -> str:
        if self.start is None or self.end is None:
            return ''

        sl, sp = self.start
        el, ep = self.end
        return f'{sl},{sp}-{el},{ep}:'

    def __str__(self) -> str:
        return f"{self._pos_str()} {self.type} '{self.value}'".strip()

    @property
    def name(self) -> str:
        return self.value

    def pformat(self) -> str:
        return f"{self._pos_str().ljust(20)} {self.type.ljust(14)} '{self.value}'"


def make_tokenizer(specs: ta.Sequence[TokenSpec | _LegacyTokenSpec]) -> ta.Callable[[str], ta.Iterable[Token]]:
    """
    Make a function that tokenizes text based on the regexp specs. The returned function takes a string and returns an
    iterable of `Token` objects, raising `LexerError` if it cannot tokenize the string according to its token specs.

    For legacy reasons, a token spec may also be a tuple of (type, args), where type sets the value of `Token.type` for
    the token, and args are the positional arguments for `re.compile()`: either just (pattern,) or (pattern, flags).

    >>> tokenize = make_tokenizer([
    ...     TokenSpec("space", r"\\s+"),
    ...     TokenSpec("id", r"\\w+"),
    ...     TokenSpec("op", r"[,!]"),
    ... ])
    >>> text = "Hello, World!"
    >>> [t for t in tokenize(text) if t.type != "space"]
    [Token('id', 'Hello'), Token('op', ','), Token('id', 'World'), Token('op', '!')]
    >>> text = "Bye?"
    >>> list(tokenize(text))
    Traceback (most recent call last):
        ...
    lexer.LexerError: cannot tokenize data: 1,4: "Bye?"
    """

    compiled: list[tuple[str, re.Pattern[str]]] = []
    for spec in specs:
        if isinstance(spec, TokenSpec):
            compiled.append((spec.type, re.compile(spec.pattern, spec.flags)))
        else:
            name, args = spec
            compiled.append((name, re.compile(*args)))

    def match_specs(s: str, i: int, position: _Place) -> Token:
        line, pos = position

        for type_name, regexp in compiled:
            if (m := regexp.match(s, i)) is None:
                continue

            value = m.group()
            nls = value.count('\n')
            n_line = line + nls
            if nls == 0:
                n_pos = pos + len(value)
            else:
                n_pos = len(value) - value.rfind('\n') - 1

            return Token(type_name, value, (line, pos + 1), (n_line, n_pos))

        err_line = s.splitlines()[line - 1]
        raise LexerError((line, pos + 1), err_line)

    def tokenize(s: str) -> ta.Iterator[Token]:
        length = len(s)
        line, pos = 1, 0
        i = 0

        while i < length:
            t = match_specs(s, i, (line, pos))
            yield t

            line, pos = check.not_none(t.end)
            i += len(t.value)

    return tokenize
