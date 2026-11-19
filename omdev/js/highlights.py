"""Lightweight lexical JavaScript highlighting, not parsing or scope-aware name resolution."""
import bisect
import typing as ta

from omcore.text import highlights as hl
from omcore.text import styled as st

from .lexing import JsScanner


##


_KEYWORDS: ta.AbstractSet[str] = frozenset([
    'as', 'async', 'await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 'default',
    'delete', 'do', 'else', 'enum', 'export', 'extends', 'false', 'finally', 'for', 'from', 'function', 'if',
    'implements', 'import', 'in', 'instanceof', 'interface', 'let', 'new', 'null', 'of', 'package', 'private',
    'protected', 'public', 'return', 'static', 'super', 'switch', 'this', 'throw', 'true', 'try', 'typeof',
    'var', 'void', 'while', 'with', 'yield',
])

_BUILTINS: ta.AbstractSet[str] = frozenset([
    'AggregateError', 'Array', 'ArrayBuffer', 'Atomics', 'BigInt', 'BigInt64Array', 'BigUint64Array', 'Boolean',
    'DataView', 'Date', 'Error', 'EvalError', 'FinalizationRegistry', 'Float16Array', 'Float32Array',
    'Float64Array', 'Function', 'Infinity', 'Int8Array', 'Int16Array', 'Int32Array', 'Intl', 'Iterator', 'JSON',
    'Map', 'Math', 'NaN', 'Number', 'Object', 'Promise', 'Proxy', 'RangeError', 'ReferenceError', 'Reflect',
    'RegExp', 'Set', 'SharedArrayBuffer', 'String', 'Symbol', 'SyntaxError', 'TypeError', 'URIError',
    'Uint8Array', 'Uint8ClampedArray', 'Uint16Array', 'Uint32Array', 'WeakMap', 'WeakRef', 'WeakSet', 'console',
    'decodeURI', 'decodeURIComponent', 'encodeURI', 'encodeURIComponent', 'eval', 'globalThis', 'isFinite',
    'isNaN', 'parseFloat', 'parseInt', 'undefined',
])

_TOKEN_STYLES: ta.Mapping[str, str] = {
    'comment': 'code.comment',
    'string': 'code.string',
    'regex': 'code.string',
    'template': 'code.string',
    'number': 'code.number',
}


class JsHighlighter(hl.Highlighter):
    """
    Source-preserving, tolerant highlighting using the shared JavaScript scanner.

    Keywords, common globals and function/class names are lexical heuristics; bindings and shadowing are not resolved.
    Property accesses are left plain, and template interpolations are highlighted as code, not string contents.
    """

    def highlight(self, lines: ta.Sequence[str]) -> hl.HighlightedLines:
        source = '\n'.join(lines)
        try:
            tokens = JsScanner(source, tolerant=True).scan()
        except RecursionError:
            # An editor must still render adversarially deep template interpolation.
            return [st.StyledText(line) for line in lines]

        starts: list[int] = []
        offset = 0
        for line in lines:
            starts.append(offset)
            offset += len(line) + 1
        spans: list[list[st.StyleSpan]] = [[] for _ in lines]

        previous: str | None = None
        declaration: str | None = None
        for token in tokens:
            tag = _TOKEN_STYLES.get(token.kind)
            if token.kind == 'identifier':
                if previous not in ('.', '?.', '#'):
                    if declaration is not None and token.value not in _KEYWORDS:
                        tag = 'code.def'
                    elif token.value in _KEYWORDS:
                        tag = 'code.keyword'
                    elif token.value in _BUILTINS:
                        tag = 'code.builtin'

            if token.kind not in ('whitespace', 'comment'):
                if tag == 'code.keyword' and token.value in ('function', 'class'):
                    declaration = token.value
                elif not (declaration == 'function' and token.value == '*'):
                    declaration = None
                previous = token.value

            if tag is None or not starts:
                continue

            row = max(0, bisect.bisect_right(starts, token.start) - 1)
            while row < len(lines) and starts[row] < token.end:
                start = max(0, token.start - starts[row])
                end = min(len(lines[row]), token.end - starts[row])
                if end > start:
                    spans[row].append(st.StyleSpan.of(start, end, tag))
                row += 1

        return [st.StyledText(line, tuple(row_spans)) for line, row_spans in zip(lines, spans)]
