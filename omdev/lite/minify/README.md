# minify

A whitespace / comment / docstring minifier for lite (python 3.8) source, written as standard (3.14) code. It is a
single-purpose unparser: it reads a module with the host `ast`, drops bare literal statements, and prints the tree back
with no optional whitespace, one-character indentation, `;`-joined simple statements, and only the parentheses needed
to preserve the tree. Nothing is renamed and no other transform is applied - on gzipped output those were measured to
be worth under 3%, and this is the part that was worth ~35%.

Every run re-parses its own output and checks it against the printed tree with `ast.dump`, so a printer bug can only
ever fail loudly, never produce a file that compiles to something else.

## Usage

```
python -m minify in.py -o out.py [--keep-literal-statements] [--no-verify] [--no-shebang] [--stats]
```

```python
from minify import minify

out = minify(src)
```

## Layout

- `precedence.py` - the expression precedence ladder (CPython's `ast._Unparser` model, with `yield` moved below
  tuples so that `x = yield a, b` and `return (yield)` both come out right).
- `writing.py` - the token writer, and the one rule for when a space is required between two tokens.
- `literals.py` - constants via `repr`, and f-string assembly under 3.8's rules (no backslashes and no delimiter quote
  inside expression parts).
- `expressions.py` / `statements.py` - the printers. Each expression is printed in a context precedence and
  parenthesizes itself iff its own is lower; suites of simple statements go inline after the header.
- `transforms.py` - removal of docstrings and other bare literal statements (an emptied body becomes `0`).
- `verification.py` - the AST round-trip check.
- `minifying.py` - the `minify` entry point.

## Target syntax

The printer covers everything that parses under python 3.8. Later syntax (`match`, `except*`, `type`, PEP 695
parameters, PEP 646 subscripts, 3.12 f-string quote reuse) raises `UnsupportedNodeError` /
`UnrepresentableFStringError` rather than being printed wrong. The test suite round-trips the running interpreter's
whole standard library, skipping those.
