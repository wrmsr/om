"""
A small, lossless JavaScript lexer for highlighting and token-level scraping.

This is not a validating parser. In particular, slash disambiguation uses statement/expression context heuristics,
not a full grammar. Token kinds and the punctuation/context tables are deliberately separate so new lexical forms
can be added without changing consumers. Keywords remain identifiers; their interpretation belongs to the caller.
"""
import bisect
import re

from omcore import dataclasses as dc


##


@dc.dataclass(frozen=True)
class JsPosition:
    """A code-point offset, UTF-8 byte offset, one-based line and zero-based code-point column (tabs unexpanded)."""

    offset: int
    byte_offset: int
    line: int
    column: int


class JsSourceMap:
    """Optional location index, independent of scanning. CRLF is one newline; CR, LF, LS and PS also end lines."""

    def __init__(self, source: str) -> None:
        super().__init__()

        self._line_starts = [0, *(m.end() for m in re.finditer(r'\r\n|[\r\n\u2028\u2029]', source))]
        self._byte_offsets = [0]
        for character in source:
            # surrogatepass also permits highlighting editor buffers containing lone surrogates.
            self._byte_offsets.append(self._byte_offsets[-1] + len(character.encode('utf-8', 'surrogatepass')))

    def position(self, offset: int) -> JsPosition:
        if not 0 <= offset < len(self._byte_offsets):
            raise ValueError(offset)
        row = bisect.bisect_right(self._line_starts, offset) - 1
        return JsPosition(offset, self._byte_offsets[offset], row + 1, offset - self._line_starts[row])


@dc.dataclass(frozen=True)
class JsToken:
    """
    An exact source slice with half-open code-point offsets; use JsSourceMap for byte/line/column locations.

    The ordered stream partitions the entire source, including trivia. Strings include their quotes; template chunks
    include backticks but exclude interpolation boundaries (`${` and `}`). Expression tokens inside interpolations
    have `embedded=True`, including nested templates. No string escape sequences are decoded.
    """

    kind: str
    value: str
    start: int
    end: int
    embedded: bool

    # On `)` and `}`, records whether the matching opener introduced a statement rather than an expression.
    regex_after: bool = False


class JsLexError(ValueError):
    def __init__(self, message: str, offset: int) -> None:
        super().__init__(f'{message} at offset {offset}')

        self.offset = offset


##


_LINE_TERMINATORS = '\r\n\u2028\u2029'
_TRIVIA_KINDS = frozenset({'whitespace', 'comment', 'template_boundary'})

_REGEX_PREFIX_KEYWORDS = frozenset({
    'await', 'case', 'delete', 'do', 'else', 'in', 'instanceof', 'new', 'of', 'return', 'throw', 'typeof', 'void',
    'yield',
})
_BLOCK_PREFIX_KEYWORDS = frozenset({'do', 'else', 'try', 'finally'})
_STATEMENT_HEAD_KEYWORDS = frozenset({'for', 'if', 'while', 'with', 'switch', 'catch'})

# Longest match wins. Single-character punctuators are handled separately.
_MULTI_CHARACTER_PUNCTUATION = tuple(sorted({
    '>>>=', '===', '!==', '**=', '<<=', '>>=', '>>>', '&&=', '||=', '??=', '...',
    '=>', '==', '!=', '<=', '>=', '++', '--', '<<', '>>', '**', '&&', '||', '??', '?.',
    '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=',
}, key=lambda s: (-len(s), s)))
_SINGLE_CHARACTER_PUNCTUATION = frozenset('{}()[].;,<>+-*%&|^!~?:=/')
_REGEX_PREFIX_PUNCTUATION = frozenset({
    *'([{,;:=!?&|+-*%^~<>', '=>', '==', '===', '!=', '!==', '<=', '>=', '**', '&&', '||', '??',
    '<<', '>>', '>>>', '+=', '-=', '*=', '/=', '%=', '**=', '&=', '|=', '^=', '<<=', '>>=', '>>>=',
    '&&=', '||=', '??=', '...',
})
_BLOCK_PREFIX_PUNCTUATION = frozenset({')', '}', ';', '{', '=>'})

# Lexical recognition, not numeric validation (e.g. legacy octal is accepted as decimal digits).
_DIGITS = r'[0-9](?:_?[0-9])*'
_NUMBER = re.compile(
    r'(?:0[xX][0-9a-fA-F](?:_?[0-9a-fA-F])*n?'
    r'|0[bB][01](?:_?[01])*n?'
    r'|0[oO][0-7](?:_?[0-7])*n?'
    rf'|{_DIGITS}n'
    rf'|(?:{_DIGITS}(?:\.(?:{_DIGITS})?)?|\.{_DIGITS})(?:[eE][+-]?{_DIGITS})?)',
)
_IDENTIFIER_ESCAPE = re.compile(r'\\u(?:[0-9a-fA-F]{4}|\{[0-9a-fA-F]+\})')


def _identifier_start(character: str) -> bool:
    return character in '_$' or character.isidentifier()


def _identifier_continue(character: str) -> bool:
    return character in '$\u200c\u200d' or ('a' + character).isidentifier()


class JsScanner:
    """
    Scan a whole source string. Each scan starts fresh and returns a caller-owned token list.

    Strict mode reports unterminated literals/comments and unrecognized characters as JsLexError. Tolerant mode keeps
    unfinished literals in their normal kind and emits unknown characters as `error` tokens, for editor input. Neither
    mode validates balanced delimiters or JavaScript syntax. Deeply recursive templates can raise RecursionError.
    """

    def __init__(self, source: str, *, tolerant: bool = False) -> None:
        super().__init__()

        self._source = source
        self._tolerant = tolerant
        self._tokens: list[JsToken] = []
        self._parentheses: list[bool] = []
        self._braces: list[bool] = []

    def _emit(
            self,
            kind: str,
            start: int,
            end: int,
            *,
            embedded: bool,
            regex_after: bool = False,
    ) -> None:
        if end > start:
            self._tokens.append(JsToken(
                kind=kind,
                value=self._source[start:end],
                start=start,
                end=end,
                embedded=embedded,
                regex_after=regex_after,
            ))

    def _unfinished(self, message: str, start: int) -> None:
        if not self._tolerant:
            raise JsLexError(message, start)

    def _previous(self, scope_start: int, /, *, skip: int = 0) -> JsToken | None:
        for index in range(len(self._tokens) - 1, scope_start - 1, -1):
            if (token := self._tokens[index]).kind not in _TRIVIA_KINDS:
                if skip:
                    skip -= 1
                else:
                    return token
        return None

    def _previous_is_keyword(self, scope_start: int, /) -> bool:
        previous = self._previous(scope_start)
        before = self._previous(scope_start, skip=1)
        return (
            previous is not None and previous.kind == 'identifier' and
            not (before is not None and before.kind == 'punctuation' and before.value in ('.', '?.', '#'))
        )

    def _regex_allowed(self, scope_start: int, /) -> bool:
        previous = self._previous(scope_start)
        if previous is None:
            return True
        if previous.kind == 'identifier':
            return self._previous_is_keyword(scope_start) and previous.value in _REGEX_PREFIX_KEYWORDS
        if previous.kind != 'punctuation':
            return False
        if previous.value in (')', '}'):
            return previous.regex_after
        return previous.value in _REGEX_PREFIX_PUNCTUATION

    def _block_follows(self, scope_start: int, /, *, expression: bool) -> bool:
        previous = self._previous(scope_start)
        if previous is None:
            return not expression
        if previous.kind == 'identifier':
            return previous.value in _BLOCK_PREFIX_KEYWORDS or previous.value not in _REGEX_PREFIX_KEYWORDS
        return previous.kind == 'punctuation' and previous.value in _BLOCK_PREFIX_PUNCTUATION

    def _statement_head_follows(self, scope_start: int, /) -> bool:
        previous = self._previous(scope_start)
        return (
            self._previous_is_keyword(scope_start) and
            previous is not None and previous.value in _STATEMENT_HEAD_KEYWORDS
        )

    def _scan_regex(self, start: int, /) -> int:
        source = self._source
        index = start + 1
        in_class = False
        while index < len(source):
            character = source[index]
            if character in _LINE_TERMINATORS:
                break
            if character == '\\':
                if index + 1 < len(source) and source[index + 1] in _LINE_TERMINATORS:
                    break
                index = min(index + 2, len(source))
                continue
            if character == '[':
                in_class = True
            elif character == ']':
                in_class = False
            elif character == '/' and not in_class:
                index += 1
                while index < len(source) and _identifier_continue(source[index]):
                    index += 1
                return index
            index += 1
        self._unfinished('Unterminated JavaScript regular expression', start)
        return index

    def _scan_string(self, start: int, /) -> int:
        source = self._source
        quote = source[start]
        index = start + 1
        while index < len(source):
            if source[index] == quote:
                return index + 1
            if source[index] in '\r\n':
                break
            if source[index] == '\\':
                index += 1
                if source.startswith('\r\n', index):
                    index += 2
                else:
                    index = min(index + 1, len(source))
            else:
                index += 1
        self._unfinished('Unterminated JavaScript string literal', start)
        return index

    def _scan_template(self, start: int, /, *, embedded: bool) -> int:
        source = self._source
        segment = start
        index = start + 1
        while index < len(source):
            if source[index] == '\\':
                index = min(index + 2, len(source))
                continue
            if source[index] == '`':
                self._emit('template', segment, index + 1, embedded=embedded)
                return index + 1
            if source.startswith('${', index):
                self._emit('template', segment, index, embedded=embedded)
                self._emit('template_boundary', index, index + 2, embedded=embedded)
                index = self._scan(index + 2, embedded=True, stop_at_brace=True)
                segment = index
                continue
            index += 1
        self._emit('template', segment, index, embedded=embedded)
        self._unfinished('Unterminated JavaScript template literal', start)
        return index

    def _scan_identifier(self, start: int) -> int:
        index = start
        while index < len(self._source):
            if self._source[index] == '\\':
                match = _IDENTIFIER_ESCAPE.match(self._source, index)
                if match is None:
                    break
                index = match.end()
            elif (_identifier_start if index == start else _identifier_continue)(self._source[index]):
                index += 1
            else:
                break
        return index

    def _scan(
            self,
            start: int,
            /,
            *,
            embedded: bool,
            stop_at_brace: bool,
    ) -> int:
        source = self._source
        scope_start = len(self._tokens)
        index = start
        brace_depth = 0
        while index < len(source):
            token_start = index
            character = source[index]
            kind: str
            if character.isspace() or character == '\ufeff':
                index += 1
                while index < len(source) and (source[index].isspace() or source[index] == '\ufeff'):
                    index += 1
                kind = 'whitespace'
            elif source.startswith('//', index) or (index == 0 and source.startswith('#!')):
                index += 2
                while index < len(source) and source[index] not in _LINE_TERMINATORS:
                    index += 1
                kind = 'comment'
            elif source.startswith('/*', index):
                end = source.find('*/', index + 2)
                if end < 0:
                    self._unfinished('Unterminated JavaScript block comment', index)
                    index = len(source)
                else:
                    index = end + 2
                kind = 'comment'
            elif character in "'\"":
                index = self._scan_string(index)
                kind = 'string'
            elif character == '`':
                index = self._scan_template(index, embedded=embedded)
                continue
            elif character == '/' and self._regex_allowed(scope_start):
                index = self._scan_regex(index)
                kind = 'regex'
            elif (
                    _identifier_start(character) or
                    (character == '\\' and _IDENTIFIER_ESCAPE.match(source, index) is not None)
            ):
                index = self._scan_identifier(index)
                kind = 'identifier'
            elif (match := _NUMBER.match(source, index)) is not None:
                index = match.end()
                kind = 'number'
            elif character == '}' and stop_at_brace and brace_depth == 0:
                self._emit('template_boundary', index, index + 1, embedded=embedded)
                return index + 1
            else:
                value = character
                for punctuation in _MULTI_CHARACTER_PUNCTUATION:
                    if source.startswith(punctuation, index):
                        # Optional chaining cannot consume the start of a decimal literal (a?.3:0).
                        if punctuation == '?.' and source[index + 2:index + 3].isdigit():
                            continue
                        value = punctuation
                        break
                regex_after = False
                if value == '(':
                    self._parentheses.append(self._statement_head_follows(scope_start))
                elif value == ')':
                    regex_after = self._parentheses.pop() if self._parentheses else False
                elif value == '{':
                    brace_depth += 1
                    self._braces.append(self._block_follows(scope_start, expression=stop_at_brace))
                elif value == '}':
                    brace_depth -= 1
                    regex_after = self._braces.pop() if self._braces else True
                kind = 'punctuation'
                if value not in _SINGLE_CHARACTER_PUNCTUATION and value not in _MULTI_CHARACTER_PUNCTUATION:
                    # Private identifiers retain their # prefix as a separate punctuation token.
                    if value != '#':
                        self._unfinished('Unrecognized JavaScript character', index)
                        kind = 'error'
                self._emit(kind, index, index + len(value), embedded=embedded, regex_after=regex_after)
                index += len(value)
                continue
            self._emit(kind, token_start, index, embedded=embedded)
        if stop_at_brace:
            self._unfinished('Unterminated JavaScript template expression', start)
        return index

    def scan(self) -> list[JsToken]:
        self._tokens = []
        self._parentheses = []
        self._braces = []
        self._scan(0, embedded=False, stop_at_brace=False)
        return self._tokens
