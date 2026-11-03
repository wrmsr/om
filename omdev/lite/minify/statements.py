"""
Prints statements with one-character indentation, consecutive simple statements joined by `;` on one line, and a suite
consisting only of simple statements placed on the same line as its header (`if x:a=1;b=2`). Compound statements always
start a new line, as the grammar requires.
"""
import ast
import functools
import typing as ta

from .expressions import ExpressionPrinter
from .expressions import UnsupportedNodeError
from .expressions import bare_tuple_precedence
from .expressions import bin_op_symbol
from .precedence import Precedence
from .writing import SourceWriter


##


_SIMPLE_STATEMENT_TYPES: tuple[type[ast.stmt], ...] = (
    ast.Expr,
    ast.Assign,
    ast.AugAssign,
    ast.AnnAssign,
    ast.Return,
    ast.Delete,
    ast.Pass,
    ast.Break,
    ast.Continue,
    ast.Raise,
    ast.Global,
    ast.Nonlocal,
    ast.Import,
    ast.ImportFrom,
    ast.Assert,
)


def is_simple_statement(node: ast.stmt) -> bool:
    return isinstance(node, _SIMPLE_STATEMENT_TYPES)


##


class StatementPrinter:
    def __init__(self, writer: SourceWriter) -> None:
        super().__init__()

        self._writer = writer
        self._exprs = ExpressionPrinter(writer)
        self._depth = 0

    #

    def _write(self, s: str) -> None:
        self._writer.write(s)

    def _newline(self) -> None:
        self._writer.newline(self._depth)

    def _print_expr(self, node: ast.expr, prec: Precedence = Precedence.TEST) -> None:
        self._exprs.print_expr(node, prec)

    #

    def _print_statement(self, node: ast.stmt) -> None:
        try:
            fn = self._DISPATCH[type(node)]
        except KeyError:
            raise UnsupportedNodeError(type(node).__name__) from None

        fn(self, node)

    def _print_block(self, body: ta.Sequence[ast.stmt], *, inline: bool = False) -> None:
        prev_simple = False
        for i, s in enumerate(body):
            simple = is_simple_statement(s)
            if i == 0 and inline:
                pass
            elif simple and prev_simple:
                self._write(';')
            else:
                self._newline()
            self._print_statement(s)
            prev_simple = simple

    def _print_suite(self, body: ta.Sequence[ast.stmt]) -> None:
        if all(is_simple_statement(s) for s in body):
            self._print_block(body, inline=True)
        else:
            self._depth += 1
            self._print_block(body)
            self._depth -= 1

    def _print_clause(self, keyword: str, body: ta.Sequence[ast.stmt]) -> None:
        self._newline()
        self._write(keyword + ':')
        self._print_suite(body)

    def print_module(self, node: ast.Module) -> None:
        self._print_block(node.body, inline=True)

    ##
    # Simple statements

    def _print_expr_statement(self, node: ast.Expr) -> None:
        self._print_expr(node.value, bare_tuple_precedence(node.value, allow_yield=True))

    def _print_assign(self, node: ast.Assign) -> None:
        for t in node.targets:
            self._print_expr(t, Precedence.TUPLE)
            self._write('=')
        self._print_expr(node.value, Precedence.YIELD)

    def _print_aug_assign(self, node: ast.AugAssign) -> None:
        self._print_expr(node.target, Precedence.ATOM)
        self._write(bin_op_symbol(node.op) + '=')
        self._print_expr(node.value, bare_tuple_precedence(node.value, allow_yield=True))

    def _print_ann_assign(self, node: ast.AnnAssign) -> None:
        if not node.simple and isinstance(node.target, ast.Name):
            self._write('(')
            self._print_expr(node.target, Precedence.ATOM)
            self._write(')')
        else:
            self._print_expr(node.target, Precedence.ATOM)
        self._write(':')
        self._print_expr(node.annotation)
        if node.value is not None:
            self._write('=')
            self._print_expr(node.value, Precedence.YIELD)

    def _print_return(self, node: ast.Return) -> None:
        self._write('return')
        if node.value is not None:
            self._print_expr(node.value, Precedence.TUPLE)

    def _print_delete(self, node: ast.Delete) -> None:
        self._write('del')
        for i, t in enumerate(node.targets):
            if i:
                self._write(',')
            self._print_expr(t)

    def _print_keyword_statement(self, node: ast.stmt, *, keyword: str) -> None:
        self._write(keyword)

    def _print_raise(self, node: ast.Raise) -> None:
        self._write('raise')
        if node.exc is not None:
            self._print_expr(node.exc)
        if node.cause is not None:
            self._write('from')
            self._print_expr(node.cause)

    def _print_names_statement(self, node: ast.Global | ast.Nonlocal, *, keyword: str) -> None:
        self._write(keyword)
        self._write(','.join(node.names))

    def _print_assert(self, node: ast.Assert) -> None:
        self._write('assert')
        self._print_expr(node.test)
        if node.msg is not None:
            self._write(',')
            self._print_expr(node.msg)

    def _print_aliases(self, names: ta.Iterable[ast.alias]) -> None:
        self._write(','.join(a.name if a.asname is None else f'{a.name} as {a.asname}' for a in names))

    def _print_import(self, node: ast.Import) -> None:
        self._write('import')
        self._print_aliases(node.names)

    def _print_import_from(self, node: ast.ImportFrom) -> None:
        self._write('from')
        self._write('.' * node.level + (node.module or ''))
        self._write('import')
        self._print_aliases(node.names)

    ##
    # Compound statements

    def _print_if(self, node: ast.If) -> None:
        self._write('if')
        self._print_expr(node.test)
        self._write(':')
        self._print_suite(node.body)

        while len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            node = node.orelse[0]
            self._newline()
            self._write('elif')
            self._print_expr(node.test)
            self._write(':')
            self._print_suite(node.body)

        if node.orelse:
            self._print_clause('else', node.orelse)

    def _print_for(self, node: ast.For | ast.AsyncFor) -> None:
        if isinstance(node, ast.AsyncFor):
            self._write('async')
        self._write('for')
        self._print_expr(node.target, Precedence.TUPLE)
        self._write('in')
        self._print_expr(node.iter, bare_tuple_precedence(node.iter))
        self._write(':')
        self._print_suite(node.body)
        if node.orelse:
            self._print_clause('else', node.orelse)

    def _print_while(self, node: ast.While) -> None:
        self._write('while')
        self._print_expr(node.test)
        self._write(':')
        self._print_suite(node.body)
        if node.orelse:
            self._print_clause('else', node.orelse)

    def _print_with(self, node: ast.With | ast.AsyncWith) -> None:
        if isinstance(node, ast.AsyncWith):
            self._write('async')
        self._write('with')
        for i, item in enumerate(node.items):
            if i:
                self._write(',')
            self._print_expr(item.context_expr)
            if item.optional_vars is not None:
                self._write('as')
                self._print_expr(item.optional_vars)
        self._write(':')
        self._print_suite(node.body)

    def _print_try(self, node: ast.Try) -> None:
        self._write('try:')
        self._print_suite(node.body)
        for h in node.handlers:
            self._newline()
            self._write('except')
            if h.type is not None:
                self._print_expr(h.type)
            if h.name is not None:
                self._write('as')
                self._write(h.name)
            self._write(':')
            self._print_suite(h.body)
        if node.orelse:
            self._print_clause('else', node.orelse)
        if node.finalbody:
            self._print_clause('finally', node.finalbody)

    def _print_decorators(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
        for d in node.decorator_list:
            self._write('@')
            self._print_expr(d)
            self._newline()

    def _print_function_def(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._print_decorators(node)
        if isinstance(node, ast.AsyncFunctionDef):
            self._write('async')
        self._write('def')
        self._write(node.name)
        self._write('(')
        self._exprs.print_arguments(node.args)
        self._write(')')
        if node.returns is not None:
            self._write('->')
            self._print_expr(node.returns)
        self._write(':')
        self._print_suite(node.body)

    def _print_class_def(self, node: ast.ClassDef) -> None:
        self._print_decorators(node)
        self._write('class')
        self._write(node.name)
        if node.bases or node.keywords:
            self._write('(')
            for i, b in enumerate(node.bases):
                if i:
                    self._write(',')
                self._print_expr(b)
            for i, k in enumerate(node.keywords):
                if i or node.bases:
                    self._write(',')
                self._exprs.print_keyword(k)
            self._write(')')
        self._write(':')
        self._print_suite(node.body)

    #

    _DISPATCH: ta.ClassVar[ta.Mapping[type[ast.stmt], ta.Callable[[StatementPrinter, ta.Any], None]]] = {
        ast.Expr: _print_expr_statement,
        ast.Assign: _print_assign,
        ast.AugAssign: _print_aug_assign,
        ast.AnnAssign: _print_ann_assign,
        ast.Return: _print_return,
        ast.Delete: _print_delete,
        ast.Pass: functools.partial(_print_keyword_statement, keyword='pass'),
        ast.Break: functools.partial(_print_keyword_statement, keyword='break'),
        ast.Continue: functools.partial(_print_keyword_statement, keyword='continue'),
        ast.Raise: _print_raise,
        ast.Global: functools.partial(_print_names_statement, keyword='global'),
        ast.Nonlocal: functools.partial(_print_names_statement, keyword='nonlocal'),
        ast.Assert: _print_assert,
        ast.Import: _print_import,
        ast.ImportFrom: _print_import_from,
        ast.If: _print_if,
        ast.For: _print_for,
        ast.AsyncFor: _print_for,
        ast.While: _print_while,
        ast.With: _print_with,
        ast.AsyncWith: _print_with,
        ast.Try: _print_try,
        ast.FunctionDef: _print_function_def,
        ast.AsyncFunctionDef: _print_function_def,
        ast.ClassDef: _print_class_def,
    }
