import json
import math
import re
import typing as ta

from ... import dataclasses as dc
from .errors import JqLexError


##


@dc.dataclass(frozen=True)
class Interpolation:
    source: str
    offset: int


StringTokenPart: ta.TypeAlias = str | Interpolation


@dc.dataclass(frozen=True)
class Token:
    kind: str
    value: ta.Any
    start: int
    end: int


_KEYWORDS: ta.Mapping[str, str] = {
    'and': 'AND',
    'as': 'AS',
    'break': 'BREAK',
    'catch': 'CATCH',
    'def': 'DEF',
    'elif': 'ELIF',
    'else': 'ELSE',
    'end': 'END',
    'foreach': 'FOREACH',
    'if': 'IF',
    'label': 'LABEL',
    'or': 'OR',
    'reduce': 'REDUCE',
    'then': 'THEN',
    'try': 'TRY',
}

_OPERATORS = (
    '?//',
    '//=',
    '!=',
    '==',
    '<=',
    '>=',
    '|=',
    '+=',
    '-=',
    '*=',
    '/=',
    '%=',
    '//',
    '..',
)

_SINGLE_TOKENS = frozenset('.?=;, :|+-*/%$<>()[]{}'.replace(' ', ''))
_IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z_0-9]*(?:::[A-Za-z_][A-Za-z_0-9]*)*')
_NUMBER = re.compile(r'(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?')


##


class Lexer:
    def __init__(self, source: str, *, offset: int = 0) -> None:
        super().__init__()

        self._source = source
        self._offset = offset
        self._index = 0

    def _raise(self, message: str, index: int | None = None) -> ta.NoReturn:
        raise JqLexError(message, offset=self._offset + (self._index if index is None else index))

    def _skip_comment(self) -> None:
        source = self._source
        index = self._index + 1
        while index < len(source):
            if source[index] == '\\' and index + 1 < len(source) and source[index + 1] == '\n':
                index += 2
            elif source[index] == '\n':
                index += 1
                break
            else:
                index += 1
        self._index = index

    @staticmethod
    def _decode_string_part(raw: str, start: int) -> str:
        try:
            return json.loads(f'"{raw}"')
        except json.JSONDecodeError as exc:
            raise JqLexError('invalid string escape', offset=start + exc.pos) from exc
        except ValueError as exc:
            raise JqLexError('invalid string escape', offset=start) from exc

    def _skip_nested_string(self, index: int) -> int:
        source = self._source
        while index < len(source):
            char = source[index]
            if char == '"':
                return index + 1
            if char == '\\':
                if index + 1 >= len(source):
                    self._raise('unterminated string', index)
                if source[index + 1] == '(':
                    index = self._find_interpolation_end(index + 2) + 1
                else:
                    index += 2
            else:
                index += 1
        self._raise('unterminated string', index)
        raise RuntimeError('unreachable')

    def _find_interpolation_end(self, index: int) -> int:
        source = self._source
        stack = [')']
        matching = {'(': ')', '[': ']', '{': '}'}
        while index < len(source):
            char = source[index]
            if char == '"':
                index = self._skip_nested_string(index + 1)
                continue
            if char == '#':
                index += 1
                while index < len(source):
                    if source[index] == '\\' and index + 1 < len(source) and source[index + 1] == '\n':
                        index += 2
                    elif source[index] == '\n':
                        index += 1
                        break
                    else:
                        index += 1
                continue
            if char in matching:
                stack.append(matching[char])
            elif char in ')]}':
                if char != stack[-1]:
                    self._raise('mismatched delimiter in string interpolation', index)
                stack.pop()
                if not stack:
                    return index
            index += 1
        self._raise('unterminated string interpolation', index)
        raise RuntimeError('unreachable')

    def _string(self) -> Token:
        source = self._source
        start = self._index
        index = start + 1
        raw_start = index
        raw_parts: list[str] = []
        parts: list[StringTokenPart] = []

        while index < len(source):
            char = source[index]
            if char == '"':
                raw_parts.append(source[raw_start:index])
                if (raw := ''.join(raw_parts)) or not parts:
                    parts.append(self._decode_string_part(raw, self._offset + raw_start))
                self._index = index + 1
                return Token('STRING', tuple(parts), self._offset + start, self._offset + self._index)

            if char == '\\':
                if index + 1 >= len(source):
                    self._raise('unterminated string', start)
                if source[index + 1] == '(':
                    raw_parts.append(source[raw_start:index])
                    if raw := ''.join(raw_parts):
                        parts.append(self._decode_string_part(raw, self._offset + raw_start))
                    expression_start = index + 2
                    expression_end = self._find_interpolation_end(expression_start)
                    parts.append(Interpolation(
                        source[expression_start:expression_end],
                        self._offset + expression_start,
                    ))
                    index = expression_end + 1
                    raw_start = index
                    raw_parts = []
                    continue
                raw_parts.append(source[raw_start:index + 2])
                index += 2
                raw_start = index
                continue

            if ord(char) < 0x20:
                self._raise('unescaped control character in string', index)
            index += 1

        self._raise('unterminated string', start)
        raise RuntimeError('unreachable')

    def tokens(self) -> ta.Iterator[Token]:
        source = self._source
        while self._index < len(source):
            char = source[self._index]
            if char.isspace():
                self._index += 1
                continue
            if char == '#':
                self._skip_comment()
                continue
            if char == '"':
                yield self._string()
                continue

            start = self._index
            if char == '$':
                match = _IDENTIFIER.match(source, start + 1)
                if match is None:
                    self._raise('expected variable name after $', start)
                self._index = match.end()
                yield Token('VARIABLE', match.group(), self._offset + start, self._offset + self._index)
                continue

            if char.isdigit() or (char == '.' and start + 1 < len(source) and source[start + 1].isdigit()):
                match = _NUMBER.match(source, start)
                if match is None:
                    self._raise('invalid number', start)
                raw = match.group()
                self._index = match.end()
                try:
                    value = json.loads(raw)
                except (json.JSONDecodeError, ValueError) as exc:
                    raise JqLexError('invalid number', offset=self._offset + start) from exc
                if isinstance(value, float) and not math.isfinite(value):
                    self._raise('number is outside the finite jq range', start)
                yield Token('NUMBER', value, self._offset + start, self._offset + self._index)
                continue

            if char.isalpha() or char == '_':
                match = _IDENTIFIER.match(source, start)
                if match is None:
                    self._raise('invalid identifier', start)
                value = match.group()
                self._index = match.end()
                yield Token(_KEYWORDS.get(value, 'IDENT'), value, self._offset + start, self._offset + self._index)
                continue

            operator = next((candidate for candidate in _OPERATORS if source.startswith(candidate, start)), None)
            if operator is not None:
                self._index += len(operator)
                yield Token(operator, operator, self._offset + start, self._offset + self._index)
                continue

            if char in _SINGLE_TOKENS:
                self._index += 1
                yield Token(char, char, self._offset + start, self._offset + self._index)
                continue

            if char == '@':
                self._raise('format strings are not supported', start)
            self._raise(f'invalid character {char!r}', start)

        end = self._offset + len(source)
        yield Token('EOF', None, end, end)


def lex(source: str, *, offset: int = 0) -> tuple[Token, ...]:
    return tuple(Lexer(source, offset=offset).tokens())
