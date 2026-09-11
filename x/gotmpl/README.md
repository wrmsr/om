# gotmpl

`gotmpl` is a Python 3.14 translation of Go's `text/template` and `text/template/parse` packages. Its lexer, parser,
parse nodes, template namespace, execution state, and builtin functions intentionally follow the order and behavior of
the corresponding Go sources.

```python
from x.gotmpl import Template

template = Template.new("welcome").parse("Hello, {{.Name}}!")
assert template.render({"Name": "Gopher"}) == "Hello, Gopher!"
```

The execution API also mirrors Go's writer-oriented API:

```python
template.execute(writer, data)
template.execute_template(writer, "associated-name", data)
```

## Python mappings

- Go structs map to Python objects. Template field and method names must begin with an uppercase Unicode letter, as Go
  exported identifiers do. Go maps map to Python mappings and may use lowercase keys.
- A Python callable can be installed with `Template.funcs`. A `(value, None)` result represents Go's `(value, nil)`,
  and a `(value, exception)` result represents `(value, error)`.
- Lists, tuples, byte strings, mappings, non-negative integers, and Python iterables can be ranged over. Iterable
  support is the Python counterpart of Go iterator functions.
- `missingkey=zero` infers a zero value from a non-empty, homogeneous Python mapping. An empty Python `dict` carries no
  element type, so its missing zero value is represented by `None` and renders as `<no value>`.

## Deliberate limits

Go strings are arbitrary bytes while Python strings are Unicode scalar sequences. Lexer positions and the `len`,
`index`, and `slice` builtins operate on UTF-8 bytes to preserve Go behavior. If a slice cuts through a multibyte rune,
the result uses Python's `surrogateescape` representation; callers encoding that result must also use
`errors='surrogateescape'`. Python cannot otherwise represent Go's invalid UTF-8 string byte-for-byte.

Go and Python can ship different Unicode table versions. Quoting and escaping therefore use Python's built-in Unicode
printability classification; an obscure newly assigned code point may be rendered literally in one runtime and escaped
in the other, without changing the represented text.

The `printf` builtin implements the commonly used Go formatting verbs, flags, widths, precisions, and argument indexes.
It does not attempt to reproduce every reflection-heavy corner of `fmt`, such as formatter interfaces, cyclic values,
or exact Go-syntax rendering of arbitrary user-defined values. Those cases would require translating most of Go's
`fmt` and reflection packages and are intentionally outside this package.

Channels, pointers, unsafe pointers, typed nils, slice capacity, and Go's exact static assignability rules have no
general Python equivalent. Their ordinary Python counterparts are supported where the intended behavior is
unambiguous; programs relying on those representation details should adapt their data before rendering.
