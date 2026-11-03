"""
Prints expressions with no optional whitespace and only the parentheses needed to preserve the tree. Every node is
printed in a context precedence: the node parenthesizes itself iff its own precedence is lower than what the context
demands. The precedence model (and most of the per-node contexts) follow CPython's `ast._Unparser`, which is the
reference for which parentheses are actually required.
"""
import ast
import contextlib
import functools
import typing as ta

from .literals import FStringField
from .literals import FStringLiteral
from .literals import FStringPart
from .literals import assemble_fstring
from .literals import render_constant
from .precedence import Precedence
from .writing import SourceWriter


##


class UnsupportedNodeError(Exception):
    pass


##


_BIN_OPS: ta.Mapping[type[ast.operator], tuple[str, Precedence]] = {
    ast.Add: ('+', Precedence.ARITH),
    ast.Sub: ('-', Precedence.ARITH),
    ast.Mult: ('*', Precedence.TERM),
    ast.MatMult: ('@', Precedence.TERM),
    ast.Div: ('/', Precedence.TERM),
    ast.Mod: ('%', Precedence.TERM),
    ast.FloorDiv: ('//', Precedence.TERM),
    ast.LShift: ('<<', Precedence.SHIFT),
    ast.RShift: ('>>', Precedence.SHIFT),
    ast.BitOr: ('|', Precedence.EXPR),
    ast.BitXor: ('^', Precedence.BXOR),
    ast.BitAnd: ('&', Precedence.BAND),
    ast.Pow: ('**', Precedence.POWER),
}

_UNARY_OPS: ta.Mapping[type[ast.unaryop], tuple[str, Precedence]] = {
    ast.Invert: ('~', Precedence.FACTOR),
    ast.Not: ('not', Precedence.NOT),
    ast.UAdd: ('+', Precedence.FACTOR),
    ast.USub: ('-', Precedence.FACTOR),
}

_BOOL_OPS: ta.Mapping[type[ast.boolop], tuple[str, Precedence]] = {
    ast.And: ('and', Precedence.AND),
    ast.Or: ('or', Precedence.OR),
}

_CMP_OPS: ta.Mapping[type[ast.cmpop], str] = {
    ast.Eq: '==',
    ast.NotEq: '!=',
    ast.Lt: '<',
    ast.LtE: '<=',
    ast.Gt: '>',
    ast.GtE: '>=',
    ast.Is: 'is',
    ast.IsNot: 'is not',
    ast.In: 'in',
    ast.NotIn: 'not in',
}


def bin_op_symbol(op: ast.operator) -> str:
    return _BIN_OPS[type(op)][0]


def has_starred(node: ast.expr) -> bool:
    return isinstance(node, ast.Tuple) and any(isinstance(e, ast.Starred) for e in node.elts)


def bare_tuple_precedence(node: ast.expr, *, allow_yield: bool = False) -> Precedence:
    """
    The precedence for a context that accepts an unparenthesized tuple but, on python 3.8, not an unparenthesized
    starred one - `for x in *a, b` and `x += *a, b` are 3.9. Expression statements and augmented assignments also
    accept a bare `yield`.
    """

    if has_starred(node):
        return Precedence.TEST
    return Precedence.YIELD if allow_yield else Precedence.TUPLE


##


class ExpressionPrinter:
    def __init__(self, writer: SourceWriter) -> None:
        super().__init__()

        self._writer = writer

    #

    def print_expr(self, node: ast.expr, prec: Precedence = Precedence.TEST) -> None:
        try:
            fn = self._DISPATCH[type(node)]
        except KeyError:
            raise UnsupportedNodeError(type(node).__name__) from None

        fn(self, node, prec)

    def _write(self, s: str) -> None:
        self._writer.write(s)

    @contextlib.contextmanager
    def _parens(self, cond: bool) -> ta.Iterator[None]:
        if cond:
            self._write('(')
        yield
        if cond:
            self._write(')')

    def _print_comma_separated(self, nodes: ta.Iterable[ast.expr], prec: Precedence = Precedence.TEST) -> None:
        for i, n in enumerate(nodes):
            if i:
                self._write(',')
            self.print_expr(n, prec)

    #

    def _print_name(self, node: ast.Name, prec: Precedence) -> None:
        self._write(node.id)

    def _print_constant(self, node: ast.Constant, prec: Precedence) -> None:
        self._write(render_constant(node.value, kind=node.kind))

    def _print_attribute(self, node: ast.Attribute, prec: Precedence) -> None:
        # `1.real` would tokenize as a float, and `....real` as two ellipses.
        v = node.value
        bare_literal = isinstance(v, ast.Constant) and (v.value is ... or type(v.value) is int)

        with self._parens(bare_literal):
            self.print_expr(v, Precedence.ATOM)
        self._write('.')
        self._write(node.attr)

    def _print_subscript(self, node: ast.Subscript, prec: Precedence) -> None:
        self.print_expr(node.value, Precedence.ATOM)
        self._write('[')

        sl = node.slice
        if isinstance(sl, ast.Tuple) and sl.elts and not has_starred(sl):
            self._print_comma_separated(sl.elts)
            if len(sl.elts) == 1:
                self._write(',')
        elif isinstance(sl, ast.Tuple) and any(isinstance(e, ast.Slice) for e in sl.elts):
            # A starred element forces parentheses, within which slices are not allowed - not expressible before 3.11.
            raise UnsupportedNodeError('subscript tuple mixing slices and starred elements')
        else:
            self.print_expr(sl, Precedence.TEST)

        self._write(']')

    def _print_slice(self, node: ast.Slice, prec: Precedence) -> None:
        if node.lower is not None:
            self.print_expr(node.lower)
        self._write(':')
        if node.upper is not None:
            self.print_expr(node.upper)
        if node.step is not None:
            self._write(':')
            self.print_expr(node.step)

    def _print_starred(self, node: ast.Starred, prec: Precedence) -> None:
        self._write('*')
        self.print_expr(node.value, Precedence.EXPR)

    def _print_named_expr(self, node: ast.NamedExpr, prec: Precedence) -> None:
        with self._parens(prec > Precedence.NAMED_EXPR):
            self.print_expr(node.target, Precedence.ATOM)
            self._write(':=')
            self.print_expr(node.value)

    #

    def _print_tuple(self, node: ast.Tuple, prec: Precedence) -> None:
        with self._parens(not node.elts or prec > Precedence.TUPLE):
            self._print_comma_separated(node.elts)
            if len(node.elts) == 1:
                self._write(',')

    def _print_list(self, node: ast.List, prec: Precedence) -> None:
        self._write('[')
        self._print_comma_separated(node.elts)
        self._write(']')

    def _print_set(self, node: ast.Set, prec: Precedence) -> None:
        self._write('{')
        self._print_comma_separated(node.elts)
        self._write('}')

    def _print_dict(self, node: ast.Dict, prec: Precedence) -> None:
        self._write('{')
        for i, (k, v) in enumerate(zip(node.keys, node.values)):
            if i:
                self._write(',')
            if k is None:
                self._write('**')
                self.print_expr(v, Precedence.EXPR)
            else:
                self.print_expr(k)
                self._write(':')
                self.print_expr(v)
        self._write('}')

    #

    def _print_comprehensions(self, gens: ta.Iterable[ast.comprehension]) -> None:
        for g in gens:
            if g.is_async:
                self._write('async')
            self._write('for')
            self.print_expr(g.target, Precedence.TUPLE)
            self._write('in')
            self.print_expr(g.iter, Precedence.TEST.next())
            for c in g.ifs:
                self._write('if')
                self.print_expr(c, Precedence.TEST.next())

    def _print_list_comp(self, node: ast.ListComp, prec: Precedence) -> None:
        self._write('[')
        self.print_expr(node.elt)
        self._print_comprehensions(node.generators)
        self._write(']')

    def _print_set_comp(self, node: ast.SetComp, prec: Precedence) -> None:
        self._write('{')
        self.print_expr(node.elt)
        self._print_comprehensions(node.generators)
        self._write('}')

    def _print_dict_comp(self, node: ast.DictComp, prec: Precedence) -> None:
        self._write('{')
        self.print_expr(node.key)
        self._write(':')
        self.print_expr(node.value)
        self._print_comprehensions(node.generators)
        self._write('}')

    def _print_generator_exp(self, node: ast.GeneratorExp, prec: Precedence, *, bare: bool = False) -> None:
        with self._parens(not bare):
            self.print_expr(node.elt)
            self._print_comprehensions(node.generators)

    #

    def print_keyword(self, node: ast.keyword) -> None:
        if node.arg is None:
            self._write('**')
            self.print_expr(node.value, Precedence.EXPR)
        else:
            self._write(node.arg)
            self._write('=')
            self.print_expr(node.value)

    def _print_call(self, node: ast.Call, prec: Precedence) -> None:
        self.print_expr(node.func, Precedence.ATOM)
        self._write('(')

        if len(node.args) == 1 and not node.keywords and isinstance(node.args[0], ast.GeneratorExp):
            # A sole generator argument needs no parentheses of its own.
            self._print_generator_exp(node.args[0], Precedence.TEST, bare=True)

        else:
            self._print_comma_separated(node.args)
            for i, k in enumerate(node.keywords):
                if i or node.args:
                    self._write(',')
                self.print_keyword(k)

        self._write(')')

    def _print_arg(self, node: ast.arg) -> None:
        self._write(node.arg)
        if node.annotation is not None:
            self._write(':')
            self.print_expr(node.annotation)

    def _print_arg_with_default(self, node: ast.arg, default: ast.expr | None) -> None:
        self._print_arg(node)
        if default is not None:
            self._write('=')
            self.print_expr(default)

    def _print_prefixed_arg(self, prefix: str, node: ast.arg) -> None:
        self._write(prefix)
        self._print_arg(node)

    def print_arguments(self, node: ast.arguments) -> None:
        parts: list[ta.Callable[[], None]] = []

        positional = [*node.posonlyargs, *node.args]
        defaults: list[ast.expr | None] = [None] * (len(positional) - len(node.defaults)) + list(node.defaults)
        for i, (a, d) in enumerate(zip(positional, defaults)):
            parts.append(functools.partial(self._print_arg_with_default, a, d))
            if i == len(node.posonlyargs) - 1:
                parts.append(functools.partial(self._write, '/'))

        if node.vararg is not None:
            parts.append(functools.partial(self._print_prefixed_arg, '*', node.vararg))
        elif node.kwonlyargs:
            parts.append(functools.partial(self._write, '*'))

        for a, d in zip(node.kwonlyargs, node.kw_defaults):
            parts.append(functools.partial(self._print_arg_with_default, a, d))

        if node.kwarg is not None:
            parts.append(functools.partial(self._print_prefixed_arg, '**', node.kwarg))

        for i, p in enumerate(parts):
            if i:
                self._write(',')
            p()

    def _print_lambda(self, node: ast.Lambda, prec: Precedence) -> None:
        with self._parens(prec > Precedence.TEST):
            self._write('lambda')
            self.print_arguments(node.args)
            self._write(':')
            self.print_expr(node.body)

    #

    def _print_bool_op(self, node: ast.BoolOp, prec: Precedence) -> None:
        op, op_prec = _BOOL_OPS[type(node.op)]
        with self._parens(prec > op_prec):
            for i, v in enumerate(node.values):
                if i:
                    self._write(op)
                self.print_expr(v, op_prec.next())

    def _print_bin_op(self, node: ast.BinOp, prec: Precedence) -> None:
        op, op_prec = _BIN_OPS[type(node.op)]
        with self._parens(prec > op_prec):
            if isinstance(node.op, ast.Pow):
                # Right-associative, and its right operand is a `factor`, so `2**-1` needs no parentheses.
                self.print_expr(node.left, op_prec.next())
                self._write(op)
                r = node.right
                if isinstance(r, ast.UnaryOp) and not isinstance(r.op, ast.Not):
                    self.print_expr(r, Precedence.FACTOR)
                else:
                    self.print_expr(r, op_prec)
            else:
                self.print_expr(node.left, op_prec)
                self._write(op)
                self.print_expr(node.right, op_prec.next())

    def _print_unary_op(self, node: ast.UnaryOp, prec: Precedence) -> None:
        op, op_prec = _UNARY_OPS[type(node.op)]
        with self._parens(prec > op_prec):
            self._write(op)
            self.print_expr(node.operand, op_prec)

    def _print_compare(self, node: ast.Compare, prec: Precedence) -> None:
        with self._parens(prec > Precedence.CMP):
            self.print_expr(node.left, Precedence.CMP.next())
            for op, c in zip(node.ops, node.comparators):
                self._write(_CMP_OPS[type(op)])
                self.print_expr(c, Precedence.CMP.next())

    def _print_if_exp(self, node: ast.IfExp, prec: Precedence) -> None:
        with self._parens(prec > Precedence.TEST):
            self.print_expr(node.body, Precedence.TEST.next())
            self._write('if')
            self.print_expr(node.test, Precedence.TEST.next())
            self._write('else')
            self.print_expr(node.orelse, Precedence.TEST)

    def _print_await(self, node: ast.Await, prec: Precedence) -> None:
        with self._parens(prec > Precedence.AWAIT):
            self._write('await')
            self.print_expr(node.value, Precedence.ATOM)

    def _print_yield(self, node: ast.Yield, prec: Precedence) -> None:
        with self._parens(prec > Precedence.YIELD):
            self._write('yield')
            if node.value is not None:
                self.print_expr(node.value, Precedence.TUPLE)

    def _print_yield_from(self, node: ast.YieldFrom, prec: Precedence) -> None:
        with self._parens(prec > Precedence.YIELD):
            self._write('yield from')
            self.print_expr(node.value)

    #

    def _fstring_parts(self, node: ast.JoinedStr) -> list[FStringPart]:
        parts: list[FStringPart] = []
        for v in node.values:
            match v:
                case ast.Constant(value=str() as s):
                    parts.append(FStringLiteral(s))
                case ast.FormattedValue():
                    parts.append(self._fstring_field(v))
                case _:
                    raise UnsupportedNodeError(type(v).__name__)
        return parts

    def _fstring_field(self, node: ast.FormattedValue) -> FStringField:
        w = SourceWriter()
        ExpressionPrinter(w).print_expr(node.value, Precedence.TEST.next())

        spec: list[FStringPart] | None = None
        if node.format_spec is not None:
            if not isinstance(node.format_spec, ast.JoinedStr):
                raise UnsupportedNodeError(type(node.format_spec).__name__)
            spec = self._fstring_parts(node.format_spec)

        return FStringField(w.getvalue(), node.conversion, spec)

    def _print_joined_str(self, node: ast.JoinedStr, prec: Precedence) -> None:
        self._write(assemble_fstring(self._fstring_parts(node)))

    #

    _DISPATCH: ta.ClassVar[
        ta.Mapping[  # noqa
            type[ast.expr],
            ta.Callable[[ExpressionPrinter, ta.Any, Precedence], None],
        ],
    ] = {
        ast.Name: _print_name,
        ast.Constant: _print_constant,
        ast.Attribute: _print_attribute,
        ast.Subscript: _print_subscript,
        ast.Slice: _print_slice,
        ast.Starred: _print_starred,
        ast.NamedExpr: _print_named_expr,
        ast.Tuple: _print_tuple,
        ast.List: _print_list,
        ast.Set: _print_set,
        ast.Dict: _print_dict,
        ast.ListComp: _print_list_comp,
        ast.SetComp: _print_set_comp,
        ast.DictComp: _print_dict_comp,
        ast.GeneratorExp: _print_generator_exp,
        ast.Call: _print_call,
        ast.Lambda: _print_lambda,
        ast.BoolOp: _print_bool_op,
        ast.BinOp: _print_bin_op,
        ast.UnaryOp: _print_unary_op,
        ast.Compare: _print_compare,
        ast.IfExp: _print_if_exp,
        ast.Await: _print_await,
        ast.Yield: _print_yield,
        ast.YieldFrom: _print_yield_from,
        ast.JoinedStr: _print_joined_str,
    }
