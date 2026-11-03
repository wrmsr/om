"""
Rendering of constants and f-strings.

Plain constants are rendered with `repr`, which already picks the quote character that minimizes escaping and escapes
exactly the characters that need it.

F-strings have to be assembled by hand because the output must be valid on python 3.8, where the expression parts of an
f-string may not contain the delimiter quote nor any backslash. Delimiters are tried in order of cost (single quote,
double quote, then the two triple-quote forms), those that no expression part contains are candidates, and the one
giving the shortest result once the literal parts are escaped to suit it wins.
"""
import dataclasses as dc
import typing as ta


type FStringPart = FStringLiteral | FStringField


##


class UnrepresentableFStringError(Exception):
    pass


@dc.dataclass(frozen=True)
class FStringLiteral:
    text: str


@dc.dataclass(frozen=True)
class FStringField:
    expr: str
    conversion: int = -1
    spec: ta.Sequence[FStringPart] | None = None


##


_INFINITY_LITERAL = '1e999'

_DELIMITERS: ta.Sequence[str] = ("'", '"', "'''", '"""')


def render_constant(value: ta.Any, *, kind: str | None = None) -> str:
    if value is None or value is True or value is False:
        return repr(value)

    if value is ...:
        return '...'

    if isinstance(value, str):
        return (kind or '') + repr(value)

    if isinstance(value, bytes):
        return repr(value)

    if isinstance(value, int):
        return repr(value)

    if isinstance(value, float):
        return _render_float(value)

    if isinstance(value, complex):
        # Only pure-imaginary complex constants can come out of the parser.
        return _render_float(value.imag) + 'j'

    raise TypeError(value)


def _render_float(value: float) -> str:
    # An overflowing literal like `1e400` parses to infinity, which has no repr that parses back.
    return _INFINITY_LITERAL if value == float('inf') else repr(value)


def escape_fstring_literal(text: str, *, quote: str) -> str:
    out: list[str] = []
    for c in text:
        if c == '{' or c == '}':
            out.append(c * 2)
        elif c == quote:
            out.append('\\' + c)
        elif c == '\\' or not c.isprintable():
            out.append(repr(c)[1:-1])
        else:
            out.append(c)
    return ''.join(out)


def _iter_field_exprs(parts: ta.Iterable[FStringPart]) -> ta.Iterator[str]:
    for p in parts:
        if isinstance(p, FStringField):
            yield p.expr
            if p.spec is not None:
                yield from _iter_field_exprs(p.spec)


def _render_fstring_body(parts: ta.Iterable[FStringPart], *, delimiter: str) -> str:
    out: list[str] = []
    for p in parts:
        match p:
            case FStringLiteral(text):
                out.append(escape_fstring_literal(text, quote=delimiter[0]))

            case FStringField(expr, conversion, spec):
                # `{ {` keeps a leading dict / set display from reading as a doubled brace.
                out.append('{ ' if expr.startswith('{') else '{')
                out.append(expr)
                if conversion != -1:
                    out.append('!' + chr(conversion))
                if spec is not None:
                    out.append(':' + _render_fstring_body(spec, delimiter=delimiter))
                out.append('}')

    return ''.join(out)


def assemble_fstring(parts: ta.Sequence[FStringPart]) -> str:
    exprs = list(_iter_field_exprs(parts))

    for e in exprs:
        if '\\' in e:
            raise UnrepresentableFStringError(f'backslash in f-string expression is not valid before 3.12: {e!r}')

    candidates = [
        'f' + delimiter + _render_fstring_body(parts, delimiter=delimiter) + delimiter
        for delimiter in _DELIMITERS
        if not any(delimiter in e for e in exprs)
    ]
    if not candidates:
        raise UnrepresentableFStringError(f'no quote delimiter is free in f-string expressions: {exprs!r}')

    return min(candidates, key=len)
