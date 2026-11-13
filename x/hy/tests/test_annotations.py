import ast
import typing as ta

import pytest

from ..models import Expression
from ..models import Integer
from ..models import List
from ..models import Symbol
from ..models import Tuple
from ..reader import read
from ..reader import read_many
from ..reader.exceptions import LexException
from ..runtime import HyRuntime


def sym(s):
    return Symbol(s)


def expr(*xs):
    return Expression(xs)


def annotation(src):
    form = read(src)
    assert isinstance(form, Expression)
    assert form[0] == sym('annotate')
    return form[2]


def py_annotation(src):
    """The Python source of the annotation of `x` in `(setv <src> x 1)`."""

    tree = HyRuntime().compile(f'(setv {src} x 1)')
    stmt = tree.body[0]
    assert isinstance(stmt, ast.AnnAssign)
    return ast.unparse(stmt.annotation)


##


def test_reading():
    assert annotation('#^int x') == sym('int')
    assert annotation('#^ int x') == sym('int')

    assert annotation('#^ta.Sequence[int] x') == expr(
        sym('get'),
        expr(sym('.'), sym('ta'), sym('Sequence')),
        sym('int'),
    )

    assert annotation('#^dict[str int] x') == expr(sym('get'), sym('dict'), Tuple([sym('str'), sym('int')]))

    assert annotation('#^int|None x') == expr(sym('|'), sym('int'), sym('None'))
    assert annotation('#^int|str|None x') == expr(sym('|'), sym('int'), sym('str'), sym('None'))

    assert annotation('#^ta.Callable[[int] str] x') == expr(
        sym('get'),
        expr(sym('.'), sym('ta'), sym('Callable')),
        Tuple([List([sym('int')]), sym('str')]),
    )


@pytest.mark.parametrize(('src', 'py'), [
    ('#^int', 'int'),
    ('#^ int', 'int'),
    ('#^ (| int None)', 'int | None'),
    ('#^(get ta.Sequence int)', 'ta.Sequence[int]'),
    ('#^ta.Sequence[int]', 'ta.Sequence[int]'),
    ('#^ ta.Sequence[int]', 'ta.Sequence[int]'),
    ('#^ta.Mapping[str int]', 'ta.Mapping[str, int]'),
    ('#^int|None', 'int | None'),
    ('#^ta.Sequence[int]|None', 'ta.Sequence[int] | None'),
    ('#^ta.Mapping[str ta.Sequence[int|None]]|None', 'ta.Mapping[str, ta.Sequence[int | None]] | None'),
    ('#^ta.Callable[[int str] ta.Awaitable[None]]', 'ta.Callable[[int, str], ta.Awaitable[None]]'),
    ('#^tuple[int ...]', 'tuple[int, ...]'),
    ('#^tuple[#()]', 'tuple[()]'),
    ('#^type[Foo]|None', 'type[Foo] | None'),
    ('#^"Foo"', "'Foo'"),
    ('#^ta.Annotated[int (some-meta 1)]', 'ta.Annotated[int, some_meta(1)]'),
    ('#^tuple[#* Ts]', 'tuple[*Ts,]'),  # Equivalent to `tuple[*Ts]`.
    ('#^#(int str)', '(int, str)'),
])
def test_compiled(src, py):
    assert py_annotation(src) == py


def test_postfix_syntax_is_annotation_only():
    # Outside of annotations, `[` and `|` mean what they always have.
    assert list(read_many('a[1]')) == [sym('a'), List([Integer(1)])]
    assert read('a|b') == sym('a|b')

    # Including within the annotated target, and after it.
    form = read('#^int [x 1]')
    assert form == expr(sym('annotate'), List([sym('x'), Integer(1)]), sym('int'))
    assert list(read_many('#^int x[1]'))[1] == List([Integer(1)])


def test_reader_macros_take_precedence():
    rt = HyRuntime()
    assert rt.eval('(defreader ^foo \'1) #^foo') == 1
    assert rt.eval('(defreader ^int \'"read") (setv #^ int x 1) #^int') == 'read'


def test_errors():
    with pytest.raises(LexException):
        read('#^foo[] x')
    with pytest.raises(LexException):
        read('#^foo[#** x] x')


def test_runtime_annotations():
    rt = HyRuntime()
    m = rt.exec("""
        (import dataclasses :as dc)

        (defn #^ta.Sequence[int] f [#^ta.Mapping[str int]|None m #^Later [l None] #^int|None [n None]]
          [(len (or m {})) n])

        (defclass [(dc.dataclass :frozen True)] Point []
          #^int x
          #^int|None y
          #^ta.Sequence[Later] ls)

        (defclass Later [])

        (setv #^dict[str ta.Any] d {})
    """)

    assert m.f({'a': 1}) == [1, None]
    assert m.f.__annotations__ == {
        'm': ta.Mapping[str, int] | None,
        'l': m.Later,
        'n': int | None,
        'return': ta.Sequence[int],
    }

    later = m.Later
    assert ta.get_type_hints(m.Point) == {
        'x': int,
        'y': int | None,
        'ls': ta.Sequence[later],  # type: ignore[valid-type]
    }
    assert m.Point(1, None, []).y is None

    assert m.__annotations__ == {'d': dict[str, ta.Any]}
