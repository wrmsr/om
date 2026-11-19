# ruff: noqa: SLF001
"""Python operators."""
import ast
import math
import typing as ta

from omcore import check

from ...compiler import HyASTCompiler
from ...compiler import mkexpr
from ...funcparserlib.parser import many
from ...funcparserlib.parser import oneplus
from ...macros import pattern_macro
from ...models import Expression
from ...models import Integer
from ...models import Object
from ...models import Symbol
from ...patterns import FORM
from ...patterns import SYM
from ...patterns import times
from ...reader import mangle
from ...results import Result
from ...results import ResultStatement
from ...results import asty


##


_UNARY_OPS: ta.Mapping[str, type[ast.unaryop]] = {
    'not': ast.Not,
    'bnot': ast.Invert,
}


@pattern_macro(['not', 'bnot'], [FORM], shadow=True)
def compile_unary_operator(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        arg: Object,
) -> Result:
    operand = compiler.compile(arg)
    return operand + asty.UnaryOp(expr, op=_UNARY_OPS[root](), operand=operand.force_expr)


##


class _BoolOpCompiler:
    """
    Compiles `and` and `or`. Operands which compile to pure expressions are collected into a `BoolOp`, but once an
    operand needs statements, the value so far is saved to a temporary variable, and the remaining operands are
    compiled into nested `if` statements which implement the short-circuiting.
    """

    def __init__(self, compiler: HyASTCompiler, root: str) -> None:
        super().__init__()

        self._compiler = compiler
        self._root = root

        self._op: type[ast.boolop] = ast.And if root == 'and' else ast.Or

        self._ret: Result | None = None
        self._var: str | None = None  # A temporary variable for assigning results to.
        self._assignment: ast.Assign | None = None  # The current assignment to `_var`.
        self._stmts: list[ResultStatement] | None = None  # The current statement list.
        self._can_append = False  # Whether the current expression is the compiled `BoolOp`.

    def _put(self, node: Object | ast.AST, value: ast.expr) -> ast.Assign:
        """Save the result of the operation so far to `_var`."""

        if self._var is None:
            self._var = self._compiler.get_anon_var()

        name = asty.Name(node, id=self._var, ctx=ast.Store())
        check.not_none(self._ret).temp_variables.append(name)
        self._can_append = False

        self._assignment = asty.Assign(node, targets=[name], value=value)
        return self._assignment

    def _get(self, node: Object | ast.AST) -> ast.Name:
        """Get the value of `_var`, creating it if necessary."""

        if self._var is None:
            check.not_none(self._stmts).append(self._put(node, check.not_none(self._ret).force_expr))

        name = asty.Name(node, id=self._var, ctx=ast.Load())
        check.not_none(self._ret).temp_variables.append(name)
        return name

    def _enbool(self, expr: ast.expr, value_expr: ast.expr) -> ast.expr:
        """Add `value_expr` to the current `BoolOp` `expr`, or create a new one if `expr` isn't one."""

        if self._can_append:
            check.isinstance(expr, ast.BoolOp).values.append(value_expr)
            return expr

        self._can_append = True
        return asty.BoolOp(expr, op=self._op(), values=[expr, value_expr])

    def _add(self, value: Result) -> None:
        if self._ret is None:
            # This is the first operand. Don't actually introduce a `BoolOp` yet; the unary case doesn't need it.
            self._ret = value
            self._stmts = value.stmts
            self._can_append = False

        elif value.stmts:
            # Save the result of the statements to the temporary variable. Use an `if` statement to implement
            # short-circuiting from this point.
            node = value.stmts[0]
            cond: ast.expr = self._get(node)
            if self._root == 'or':
                cond = asty.UnaryOp(node, op=ast.Not(), operand=cond)

            branch = asty.If(node, test=cond, body=value.stmts, orelse=[])
            check.not_none(self._stmts).append(branch)
            self._stmts = branch.body
            self._stmts.append(self._put(node, value.force_expr))

        else:
            value_expr = value.force_expr
            if self._assignment is not None:
                self._assignment.value = self._enbool(self._assignment.value, value_expr)
            else:
                self._ret.expr = self._enbool(self._ret.force_expr, value_expr)

    def compile(self, expr: Expression, args: ta.Sequence[Object]) -> Result:
        # Each operand is compiled only once the previous ones have been added.
        for value in map(self._compiler.compile, args):
            self._add(value)

        ret = check.not_none(self._ret)
        if self._var is not None:
            ret.expr = self._get(expr)
        return ret


@pattern_macro(['and', 'or'], [many(FORM)], shadow=True)
def compile_logical_or_and_and_operator(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        args: list[Object],
) -> Result | ast.AST:
    if not args:
        return asty.Constant(expr[0], value=True if root == 'and' else None)

    return _BoolOpCompiler(compiler, root).compile(expr, args)


##


_COMPARISON_OPS: ta.Mapping[str, type[ast.cmpop]] = {
    mangle(k): v
    for k, v in {
        '=': ast.Eq,
        '!=': ast.NotEq,
        '<': ast.Lt,
        '<=': ast.LtE,
        '>': ast.Gt,
        '>=': ast.GtE,
        'is': ast.Is,
        'is-not': ast.IsNot,
        'in': ast.In,
        'not-in': ast.NotIn,
    }.items()
}


def _get_comparison_op(compiler: HyASTCompiler, sym: str) -> ast.cmpop:
    k = mangle(sym)
    if k not in _COMPARISON_OPS:
        compiler._syntax_error(Symbol(sym), 'Illegal comparison operator: ' + str(sym))
    return _COMPARISON_OPS[k]()


@pattern_macro(['=', 'is', '<', '<=', '>', '>='], [oneplus(FORM)], shadow=True)
@pattern_macro(['!=', 'is-not', 'in', 'not-in'], [times(2, math.inf, FORM)], shadow=True)
def compile_compare_op_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        args: list[Object],
) -> Result:
    if len(args) == 1:
        return compiler.compile(args[0]) + asty.Constant(expr, value=True)

    ops = [_get_comparison_op(compiler, root) for _ in args[1:]]
    exprs, ret, _ = compiler._compile_collect(args)
    return ret + asty.Compare(expr, left=exprs[0], ops=ops, comparators=exprs[1:])


@pattern_macro('chainc', [FORM, many(SYM + FORM)])
def compile_chained_comparison(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        arg1: Object,
        args: list[tuple[Symbol, Object]],
) -> Result:
    ret = compiler.compile(arg1)
    left = ret.force_expr

    ops = [_get_comparison_op(compiler, op) for op, _ in args]
    comparators, ret2, _ = compiler._compile_collect([x for _, x in args])

    return ret + ret2 + asty.Compare(expr, left=left, ops=ops, comparators=comparators)


##


# For each operator, its node type, and the aggregation operator used for augmented assignment with three or more
# arguments - `(+= x a b)` is `(+= x (+ a b))`, and `(-= x a b)` is `(-= x (+ a b))`.
_MATH_OPS: ta.Mapping[str, tuple[type[ast.operator], str | None]] = {
    '+': (ast.Add, '+'),
    '/': (ast.Div, '*'),
    '//': (ast.FloorDiv, '*'),
    '*': (ast.Mult, '*'),
    '-': (ast.Sub, '+'),
    '%': (ast.Mod, None),
    '**': (ast.Pow, '**'),
    '<<': (ast.LShift, '+'),
    '>>': (ast.RShift, '+'),
    '|': (ast.BitOr, '|'),
    '^': (ast.BitXor, None),
    '&': (ast.BitAnd, '&'),
    '@': (ast.MatMult, '@'),
}

_MATH_IDENTITIES: ta.Mapping[str, int] = {
    '+': 0,
    '|': 0,
    '*': 1,
}

_UNARY_MATH_OPS: ta.Mapping[str, type[ast.unaryop]] = {
    '+': ast.UAdd,
    '-': ast.USub,
}


@pattern_macro(['+', '*', '|'], [many(FORM)], shadow=True)
@pattern_macro(['-', '/', '&', '@'], [oneplus(FORM)], shadow=True)
@pattern_macro(['**', '//', '<<', '>>'], [times(2, math.inf, FORM)], shadow=True)
@pattern_macro(['%', '^'], [times(2, 2, FORM)], shadow=True)
def compile_maths_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        args: list[Object],
) -> Result | ast.AST:
    if len(args) == 0:
        return asty.Constant(expr, value=_MATH_IDENTITIES[root])

    if len(args) == 1:
        if root == '/':
            # Compute the reciprocal of the argument.
            args = [Integer(1).replace(expr), args[0]]
        elif root in _UNARY_MATH_OPS:
            ret = compiler.compile(args[0])
            return ret + asty.UnaryOp(expr, op=_UNARY_MATH_OPS[root](), operand=ret.force_expr)
        else:
            return compiler.compile(args[0])

    op = _MATH_OPS[root][0]
    right_associative = root == '**'

    ret = compiler.compile(args[-1 if right_associative else 0])
    for child in args[-2 if right_associative else 1::-1 if right_associative else 1]:
        left_expr = ret.force_expr
        ret += compiler.compile(child)
        right_expr = ret.force_expr
        if right_associative:
            left_expr, right_expr = right_expr, left_expr
        ret += asty.BinOp(expr, left=left_expr, op=op(), right=right_expr)

    return ret


_AUGASSIGN_OPS: ta.Mapping[str, tuple[type[ast.operator], str | None]] = {
    x + '=': v
    for x, v in _MATH_OPS.items()
}


@pattern_macro([x for x, (_, v) in _AUGASSIGN_OPS.items() if v is not None], [FORM, oneplus(FORM)])
@pattern_macro([x for x, (_, v) in _AUGASSIGN_OPS.items() if v is None], [FORM, times(1, 1, FORM)])
def compile_augassign_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        target: Object,
        values: list[Object],
) -> Result:
    op, aggregate_op = _AUGASSIGN_OPS[root]

    if len(values) > 1:
        return compiler.compile(mkexpr(root, [target], mkexpr(aggregate_op, rest=values)).replace(expr))

    store_target = compiler._storeize(target, compiler.compile(target))
    ret = compiler.compile(values[0])
    return ret + asty.AugAssign(expr, target=store_target, value=ret.force_expr, op=op())
