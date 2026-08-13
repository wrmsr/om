import dataclasses as dc
import io
import typing as ta

from omcore import lang


##


@ta.final
@dc.dataclass(frozen=True)
class Quote:
    s: str


type Const = ta.Union[  # noqa
    int,
    float,
    Quote,
]


CONST_TYPES: ta.Final[tuple[type[Const], ...]] = (
    int,
    float,
    Quote,
)


type Sexp = ta.Union[  # noqa
    str,
    Const,
    list[Sexp],
]


##


def quote(s: str) -> Quote:
    return Quote(s)


def render_to(out: lang.SupportsWrite[str], *xs: Sexp) -> None:
    def rec(c: Sexp) -> None:
        if isinstance(c, Quote):
            s = (
                c.s
                .replace('\\', '\\\\')
                .replace('"', '\\"')
                .replace('\\n', '\\\\n')
            )
            out.write(f'"{s}"')

        elif isinstance(c, CONST_TYPES):
            out.write(str(c))

        elif isinstance(c, str):
            out.write(c)

        elif isinstance(c, list):
            out.write('(')
            for j, n in enumerate(c):
                if j:
                    out.write(' ')
                rec(n)
            out.write(')')

        else:
            raise TypeError(c)

    for i, x in enumerate(xs):
        if i:
            out.write('\n')
        rec(x)


def render(*xs: Sexp) -> str:
    out = io.StringIO()
    render_to(out)
    return out.getvalue()


##


def _main() -> None:
    assert render('hi') == 'hi'
    assert render(['hi', ['there']]) == '(hi (there))'


if __name__ == '__main__':
    _main()
