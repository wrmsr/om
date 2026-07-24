# ruff: noqa: UP037
# @om-lite
# Copyright (c) Donald Stufft and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice, this list of conditions and the
#        following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#        following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. This file is dual licensed under the terms of the
# Apache License, Version 2.0, and the BSD License. See the LICENSE file in the root of this repository for complete
# details.
# https://github.com/pypa/packaging/blob/cf2cbe2aec28f87c6228a6fb136c27931c9af407/src/packaging/_parser.py#L65
# ruff: noqa: UP006 UP007 UP045
import ast
import contextlib
import dataclasses as dc
import re
import typing as ta

from omcore.lite.check import check
from omcore.lite.dataclasses import install_dataclass_cache_hash

from .names import canonicalize_name
from .specifiers import Specifier
from .specifiers import SpecifierSet


RequirementMarkerVar = ta.Union['RequirementVariable', 'RequirementValue']  # ta.TypeAlias

RequirementMarkerAtom = ta.Union['RequirementMarkerItem', ta.Sequence['RequirementMarkerAtom']]  # ta.TypeAlias
RequirementMarkerList = ta.Sequence[ta.Union['RequirementMarkerList', 'RequirementMarkerAtom', str]]  # ta.TypeAlias


##


@dc.dataclass()
class RequirementToken:
    name: str
    text: str
    position: int


class RequirementParserSyntaxError(Exception):
    def __init__(
        self,
        message: str,
        *,
        source: str,
        span: ta.Tuple[int, int],
    ) -> None:
        self.span = span
        self.message = message
        self.source = source

        super().__init__()

    def __str__(self) -> str:
        marker = ' ' * self.span[0] + '~' * (self.span[1] - self.span[0]) + '^'
        return '\n    '.join([self.message, self.source, marker])


REQUIRES_DEFAULT_RULES: ta.Dict[str, ta.Union[str, ta.Pattern[str]]] = {
    'LEFT_PARENTHESIS': r'\(',
    'RIGHT_PARENTHESIS': r'\)',
    'LEFT_BRACKET': r'\[',
    'RIGHT_BRACKET': r'\]',
    'SEMICOLON': r';',
    'COMMA': r',',
    'QUOTED_STRING': re.compile(
        r"""
            (
                ('[^']*')
                |
                ("[^"]*")
            )
        """,
        re.VERBOSE,
    ),
    'OP': r'(===|==|~=|!=|<=|>=|<|>)',
    'BOOLOP': r'\b(or|and)\b',
    'IN': r'\bin\b',
    'NOT': r'\bnot\b',
    'VARIABLE': re.compile(
        r"""
            \b(
                python_version
                |python_full_version
                |os[._]name
                |sys[._]platform
                |platform_(release|system)
                |platform[._](version|machine|python_implementation)
                |python_implementation
                |implementation_(name|version)
                |extra
            )\b
        """,
        re.VERBOSE,
    ),
    'SPECIFIER': re.compile(
        Specifier._operator_regex_str + Specifier._version_regex_str,  # noqa
        re.VERBOSE | re.IGNORECASE,
    ),
    'AT': r'\@',
    'URL': r'[^ \t]+',
    'IDENTIFIER': r'\b[a-zA-Z0-9][a-zA-Z0-9._-]*\b',
    'VERSION_PREFIX_TRAIL': r'\.\*',
    'VERSION_LOCAL_LABEL_TRAIL': r'\+[a-z0-9]+(?:[-_\.][a-z0-9]+)*',
    'WS': r'[ \t]+',
    'END': r'$',
}


class RequirementTokenizer:
    def __init__(
        self,
        source: str,
        *,
        rules: ta.Dict[str, ta.Union[str, ta.Pattern[str]]],
    ) -> None:
        super().__init__()

        self.source = source
        self.rules: ta.Dict[str, ta.Pattern[str]] = {name: re.compile(pattern) for name, pattern in rules.items()}
        self.next_token: ta.Optional[RequirementToken] = None
        self.position = 0

    def consume(self, name: str) -> None:
        if self.check(name):
            self.read()

    def check(self, name: str, *, peek: bool = False) -> bool:
        check.state(self.next_token is None, f'Cannot check for {name!r}, already have {self.next_token!r}')
        check.state(name in self.rules, f'Unknown token name: {name!r}')

        expression = self.rules[name]

        match = expression.match(self.source, self.position)
        if match is None:
            return False
        if not peek:
            self.next_token = RequirementToken(name, match[0], self.position)
        return True

    def expect(self, name: str, *, expected: str) -> RequirementToken:
        if not self.check(name):
            raise self.raise_syntax_error(f'Expected {expected}')
        return self.read()

    def read(self) -> RequirementToken:
        token = self.next_token
        check.state(token is not None)

        self.position += len(check.not_none(token).text)
        self.next_token = None

        return check.not_none(token)

    def raise_syntax_error(
        self,
        message: str,
        *,
        span_start: ta.Optional[int] = None,
        span_end: ta.Optional[int] = None,
    ) -> ta.NoReturn:
        span = (
            self.position if span_start is None else span_start,
            self.position if span_end is None else span_end,
        )
        raise RequirementParserSyntaxError(
            message,
            source=self.source,
            span=span,
        )

    @contextlib.contextmanager
    def enclosing_tokens(self, open_token: str, close_token: str, *, around: str) -> ta.Iterator[None]:
        if self.check(open_token):
            open_position = self.position
            self.read()
        else:
            open_position = None

        yield

        if open_position is None:
            return

        if not self.check(close_token):
            self.raise_syntax_error(
                f'Expected matching {close_token} for {open_token}, after {around}',
                span_start=open_position,
            )

        self.read()


@dc.dataclass(frozen=True)
class RequirementNode:
    value: str

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}('{self}')>"

    def serialize(self) -> str:
        raise NotImplementedError


@dc.dataclass(frozen=True)
class RequirementVariable(RequirementNode):
    def serialize(self) -> str:
        return str(self)


@dc.dataclass(frozen=True)
class RequirementValue(RequirementNode):
    def serialize(self) -> str:
        return f'"{self}"'


@dc.dataclass(frozen=True)
class RequirementOp(RequirementNode):
    def serialize(self) -> str:
        return str(self)


class RequirementMarkerItem(ta.NamedTuple):
    l: ta.Union[RequirementVariable, RequirementValue]
    op: RequirementOp
    r: ta.Union[RequirementVariable, RequirementValue]


@install_dataclass_cache_hash()
@dc.dataclass(frozen=True)
class ParsedRequirement:
    name: str
    url: str
    extras: ta.List[str]
    specifier: str
    marker: ta.Optional[RequirementMarkerList]


def parse_requirement(source: str) -> ParsedRequirement:
    return _parse_requirement(RequirementTokenizer(source, rules=REQUIRES_DEFAULT_RULES))


def _parse_requirement(tokenizer: RequirementTokenizer) -> ParsedRequirement:
    tokenizer.consume('WS')

    name_token = tokenizer.expect('IDENTIFIER', expected='package name at the start of dependency specifier')
    name = name_token.text
    tokenizer.consume('WS')

    extras = _parse_requirement_extras(tokenizer)
    tokenizer.consume('WS')

    url, specifier, marker = _parse_requirement_details(tokenizer)
    tokenizer.expect('END', expected='end of dependency specifier')

    return ParsedRequirement(name, url, extras, specifier, marker)


def _parse_requirement_details(
        tokenizer: RequirementTokenizer,
) -> ta.Tuple[str, str, ta.Optional[RequirementMarkerList]]:
    specifier = ''
    url = ''
    marker = None

    if tokenizer.check('AT'):
        tokenizer.read()
        tokenizer.consume('WS')

        url_start = tokenizer.position
        url = tokenizer.expect('URL', expected='URL after @').text
        if tokenizer.check('END', peek=True):
            return (url, specifier, marker)

        tokenizer.expect('WS', expected='whitespace after URL')

        # The input might end after whitespace.
        if tokenizer.check('END', peek=True):
            return (url, specifier, marker)

        marker = _parse_requirement_marker(
            tokenizer, span_start=url_start, after='URL and whitespace',
        )
    else:
        specifier_start = tokenizer.position
        specifier = _parse_requirement_specifier(tokenizer)
        tokenizer.consume('WS')

        if tokenizer.check('END', peek=True):
            return (url, specifier, marker)

        marker = _parse_requirement_marker(
            tokenizer,
            span_start=specifier_start,
            after=(
                'version specifier'
                if specifier
                else 'name and no valid version specifier'
            ),
        )

    return (url, specifier, marker)


def _parse_requirement_marker(
    tokenizer: RequirementTokenizer, *, span_start: int, after: str,
) -> RequirementMarkerList:
    if not tokenizer.check('SEMICOLON'):
        tokenizer.raise_syntax_error(
            f'Expected end or semicolon (after {after})',
            span_start=span_start,
        )
    tokenizer.read()

    marker = _parse_requirement_marker_(tokenizer)
    tokenizer.consume('WS')

    return marker


def _parse_requirement_extras(tokenizer: RequirementTokenizer) -> ta.List[str]:
    if not tokenizer.check('LEFT_BRACKET', peek=True):
        return []

    with tokenizer.enclosing_tokens(
        'LEFT_BRACKET',
        'RIGHT_BRACKET',
        around='extras',
    ):
        tokenizer.consume('WS')
        extras = _parse_requirement_extras_list(tokenizer)
        tokenizer.consume('WS')

    return extras


def _parse_requirement_extras_list(tokenizer: RequirementTokenizer) -> ta.List[str]:
    extras: ta.List[str] = []

    if not tokenizer.check('IDENTIFIER'):
        return extras

    extras.append(tokenizer.read().text)

    while True:
        tokenizer.consume('WS')
        if tokenizer.check('IDENTIFIER', peek=True):
            tokenizer.raise_syntax_error('Expected comma between extra names')
        elif not tokenizer.check('COMMA'):
            break

        tokenizer.read()
        tokenizer.consume('WS')

        extra_token = tokenizer.expect('IDENTIFIER', expected='extra name after comma')
        extras.append(extra_token.text)

    return extras


def _parse_requirement_specifier(tokenizer: RequirementTokenizer) -> str:
    with tokenizer.enclosing_tokens(
        'LEFT_PARENTHESIS',
        'RIGHT_PARENTHESIS',
        around='version specifier',
    ):
        tokenizer.consume('WS')
        parsed_specifiers = _parse_requirement_version_many(tokenizer)
        tokenizer.consume('WS')

    return parsed_specifiers


def _parse_requirement_version_many(tokenizer: RequirementTokenizer) -> str:
    parsed_specifiers = ''
    while tokenizer.check('SPECIFIER'):
        span_start = tokenizer.position
        parsed_specifiers += tokenizer.read().text
        if tokenizer.check('VERSION_PREFIX_TRAIL', peek=True):
            tokenizer.raise_syntax_error(
                '.* suffix can only be used with `==` or `!=` operators',
                span_start=span_start,
                span_end=tokenizer.position + 1,
            )
        if tokenizer.check('VERSION_LOCAL_LABEL_TRAIL', peek=True):
            tokenizer.raise_syntax_error(
                'Local version label can only be used with `==` or `!=` operators',
                span_start=span_start,
                span_end=tokenizer.position,
            )
        tokenizer.consume('WS')
        if not tokenizer.check('COMMA'):
            break
        parsed_specifiers += tokenizer.read().text
        tokenizer.consume('WS')

    return parsed_specifiers


def parse_requirement_marker(source: str) -> RequirementMarkerList:
    return _parse_requirement_full_marker(RequirementTokenizer(source, rules=REQUIRES_DEFAULT_RULES))


def _parse_requirement_full_marker(tokenizer: RequirementTokenizer) -> RequirementMarkerList:
    retval = _parse_requirement_marker_(tokenizer)
    tokenizer.expect('END', expected='end of marker expression')
    return retval


def _parse_requirement_marker_(tokenizer: RequirementTokenizer) -> RequirementMarkerList:
    expression = [_parse_requirement_marker_atom(tokenizer)]
    while tokenizer.check('BOOLOP'):
        token = tokenizer.read()
        expr_right = _parse_requirement_marker_atom(tokenizer)
        expression.extend((token.text, expr_right))
    return expression


def _parse_requirement_marker_atom(tokenizer: RequirementTokenizer) -> RequirementMarkerAtom:
    tokenizer.consume('WS')
    if tokenizer.check('LEFT_PARENTHESIS', peek=True):
        with tokenizer.enclosing_tokens(
            'LEFT_PARENTHESIS',
            'RIGHT_PARENTHESIS',
            around='marker expression',
        ):
            tokenizer.consume('WS')
            marker: RequirementMarkerAtom = _parse_requirement_marker_(tokenizer)
            tokenizer.consume('WS')
    else:
        marker = _parse_requirement_marker_item(tokenizer)
    tokenizer.consume('WS')
    return marker


def _parse_requirement_marker_item(tokenizer: RequirementTokenizer) -> RequirementMarkerItem:
    tokenizer.consume('WS')
    marker_var_left = _parse_requirement_marker_var(tokenizer)
    tokenizer.consume('WS')
    marker_op = _parse_requirement_marker_op(tokenizer)
    tokenizer.consume('WS')
    marker_var_right = _parse_requirement_marker_var(tokenizer)
    tokenizer.consume('WS')
    return RequirementMarkerItem(marker_var_left, marker_op, marker_var_right)


def _parse_requirement_marker_var(tokenizer: RequirementTokenizer) -> RequirementMarkerVar:
    if tokenizer.check('VARIABLE'):
        return process_requirement_env_var(tokenizer.read().text.replace('.', '_'))
    elif tokenizer.check('QUOTED_STRING'):
        return process_requirement_python_str(tokenizer.read().text)
    else:
        tokenizer.raise_syntax_error(message='Expected a marker variable or quoted string')
        raise RuntimeError  # noqa


def process_requirement_env_var(env_var: str) -> RequirementVariable:
    if env_var in ('platform_python_implementation', 'python_implementation'):
        return RequirementVariable('platform_python_implementation')
    else:
        return RequirementVariable(env_var)


def process_requirement_python_str(python_str: str) -> RequirementValue:
    value = ast.literal_eval(python_str)
    return RequirementValue(str(value))


def _parse_requirement_marker_op(tokenizer: RequirementTokenizer) -> RequirementOp:
    if tokenizer.check('IN'):
        tokenizer.read()
        return RequirementOp('in')
    elif tokenizer.check('NOT'):
        tokenizer.read()
        tokenizer.expect('WS', expected="whitespace after 'not'")
        tokenizer.expect('IN', expected="'in' after 'not'")
        return RequirementOp('not in')
    elif tokenizer.check('OP'):
        return RequirementOp(tokenizer.read().text)
    else:
        return tokenizer.raise_syntax_error(
            'Expected marker operator, one of '
            '<=, <, !=, ==, >=, >, ~=, ===, in, not in',
        )


##


def _normalize_requirement_marker_extras(
        result: ta.Union[RequirementMarkerList, RequirementMarkerAtom, str],
) -> ta.Union[RequirementMarkerList, RequirementMarkerAtom, str]:
    if not isinstance(result, tuple):
        return result

    lhs, op, rhs = result
    if isinstance(lhs, RequirementVariable) and lhs.value == 'extra':
        normalized_extra = canonicalize_name(rhs.value)
        rhs = RequirementValue(normalized_extra)
    elif isinstance(rhs, RequirementVariable) and rhs.value == 'extra':
        normalized_extra = canonicalize_name(lhs.value)
        lhs = RequirementValue(normalized_extra)
    return lhs, op, rhs


def _normalize_requirement_marker_extra_values(results: RequirementMarkerList) -> RequirementMarkerList:
    return [_normalize_requirement_marker_extras(r) for r in results]


def _format_requirement_marker(
        marker: ta.Union[ta.List[str], RequirementMarkerAtom, str],
        first: ta.Optional[bool] = True,
) -> str:
    check.isinstance(marker, (list, tuple, str))

    if (
            isinstance(marker, list) and
            len(marker) == 1 and
            isinstance(marker[0], (list, tuple))
    ):
        return _format_requirement_marker(marker[0])

    if isinstance(marker, list):
        inner = (_format_requirement_marker(m, first=False) for m in marker)
        if first:
            return ' '.join(inner)
        else:
            return '(' + ' '.join(inner) + ')'
    elif isinstance(marker, tuple):
        return ' '.join([m.serialize() for m in marker])
    else:
        return marker  # type: ignore[return-value]


class InvalidRequirementMarkerError(ValueError):
    """An invalid requirement was found, users should refer to PEP 508."""


class RequirementMarker:
    def __init__(self, marker: str) -> None:
        self._markers: RequirementMarkerList = []

        try:
            self._markers = _normalize_requirement_marker_extra_values(parse_requirement_marker(marker))
        except RequirementParserSyntaxError as e:
            raise InvalidRequirementMarkerError(str(e)) from e

    @classmethod
    def _from_markers(cls, markers: RequirementMarkerList) -> 'RequirementMarker':
        new = cls.__new__(cls)
        new._markers = markers  # noqa
        return new

    def __str__(self) -> str:
        return _format_requirement_marker(self._markers)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}({str(self)!r})>'

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RequirementMarker):
            return NotImplemented

        return str(self) == str(other)

    def __getstate__(self) -> str:
        return str(self)

    def __setstate__(self, state: object) -> None:
        s = check.isinstance(state, str)
        try:
            self._markers = _normalize_requirement_marker_extra_values(parse_requirement_marker(s))
        except RequirementParserSyntaxError as exc:
            raise TypeError(f'Cannot restore Marker from {state!r}') from exc

    def __and__(self, other: 'RequirementMarker') -> 'RequirementMarker':
        if not isinstance(other, RequirementMarker):
            return NotImplemented
        return self._from_markers([self._markers, 'and', other._markers])

    def __or__(self, other: 'RequirementMarker') -> 'RequirementMarker':
        if not isinstance(other, RequirementMarker):
            return NotImplemented
        return self._from_markers([self._markers, 'or', other._markers])

    # def evaluate(
    #         self,
    #         environment: ta.Optional[ta.Mapping[str, ta.Union[str, ta.AbstractSet[str]]]] = None,
    #         context: EvaluateContext = "metadata",
    # ) -> bool:
    #     current_environment = ta.cast(
    #         "ta.Dict[str, ta.Optional[ta.AbstractSet[str]]]", default_environment()
    #     )
    #     if context == "lock_file":
    #         current_environment.update(
    #             extras=frozenset(), dependency_groups=frozenset()
    #         )
    #     elif context == "metadata":
    #         current_environment["extra"] = ""
    #
    #     if environment is not None:
    #         current_environment.update(environment)
    #         if "extra" in current_environment:
    #             # The API used to allow setting extra to None. We need to handle this case for backwards
    #             # compatibility. Also skip running normalize name if extra is empty.
    #             extra = ta.cast("ta.Optional[str]", current_environment["extra"])
    #             current_environment["extra"] = canonicalize_name(extra) if extra else ""
    #
    #     return _evaluate_markers(self._markers, _repair_python_full_version(current_environment))


class InvalidRequirementError(ValueError):
    """An invalid requirement was found, users should refer to PEP 508."""


class Requirement:
    def __init__(self, requirement_string: str) -> None:
        try:
            parsed = parse_requirement(requirement_string)
        except RequirementParserSyntaxError as e:
            raise InvalidRequirementError(str(e)) from e

        self.name: str = parsed.name
        self.url: ta.Optional[str] = parsed.url or None
        self.extras: ta.Set[str] = set(parsed.extras or [])
        self.specifier: SpecifierSet = SpecifierSet(parsed.specifier)
        self.marker: ta.Optional[RequirementMarker] = None
        if parsed.marker is not None:
            self.marker = RequirementMarker.__new__(RequirementMarker)
            self.marker._markers = _normalize_requirement_marker_extra_values(parsed.marker)  # noqa

    def _iter_parts(self, name: str) -> ta.Iterator[str]:
        yield name

        if self.extras:
            formatted_extras = ','.join(sorted(self.extras))
            yield f'[{formatted_extras}]'

        if self.specifier:
            yield str(self.specifier)

        if self.url:
            yield f' @ {self.url}'
            if self.marker:
                yield ' '

        if self.marker:
            yield f'; {self.marker}'

    def __getstate__(self) -> str:
        return str(self)

    def __setstate__(self, state: object) -> None:
        try:
            tmp = Requirement(check.isinstance(state, str))
        except InvalidRequirementError as exc:
            raise TypeError(f'Cannot restore Requirement from {state!r}') from exc
        self.name = tmp.name
        self.url = tmp.url
        self.extras = tmp.extras
        self.specifier = tmp.specifier
        self.marker = tmp.marker

    def __str__(self) -> str:
        return ''.join(self._iter_parts(self.name))

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}({str(self)!r})>'

    def __hash__(self) -> int:
        return hash(tuple(self._iter_parts(canonicalize_name(self.name))))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Requirement):
            return NotImplemented

        return (
            canonicalize_name(self.name) == canonicalize_name(other.name) and
            self.extras == other.extras and
            self.specifier == other.specifier and
            self.url == other.url and
            self.marker == other.marker
        )
