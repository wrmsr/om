"""Compiler results: the bridge between Hy's everything-is-an-expression world and Python's statements."""
import ast
import traceback
import typing as ta

from .models import Object
from .reader.mangling import mangle


if ta.TYPE_CHECKING:
    from .compiler import HyASTCompiler


ResultStatement: ta.TypeAlias = ast.stmt | ast.excepthandler


##


# Provide asty.Foo(x, ...) as shorthand for
# ast.Foo(..., lineno=x.start_line, col_offset=x.start_column) or
# ast.Foo(..., lineno=x.lineno, col_offset=x.col_offset)
# Also provides asty.parse(x, ...) which recursively copies x's position data onto the parse result.
class Asty:
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
        setattr(
            Asty,
            name,
            staticmethod(
                lambda x, **kwargs: getattr(ast, name)(**Asty._get_pos(x), **kwargs),
            ),
        )
        return getattr(Asty, name)


asty = Asty()


class Result:
    """
    Smart representation of the result of a hy->AST compilation

    This object tries to reconcile the hy world, where everything can be used as an expression, with the Python world,
    where statements and expressions need to coexist.

    To do so, we represent a compiler result as a list of statements `stmts`, terminated by an expression context
    `expr`. The expression context is used when the compiler needs to use the result as an expression.

    Results are chained by addition: adding two results together returns a Result representing the succession of the two
    Results' statements, with the second Result's expression context.

    We make sure that a non-empty expression context does not get clobbered by adding more results, by checking accesses
    to the expression context. We assume that the context has been used, or deliberately ignored, if it has been
    accessed.

    The Result object is interoperable with python AST objects: when an AST object gets added to a Result object, it
    gets converted on-the-fly.
    """

    __slots__ = ('stmts', 'temp_variables', '_expr', '__used_expr')

    def __init__(
            self,
            *,
            stmts: ta.Iterable[ResultStatement] = (),
            expr: ast.expr | None = None,
            temp_variables: ta.Iterable[ast.Name | ast.FunctionDef | ast.AsyncFunctionDef] = (),
    ) -> None:
        super().__init__()

        self.stmts = list(stmts)
        self.temp_variables = list(temp_variables)
        self._expr = expr

        self.__used_expr = False

    @property
    def expr(self) -> ast.expr | None:
        self.__used_expr = True
        return self._expr

    @expr.setter
    def expr(self, value: ast.expr | None) -> None:
        self.__used_expr = False
        self._expr = value

    @property
    def lineno(self) -> int | None:
        if self._expr is not None:
            return self._expr.lineno
        if self.stmts:
            return self.stmts[-1].lineno
        return None

    @property
    def col_offset(self) -> int | None:
        if self._expr is not None:
            return self._expr.col_offset
        if self.stmts:
            return self.stmts[-1].col_offset
        return None

    @property
    def end_col_offset(self) -> int | None:
        if self._expr is not None:
            return self._expr.end_col_offset
        if self.stmts:
            return self.stmts[-1].end_col_offset
        return None

    @property
    def end_lineno(self) -> int | None:
        if self._expr is not None:
            return self._expr.end_lineno
        if self.stmts:
            return self.stmts[-1].end_lineno
        return None

    def is_expr(self) -> bool:
        """Check whether I am a pure expression"""

        return self._expr is not None and not self.stmts

    @property
    def force_expr(self) -> ast.expr:
        """
        Force the expression context of the Result.

        If there is no expression context, we return a "None" expression.
        """

        if self.expr:
            return self.expr
        return ast.Constant(
            value=None,
            lineno=self.stmts[-1].lineno if self.stmts else 0,
            col_offset=self.stmts[-1].col_offset if self.stmts else 0,
        )

    def expr_as_stmt(self) -> Result:
        """
        Convert the Result's expression context to a statement

        This is useful when we want to use the stored expression in a statement context (for instance in a code branch).

        We drop ast.Names if they are appended to statements, as they can't have any side effect. "Bare" names still get
        converted to statements.

        If there is no expression context, return an empty result.
        """

        if self.expr and not (isinstance(self.expr, ast.Name) and self.stmts):
            return Result() + asty.Expr(self.expr, value=self.expr)
        return Result()

    def rename(self, compiler: HyASTCompiler, new_name: str) -> None:
        """
        Rename the Result's temporary variables to a `new_name`.

        We know how to handle ast.Names and ast.FunctionDefs.
        """

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
        # If we add an ast statement, convert it first
        if isinstance(other, ast.stmt):
            return self + Result(stmts=[other])

        # If we add an ast expression, clobber the expression context
        if isinstance(other, ast.expr):
            return self + Result(expr=other)

        if isinstance(other, ast.excepthandler):
            return self + Result(stmts=[other])

        if not isinstance(other, Result):
            raise TypeError(f"Can't add {self!r} with non-compiler result {other!r}")

        # Check for expression context clobbering
        if self.expr and not self.__used_expr:
            traceback.print_stack()
            print(
                f'Bad boy clobbered expr {ast.dump(self.expr)} with '
                f'{ast.dump(other.expr) if other.expr is not None else None}',
            )

        # Fairly obvious addition
        result = Result()
        result.stmts = self.stmts + other.stmts
        result.expr = other.expr
        result.temp_variables = other.temp_variables

        return result

    def __str__(self) -> str:
        return 'Result(stmts=[{}], expr={})'.format(
            ', '.join(ast.dump(x) for x in self.stmts),
            ast.dump(self.expr) if self.expr else None,
        )
