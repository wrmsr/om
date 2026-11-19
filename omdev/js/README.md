# JavaScript utilities

## Token scanning

`lexing.JsScanner` is a small, dependency-free lexer for token-level scraping and highlighting, not a JavaScript
parser or syntax validator:

```python
from omdev.js.lexing import JsScanner
from omdev.js.lexing import JsSourceMap

source = 'const π = "hello";'
tokens = JsScanner(source).scan()
locations = JsSourceMap(source)  # Optional; scanning itself needs no location index.
for token in tokens:
    print(token.kind, token.value, locations.position(token.start))
```

- Tokens partition the entire source in order, without overlaps or gaps. `value` is always exactly
  `source[token.start:token.end]`. Offsets are half-open Python string indices, not byte offsets.
- Kinds are `identifier`, `number`, `string`, `regex`, `template`, `template_boundary`, `punctuation`, `whitespace`,
  `comment`, and (in tolerant mode) `error`. Keywords remain identifiers; escape sequences are not decoded.
- Strings and regexes include delimiters. Comments include their markers; a leading shebang is also a comment.
- Templates are split into string chunks and `${` / `}` boundary tokens. Their expressions are scanned recursively,
  with `embedded=True` on expression tokens. Nested templates work the same way. Consumers should retain boundaries
  when interpreting adjacency, even if they otherwise ignore them.
- `JsSourceMap.position(offset)` returns a code-point offset, UTF-8 byte offset, one-based line and zero-based
  code-point column. Tabs are not expanded. CRLF counts as one line ending; CR, LF, LS and PS also end lines.
  Lone surrogates use UTF-8 `surrogatepass` byte accounting.
- The default mode raises `JsLexError` (a `ValueError` with an `offset`) for unfinished literals/comments or unknown
  characters. `tolerant=True` retains unfinished literals and emits unknown characters as `error`, allowing editor
  buffers to be scanned. Neither mode validates syntax or balanced delimiters. Extremely nested templates can hit
  Python's recursion limit.

Slash disambiguation is heuristic: parentheses/braces remember statement context, but this is not a full grammar.
In particular, ambiguous function/class expression endings and newer regexp grammars may need further work. The
vendored marked source is covered by strict scanner and vendor-parser regression tests.

For lexical extensions, add punctuators to the longest-match table, update expression-prefix context tables when
necessary, or add a dedicated literal-scanning method. Keep token spans lossless and template boundaries explicit.
Keyword and builtin styling tables live separately in `highlights.py`, not in the scanner.

## Highlighting

`highlights.JsHighlighter` implements `omcore.text.highlights.Highlighter`. It accepts source lines and returns the
same text with semantic `code.*` spans, without evaluating code or importing a third-party highlighter. It uses
tolerant scanning, styles interpolation expressions independently of template text, and falls back to plain text on
excessive template nesting. Name classification is lexical, not scope-aware.

The `vendor` package keeps its module-specific parsing in `vendor/parsing.py`; all other vendoring code continues to
use that module's existing interface.
