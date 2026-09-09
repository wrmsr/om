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


_REGEX_ALLOWED: tuple[str, ...] = tuple('([{,;:=!?&|+-*%^~<>')


def _regex_allowed(tokens: list[_Token], /) -> bool:
    if not tokens:
        return True

    previous = tokens[-1]
    if previous.kind == 'identifier':
        return previous.value in _REGEX_PREFIX_KEYWORDS

    return previous.value in _REGEX_ALLOWED


def _scan_regex(source: str, start: int, /) -> int:
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


def _scan_template(source: str, start: int, /) -> tuple[list[_Token], int]:
    tokens: list[_Token] = []
    index = start + 1

    while index < len(source):
        character = source[index]

        if character == '\\':
            index += 2
            continue

        if character == '`':
            return tokens, index + 1

        if source.startswith('${', index):
            expression, index = _scan_tokens(source, index + 2, embedded=True, stop_at_brace=True)
            tokens.extend(expression)
            continue

        index += 1

    raise ValueError('Unterminated JavaScript template literal')


def _scan_tokens(
        source: str,
        start: int = 0,
        *,
        embedded: bool = False,
        stop_at_brace: bool = False,
) -> tuple[list[_Token], int]:
    tokens: list[_Token] = []
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
            quote = character
            token_start = index + 1
            index += 1
            while index < len(source) and source[index] != quote:
                if source[index] in '\r\n':
                    raise ValueError('Unterminated JavaScript string literal')
                index += 2 if source[index] == '\\' else 1
            if index >= len(source):
                raise ValueError('Unterminated JavaScript string literal')
            tokens.append(_Token('string', source[token_start:index], token_start, index, embedded))
            index += 1
            continue

        if character == '`':
            template_tokens, index = _scan_template(source, index)
            tokens.extend(template_tokens)
            continue

        if character == '/' and _regex_allowed(tokens):
            index = _scan_regex(source, index)
            continue

        if character.isalpha() or character in '_$':
            token_start = index
            index += 1
            while index < len(source) and (source[index].isalnum() or source[index] in '_$'):
                index += 1
            tokens.append(_Token('identifier', source[token_start:index], token_start, index, embedded))
            continue

        if character == '}' and stop_at_brace and brace_depth == 0:
            return tokens, index + 1

        if character == '{':
            brace_depth += 1

        elif character == '}':
            brace_depth -= 1

        tokens.append(_Token('punctuation', character, index, index + 1, embedded))
        index += 1

    if stop_at_brace:
        raise ValueError('Unterminated JavaScript template expression')

    return tokens, index


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
    if following.value in ('.', '('):
        return None

    depth = 0
    for token_index in range(index + 1, len(tokens)):
        token = tokens[token_index]

        if token.value in ('{', '(', '['):
            depth += 1

        elif token.value in ('}', ')', ']'):
            depth -= 1

        elif depth == 0 and token.value == ';':
            break

        elif depth == 0 and token.kind == 'identifier' and token.value == 'from':
            if token_index + 1 < len(tokens) and tokens[token_index + 1].kind == 'string':
                return _module_string(tokens[token_index + 1])
            raise ValueError('Invalid JavaScript import source')

    raise ValueError('JavaScript import declaration has no source')


def _parse_export(tokens: list[_Token], index: int, /) -> ModuleSpecifier | None:
    if index + 1 >= len(tokens) or tokens[index + 1].value not in ('*', '{'):
        return None

    depth = 0
    for token_index in range(index + 1, len(tokens)):
        token = tokens[token_index]

        if token.value in ('{', '(', '['):
            depth += 1

        elif token.value in ('}', ')', ']'):
            depth -= 1

        elif depth == 0 and token.value == ';':
            return None

        elif depth == 0 and token.kind == 'identifier' and token.value == 'from':
            if token_index + 1 < len(tokens) and tokens[token_index + 1].kind == 'string':
                return _module_string(tokens[token_index + 1])
            raise ValueError('Invalid JavaScript export source')

    return None


def _is_dynamic_import(tokens: list[_Token], index: int, /) -> bool:
    if index + 1 >= len(tokens) or tokens[index + 1].value != '(':
        return False

    depth = 0
    for token_index in range(index + 1, len(tokens)):
        token = tokens[token_index]

        if token.value == '(':
            depth += 1

        elif token.value == ')':
            depth -= 1
            if depth == 0:
                return token_index + 1 >= len(tokens) or tokens[token_index + 1].value != '{'

    return True


def parse_module(source: str, /) -> ModuleParseResult:
    tokens, _ = _scan_tokens(source)
    specifiers = []
    dynamic_import = False
    braces = parentheses = brackets = 0

    for index, token in enumerate(tokens):
        previous = tokens[index - 1] if index else None
        is_keyword = previous is None or previous.value not in ('.', '?.')

        if token.kind == 'identifier' and token.value == 'import' and is_keyword:
            if _is_dynamic_import(tokens, index):
                dynamic_import = True

            elif not token.embedded and braces == parentheses == brackets == 0:
                specifier = _parse_import(tokens, index)
                if specifier is not None:
                    specifiers.append(specifier)

        elif (
                token.kind == 'identifier' and
                token.value == 'export' and
                is_keyword and
                not token.embedded and
                braces == parentheses == brackets == 0
        ):
            specifier = _parse_export(tokens, index)
            if specifier is not None:
                specifiers.append(specifier)

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
