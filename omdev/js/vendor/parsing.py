from omcore import dataclasses as dc

from .models import ModuleParseResult
from .models import ModuleSpecifier


##


@dc.dataclass(frozen=True)
class _Token:
    kind: str
    value: str
    start: int
    end: int
    embedded: bool

    # Only meaningful on `)` and `}`: whether a following `/` begins a regular expression. It is decided when the
    # matching opener was scanned, since by the closer the context which disambiguates it is long gone.
    regex_after: bool = False


# Keywords after which a `/` begins a regular expression rather than division.
_REGEX_PREFIX_KEYWORDS = frozenset({
    'await',
    'case',
    'delete',
    'do',
    'else',
    'in',
    'instanceof',
    'new',
    'of',
    'return',
    'throw',
    'typeof',
    'void',
    'yield',
})

# Keywords which begin an expression context but are nonetheless followed by a statement block, not an object literal.
_BLOCK_PREFIX_KEYWORDS = frozenset({
    'do',
    'else',
})

# Keywords whose parenthesized head is followed by a statement, so a `/` after the closing parenthesis begins a regular
# expression rather than dividing the parenthesized value.
_STATEMENT_HEAD_KEYWORDS = frozenset({
    'for',
    'if',
    'while',
    'with',
})

_MULTI_CHARACTER_PUNCTUATION: tuple[str, ...] = (
    '++',
    '--',
    '=>',
)

_REGEX_PREFIX_PUNCTUATION = frozenset({*'([{,;:=!?&|+-*%^~<>', '=>'})

_BLOCK_PREFIX_PUNCTUATION = frozenset({')', '}', ';', '{', '=>'})


class _Scanner:
    def __init__(self, source: str) -> None:
        super().__init__()

        self._source = source
        self._tokens: list[_Token] = []

        # Stacks of `regex_after` values for the currently open parentheses and braces.
        self._parentheses: list[bool] = []
        self._braces: list[bool] = []

    def _previous(self, scope_start: int, /) -> _Token | None:
        return self._tokens[-1] if len(self._tokens) > scope_start else None

    def _regex_allowed(self, scope_start: int, /) -> bool:
        previous = self._previous(scope_start)
        if previous is None:
            return True

        if previous.kind == 'identifier':
            return previous.value in _REGEX_PREFIX_KEYWORDS

        if previous.kind != 'punctuation':
            return False

        if previous.value in (')', '}'):
            return previous.regex_after

        return previous.value in _REGEX_PREFIX_PUNCTUATION

    def _block_follows(self, scope_start: int, /) -> bool:
        previous = self._previous(scope_start)
        if previous is None:
            return True

        if previous.kind == 'identifier':
            return previous.value in _BLOCK_PREFIX_KEYWORDS or previous.value not in _REGEX_PREFIX_KEYWORDS

        return previous.kind == 'punctuation' and previous.value in _BLOCK_PREFIX_PUNCTUATION

    def _statement_head_follows(self, scope_start: int, /) -> bool:
        previous = self._previous(scope_start)
        return previous is not None and previous.kind == 'identifier' and previous.value in _STATEMENT_HEAD_KEYWORDS

    def _scan_regex(self, start: int, /) -> int:
        source = self._source
        index = start + 1
        in_class = False

        while index < len(source):
            character = source[index]
            if character in '\r\n':
                raise ValueError(f'Unterminated JavaScript regular expression at offset {start}')

            if character == '\\':
                index += 2
                continue

            if character == '[':
                in_class = True

            elif character == ']':
                in_class = False

            elif character == '/' and not in_class:
                index += 1
                while index < len(source) and (source[index].isalnum() or source[index] in '_$'):
                    index += 1
                return index

            index += 1

        raise ValueError(f'Unterminated JavaScript regular expression at offset {start}')

    def _scan_string(self, start: int, /, *, embedded: bool) -> int:
        source = self._source
        quote = source[start]
        index = start + 1

        while index < len(source) and source[index] != quote:
            if source[index] in '\r\n':
                raise ValueError('Unterminated JavaScript string literal')
            index += 2 if source[index] == '\\' else 1

        if index >= len(source):
            raise ValueError('Unterminated JavaScript string literal')

        self._tokens.append(_Token('string', source[start + 1:index], start + 1, index, embedded))
        return index + 1

    def _scan_template(self, start: int, /, *, embedded: bool) -> int:
        source = self._source
        index = start + 1

        while index < len(source):
            character = source[index]

            if character == '\\':
                index += 2
                continue

            if character == '`':
                self._tokens.append(_Token('template', '', start, index + 1, embedded))
                return index + 1

            if source.startswith('${', index):
                index = self._scan(index + 2, embedded=True, stop_at_brace=True)
                continue

            index += 1

        raise ValueError('Unterminated JavaScript template literal')

    def _scan(
            self,
            start: int,
            /,
            *,
            embedded: bool,
            stop_at_brace: bool,
    ) -> int:
        source = self._source
        tokens = self._tokens
        scope_start = len(tokens)
        index = start
        brace_depth = 0

        while index < len(source):
            character = source[index]

            if character.isspace():
                index += 1
                continue

            if source.startswith('//', index):
                newline = source.find('\n', index + 2)
                index = len(source) if newline < 0 else newline + 1
                continue

            if source.startswith('/*', index):
                end = source.find('*/', index + 2)
                if end < 0:
                    raise ValueError('Unterminated JavaScript block comment')
                index = end + 2
                continue

            if character in "'\"":
                index = self._scan_string(index, embedded=embedded)
                continue

            if character == '`':
                index = self._scan_template(index, embedded=embedded)
                continue

            if character == '/' and self._regex_allowed(scope_start):
                end = self._scan_regex(index)
                tokens.append(_Token('regex', source[index:end], index, end, embedded))
                index = end
                continue

            if character.isalpha() or character in '_$':
                token_start = index
                index += 1
                while index < len(source) and (source[index].isalnum() or source[index] in '_$'):
                    index += 1
                tokens.append(_Token('identifier', source[token_start:index], token_start, index, embedded))
                continue

            if character == '}' and stop_at_brace and brace_depth == 0:
                return index + 1

            value = character
            for punctuation in _MULTI_CHARACTER_PUNCTUATION:
                if source.startswith(punctuation, index):
                    value = punctuation
                    break

            regex_after = False
            if value == '(':
                self._parentheses.append(self._statement_head_follows(scope_start))

            elif value == ')':
                regex_after = self._parentheses.pop() if self._parentheses else False

            elif value == '{':
                brace_depth += 1
                self._braces.append(self._block_follows(scope_start))

            elif value == '}':
                brace_depth -= 1
                regex_after = self._braces.pop() if self._braces else True

            tokens.append(_Token('punctuation', value, index, index + len(value), embedded, regex_after))
            index += len(value)

        if stop_at_brace:
            raise ValueError('Unterminated JavaScript template expression')

        return index

    def scan(self) -> list[_Token]:
        start = 0
        if self._source.startswith('#!'):
            newline = self._source.find('\n')
            start = len(self._source) if newline < 0 else newline + 1

        self._scan(start, embedded=False, stop_at_brace=False)
        return self._tokens


def _is_punctuation(token: _Token, value: str, /) -> bool:
    return token.kind == 'punctuation' and token.value == value


def _is_identifier(token: _Token, value: str, /) -> bool:
    return token.kind == 'identifier' and token.value == value


def _module_string(token: _Token, /) -> ModuleSpecifier:
    if '\\' in token.value:
        raise ValueError('Escaped JavaScript module specifiers are not supported')
    return ModuleSpecifier(value=token.value, start=token.start, end=token.end)


def _parse_import(tokens: list[_Token], index: int, /) -> ModuleSpecifier | None:
    if index + 1 >= len(tokens):
        raise ValueError('Incomplete JavaScript import declaration')
    following = tokens[index + 1]
    if following.kind == 'string':
        return _module_string(following)
    if following.kind == 'punctuation' and following.value in ('.', '('):
        return None

    depth = 0
    for token_index in range(index + 1, len(tokens)):
        token = tokens[token_index]

        if token.kind == 'punctuation' and token.value in ('{', '(', '['):
            depth += 1

        elif token.kind == 'punctuation' and token.value in ('}', ')', ']'):
            depth -= 1

        elif depth == 0 and _is_punctuation(token, ';'):
            break

        elif depth == 0 and _is_identifier(token, 'from'):
            if token_index + 1 < len(tokens) and tokens[token_index + 1].kind == 'string':
                return _module_string(tokens[token_index + 1])
            raise ValueError('Invalid JavaScript import source')

    raise ValueError('JavaScript import declaration has no source')


def _export_clause_end(tokens: list[_Token], index: int, /) -> int | None:
    """Returns the index of the token following the balanced export clause at `index`, or None if it is not one."""

    following = tokens[index + 1]

    if _is_punctuation(following, '{'):
        depth = 0
        for token_index in range(index + 1, len(tokens)):
            token = tokens[token_index]
            if _is_punctuation(token, '{'):
                depth += 1
            elif _is_punctuation(token, '}'):
                depth -= 1
                if depth == 0:
                    return token_index + 1
        raise ValueError('Unterminated JavaScript export list')

    if _is_punctuation(following, '*'):
        end = index + 2
        if end < len(tokens) and _is_identifier(tokens[end], 'as'):
            end += 2
        if end >= len(tokens) or not _is_identifier(tokens[end], 'from'):
            raise ValueError('Invalid JavaScript export source')
        return end

    return None


def _parse_export(tokens: list[_Token], index: int, /) -> ModuleSpecifier | None:
    if index + 1 >= len(tokens):
        return None

    end = _export_clause_end(tokens, index)
    if end is None:
        return None

    # A source clause can only be the token immediately after the balanced clause. Scanning any further would, in
    # semicolon-free code, adopt the `from` of a later statement as this declaration's source.
    if end < len(tokens) and _is_identifier(tokens[end], 'from'):
        if end + 1 < len(tokens) and tokens[end + 1].kind == 'string':
            return _module_string(tokens[end + 1])
        raise ValueError('Invalid JavaScript export source')

    return None


def _is_dynamic_import(tokens: list[_Token], index: int, /) -> bool:
    if index + 1 >= len(tokens) or not _is_punctuation(tokens[index + 1], '('):
        return False

    depth = 0
    for token_index in range(index + 1, len(tokens)):
        token = tokens[token_index]

        if _is_punctuation(token, '('):
            depth += 1

        elif _is_punctuation(token, ')'):
            depth -= 1
            if depth == 0:
                return token_index + 1 >= len(tokens) or not _is_punctuation(tokens[token_index + 1], '{')

    return True


def parse_module(source: str, /) -> ModuleParseResult:
    tokens = _Scanner(source).scan()
    specifiers = []
    dynamic_import = False
    braces = parentheses = brackets = 0

    for index, token in enumerate(tokens):
        previous = tokens[index - 1] if index else None
        is_keyword = previous is None or not _is_punctuation(previous, '.')

        if _is_identifier(token, 'import') and is_keyword:
            if _is_dynamic_import(tokens, index):
                dynamic_import = True

            elif not token.embedded and braces == parentheses == brackets == 0:
                specifier = _parse_import(tokens, index)
                if specifier is not None:
                    specifiers.append(specifier)

        elif (
                _is_identifier(token, 'export') and
                is_keyword and
                not token.embedded and
                braces == parentheses == brackets == 0
        ):
            specifier = _parse_export(tokens, index)
            if specifier is not None:
                specifiers.append(specifier)

        if token.kind != 'punctuation':
            continue

        if token.value == '{':
            braces += 1

        elif token.value == '}':
            braces -= 1

        elif token.value == '(':
            parentheses += 1

        elif token.value == ')':
            parentheses -= 1

        elif token.value == '[':
            brackets += 1

        elif token.value == ']':
            brackets -= 1

    return ModuleParseResult(specifiers=tuple(specifiers), dynamic_import=dynamic_import)
