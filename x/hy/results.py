"""Compiler results: the bridge between Hy's everything-is-an-expression world and Python's statements."""
import ast
import typing as ta

from .models import Object
from .reader.mangling import mangle


if ta.TYPE_CHECKING:
    from .compiler import HyASTCompiler


ResultStatement: ta.TypeAlias = ast.stmt | ast.excepthandler
ResultTempVariable: ta.TypeAlias = ast.Name | ast.FunctionDef | ast.AsyncFunctionDef


##


class Asty:
    """
    Provides `asty.Foo(x, ...)` as shorthand for `ast.Foo(..., lineno=x.start_line, col_offset=x.start_column, ...)`
    (or, for AST nodes and results, `ast.Foo(..., lineno=x.lineno, col_offset=x.col_offset, ...)`).

    Also provides `asty.parse(x, ...)`, which recursively copies the position of `x` onto the parse result.
    """

    POS_ATTRS: ta.ClassVar[ta.Mapping[str, str]] = {
        'lineno': 'start_line',
        'col_offset': 'start_column',
        'end_lineno': 'end_line',
        'end_col_offset': 'end_column',
    }

    @staticmethod
    def _get_pos(node: Object | ast.AST | Result) -> dict[str, int | None]:
        return {
            attr: getattr(node, hy_attr, getattr(node, attr, None))
            for attr, hy_attr in Asty.POS_ATTRS.items()
        }

    @staticmethod
    def _replace_pos(node: ast.AST, pos: ta.Mapping[str, int | None]) -> None:
        for attr, value in pos.items():
            if hasattr(node, attr):
                setattr(node, attr, value)

        for child in ast.iter_child_nodes(node):
            Asty._replace_pos(child, pos)

    def parse(self, x: Object | ast.AST | Result, *args: ta.Any, **kwargs: ta.Any) -> ta.Any:
        res = ast.parse(*args, **kwargs)
        Asty._replace_pos(res, Asty._get_pos(x))
        return res

    def __getattr__(self, name: str) -> ta.Any:
        def make_node(x: Object | ast.AST | Result, **kwargs: ta.Any) -> ta.Any:
            return getattr(ast, name)(**Asty._get_pos(x), **kwargs)

        # Cached on the class, so this is only reached once per node type.
        setattr(Asty, name, staticmethod(make_node))
        return getattr(Asty, name)


asty = Asty()


class Result:
    """
    Smart representation of the result of a Hy-to-AST compilation.

    This object tries to reconcile the Hy world, where everything can be used as an expression, with the Python world,
    where statements and expressions need to coexist.

    To do so, we represent a compiler result as a list of statements `stmts`, terminated by an expression context
    `expr`. The expression context is used when the compiler needs to use the result as an expression.

    Results are chained by addition: adding two results together returns a Result representing the succession of the two
    Results' statements, with the second Result's expression context.

    The Result object is interoperable with Python AST objects: when an AST object gets added to a Result object, it
    gets converted on-the-fly.
    """

    __slots__ = ('expr', 'stmts', 'temp_variables')

    stmts: list[ResultStatement]
    expr: ast.expr | None
    temp_variables: list[ResultTempVariable]

    def __init__(
            self,
            *,
            stmts: ta.Iterable[ResultStatement] = (),
            expr: ast.expr | None = None,
            temp_variables: ta.Iterable[ResultTempVariable] = (),
    ) -> None:
        super().__init__()

        self.stmts = list(stmts)
        self.expr = expr
        self.temp_variables = list(temp_variables)

    def _pos_node(self) -> ast.expr | ResultStatement | None:
        if self.expr is not None:
            return self.expr
        if self.stmts:
            return self.stmts[-1]
        return None

    @property
    def lineno(self) -> int | None:
        return node.lineno if (node := self._pos_node()) is not None else None

    @property
    def col_offset(self) -> int | None:
        return node.col_offset if (node := self._pos_node()) is not None else None

    @property
    def end_lineno(self) -> int | None:
        return node.end_lineno if (node := self._pos_node()) is not None else None

    @property
    def end_col_offset(self) -> int | None:
        return node.end_col_offset if (node := self._pos_node()) is not None else None

    def is_expr(self) -> bool:
        """Check whether this is a pure expression."""

        return self.expr is not None and not self.stmts

    @property
    def force_expr(self) -> ast.expr:
        """The expression context of the Result, or a `None` constant expression if there is none."""

        if self.expr is not None:
            return self.expr

        return ast.Constant(
            value=None,
            lineno=self.stmts[-1].lineno if self.stmts else 0,
            col_offset=self.stmts[-1].col_offset if self.stmts else 0,
        )

    def expr_as_stmt(self) -> Result:
        """
        Convert the Result's expression context to a statement, which is useful when using it in a statement context
        (for instance in a code branch). If there is no expression context, return an empty result.

        `ast.Name`s are dropped if they would follow statements, as they can't have any side effect. 'Bare' names still
        get converted to statements.
        """

        if self.expr is not None and not (isinstance(self.expr, ast.Name) and self.stmts):
            return Result() + asty.Expr(self.expr, value=self.expr)

        return Result()

    def rename(self, compiler: HyASTCompiler, new_name: str) -> None:
        """Rename the Result's temporary variables (`ast.Name`s and function definitions) to `new_name`."""

        new_name = mangle(new_name)

        for var in self.temp_variables:
            if isinstance(var, ast.Name):
                var.id = new_name
                compiler.scope.assign(var)
            elif isinstance(var, (ast.FunctionDef, ast.AsyncFunctionDef)):
                var.name = new_name
            else:
                raise TypeError(f"Don't know how to rename a {var.__class__.__name__}!")

        self.temp_variables = []

    def __add__(self, other: Result | ast.AST) -> Result:
        if isinstance(other, (ast.stmt, ast.excepthandler)):
            return self + Result(stmts=[other])

        # Adding an expression replaces the expression context.
        if isinstance(other, ast.expr):
            return self + Result(expr=other)

        if not isinstance(other, Result):
            raise TypeError(f"Can't add {self!r} with non-compiler result {other!r}")

        result = Result()
        result.stmts = self.stmts + other.stmts
        result.expr = other.expr
        result.temp_variables = other.temp_variables
        return result

    def __str__(self) -> str:
        stmts = ', '.join(ast.dump(x) for x in self.stmts)
        expr = ast.dump(self.expr) if self.expr is not None else None
        return f'Result(stmts=[{stmts}], expr={expr})'
