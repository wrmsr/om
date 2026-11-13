import pytest

from ...compiler import HyASTCompiler
from ...errors import HyMacroExpansionError
from ...globalruntime import get_global_runtime
from ...macros import macro
from ...macros import macroexpand
from ...macros import rename_function
from ...models import Expression
from ...models import Float
from ...models import List
from ...models import String
from ...models import Symbol
from ...reader import read


RT = get_global_runtime()
hy = RT.hy


@macro('test')
def tmac(*tree):
    """Turn an expression into a list"""

    return List(tree)


def test_preprocessor_simple():
    """Test basic macro expansion"""

    obj = macroexpand(read('(test "one" "two")'), __name__, HyASTCompiler(__name__, runtime=RT))
    assert obj == List([String('one'), String('two')])
    assert type(obj) is List


def test_preprocessor_expression():
    """Test that macro expansion doesn't recurse"""

    obj = macroexpand(
        read('(test (test "one" "two"))'), __name__, HyASTCompiler(__name__, runtime=RT),
    )

    assert type(obj) is List
    assert type(obj[0]) is Expression

    assert obj[0] == Expression([Symbol('test'), String('one'), String('two')])

    obj = List([String('one'), String('two')])
    form = read('(shill ["one" "two"])')
    assert isinstance(form, Expression)
    obj = form[1]
    assert obj == macroexpand(obj, __name__, HyASTCompiler(__name__, runtime=RT))


def test_preprocessor_exceptions():
    """Test that macro expansion raises appropriate exceptions"""

    with pytest.raises(HyMacroExpansionError) as excinfo:
        macroexpand(read('(when)'), __name__, HyASTCompiler(__name__, runtime=RT))
    assert 'TypeError: when()' in excinfo.value.msg


def test_macroexpand_nan():
    # https://github.com/hylang/hy/issues/1574
    import math

    nan = float('nan')
    x = macroexpand(Float(nan), __name__, HyASTCompiler(__name__, runtime=RT))
    assert type(x) is Float
    assert math.isnan(x)


def test_macroexpand_source_data():
    # https://github.com/hylang/hy/issues/1944
    ast = Expression([Symbol('when'), String('a')])
    ast.start_line = 3
    ast.start_column = 5
    bad = macroexpand(ast, f'{hy.__package__}.core.macros', once=True)
    assert isinstance(bad, Expression)
    assert bad.start_line == 3
    assert bad.start_column == 5


def test_renamed_function_metadata():
    def original(value: int, *, offset: int = 2) -> int:
        return value + offset

    setattr(original, 'marker', 'macro metadata')
    renamed = rename_function(original, 'renamed')
    assert renamed.__name__ == 'renamed'
    assert renamed(3) == 5
    assert renamed.__dict__ == original.__dict__
    assert renamed.__kwdefaults__ == original.__kwdefaults__
    assert renamed.__kwdefaults__ is not original.__kwdefaults__
    assert renamed.__annotations__ == original.__annotations__
