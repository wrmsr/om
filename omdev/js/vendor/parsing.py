from ..lexing import JsScanner
from ..lexing import JsToken
from .models import ModuleParseResult
from .models import ModuleSpecifier


##


def _is_punctuation(token: JsToken, value: str, /) -> bool:
    return token.kind == 'punctuation' and token.value == value


def _is_identifier(token: JsToken, value: str, /) -> bool:
    return token.kind == 'identifier' and token.value == value


def _module_string(token: JsToken, /) -> ModuleSpecifier:
    if '\\' in token.value:
        raise ValueError('Escaped JavaScript module specifiers are not supported')
    return ModuleSpecifier(value=token.value[1:-1], start=token.start + 1, end=token.end - 1)


def _parse_import(tokens: list[JsToken], index: int, /) -> ModuleSpecifier | None:
    if index + 1 >= len(tokens):
        raise ValueError('Incomplete JavaScript import declaration')
    following = tokens[index + 1]
    if following.kind == 'string':
        return _module_string(following)
    if following.kind == 'punctuation' and following.value in ('.', '('):
        return None

    # A default binding may itself be named `from`; it is not the source-clause marker.
    clause_start = index + 2 if following.kind == 'identifier' else index + 1
    depth = 0
    for token_index in range(clause_start, len(tokens)):
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


def _export_clause_end(tokens: list[JsToken], index: int, /) -> int | None:
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


def _parse_export(tokens: list[JsToken], index: int, /) -> ModuleSpecifier | None:
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


def _is_dynamic_import(tokens: list[JsToken], index: int, /) -> bool:
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
    # Keep template boundaries so lookahead never joins separate interpolations.
    tokens = [token for token in JsScanner(source).scan() if token.kind not in ('whitespace', 'comment')]
    specifiers = []
    dynamic_import = False
    braces = parentheses = brackets = 0

    for index, token in enumerate(tokens):
        previous = tokens[index - 1] if index else None
        is_keyword = previous is None or not (
            previous.kind == 'punctuation' and previous.value in ('.', '?.', '#')
        )

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
