# ruff: noqa: SLF001
"""The `for` family: `for`, and the comprehensions `lfor`, `sfor`, `gfor`, and `dfor`."""
import ast
import contextlib
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ...compat import PY3_15
from ...compiler import HyASTCompiler
from ...funcparserlib.parser import finished
from ...funcparserlib.parser import many
from ...funcparserlib.parser import maybe
from ...macros import pattern_macro
from ...models import Expression
from ...models import Object
from ...models import Symbol
from ...patterns import FORM
from ...patterns import Tag
from ...patterns import brackets
from ...patterns import dolike
from ...patterns import notpexpr
from ...patterns import sym
from ...patterns import tag
from ...patterns import unpack
from ...reader import mangle
from ...results import Result
from ...results import ResultStatement
from ...results import asty
from ...scoping import ScopeGen
from ...scoping import is_inside_function_scope


##


_LOOPERS = many(
    tag('setv', sym(':setv') + FORM + FORM) |
    tag('if', sym(':if') + FORM) |
    tag('do', sym(':do') + FORM) |
    tag('afor', sym(':async') + FORM + FORM) |
    tag('for', FORM + FORM),
)


# The source of the value of each form when it has no loop clauses.
_EMPTY_COMPREHENSION_SOURCES: ta.Mapping[str, str] = {
    'for': 'None',
    'lfor': '[]',
    'dfor': '{}',
    'sfor': '{1}.__class__()',
    'gfor': '(_ for _ in [])',
}


@dc.dataclass(frozen=True)
class _CompiledLooper:
    """A compiled loop clause. `target` is the assignment target of `for`, `afor`, and `setv` clauses."""

    tag: str
    value: Result
    target: ast.expr | None = None


class _ComprehensionCompiler:
    """
    Compiles the `for` family. A comprehension is compiled to a real Python comprehension if it can be. Otherwise - as
    is `for` - it's compiled to nested loops, which for a comprehension are put in a generator function, called to
    produce its value.
    """

    def __init__(
            self,
            compiler: HyASTCompiler,
            expr: Expression,
            root: str,
    ) -> None:
        super().__init__()

        self._compiler = compiler
        self._expr = expr
        self._root = root

        self._is_for = root == 'for'
        self._is_dict = root == 'dfor'

        # For `for`, the body forms, and the compiled `else` branch, which is attached to the outermost loop.
        self._for_body: list[Object] = []
        self._for_orelse: Result | None = None

        # For comprehensions, the form of the final value, and its compiled value - or, for `dfor`, its compiled key and
        # value, unless it's a `#**` form unpacking a mapping (`_dict_unpack`), in which case `_key` is the mapping.
        self._final: ta.Any = None
        self._dict_unpack = False
        self._key: Result | None = None
        self._elt: Result | None = None
        self._ends_with_unpack = False

        self._any_async = False

    ##

    def _compile_loopers(self, scope: ScopeGen | None, loopers: ta.Sequence[Tag]) -> list[_CompiledLooper]:
        compiler = self._compiler

        compiled: list[_CompiledLooper] = []
        for looper in loopers:
            if looper.tag in ('if', 'do'):
                compiled.append(_CompiledLooper(looper.tag, compiler.compile(looper.value)))

            else:
                target, value = looper.value
                store_target = compiler._storeize(target, compiler.compile(target))
                value_ret = compiler.compile(value)
                if not self._is_for:
                    check.not_none(scope).iterator(store_target)
                compiled.append(_CompiledLooper(looper.tag, value_ret, store_target))

        return compiled

    def _compile_final(self, final: ta.Any) -> None:
        compiler = self._compiler

        self._final = final
        if self._is_dict:
            if self._dict_unpack:
                self._key = compiler.compile(final[1])
            else:
                self._key, self._elt = map(compiler.compile, final)
        else:
            self._elt = compiler.compile(final)

        self._ends_with_unpack = self._dict_unpack or (
            self._elt is not None and
            isinstance(self._elt.expr, ast.Starred)
        )

    def _can_be_real_comprehension(self, loopers: ta.Sequence[_CompiledLooper]) -> bool:
        return not (
            (self._elt is not None and self._elt.stmts) or
            (self._key is not None and self._key.stmts) or
            (not PY3_15 and self._ends_with_unpack) or
            any(looper.tag == 'do' or looper.value.stmts for looper in loopers)
        )

    ##

    def _build_real_comprehension(self, loopers: ta.Sequence[_CompiledLooper]) -> ast.AST:
        expr = self._expr

        generators: list[ast.comprehension] = []
        for looper in loopers:
            if looper.tag in ('for', 'afor'):
                generators.append(ast.comprehension(
                    target=check.not_none(looper.target),
                    iter=ta.cast(ast.expr, looper.value.expr),
                    ifs=[],
                    is_async=int(looper.tag == 'afor'),
                ))

            elif looper.tag == 'setv':
                generators.append(ast.comprehension(
                    target=check.not_none(looper.target),
                    iter=asty.Tuple(looper.value, elts=[looper.value.expr], ctx=ast.Load()),
                    ifs=[],
                    is_async=0,
                ))

            elif looper.tag == 'if':
                generators[-1].ifs.append(ta.cast(ast.expr, looper.value.expr))

            else:
                raise ValueError("can't happen")

        if self._is_dict:
            return asty.DictComp(
                expr,
                key=check.not_none(self._key).expr,
                value=self._elt.expr if self._elt is not None else None,
                generators=generators,
            )

        node = {
            'lfor': asty.ListComp,
            'sfor': asty.SetComp,
            'gfor': asty.GeneratorExp,
        }[self._root]
        return node(expr, elt=check.not_none(self._elt).expr, generators=generators)

    ##

    def _build_loop_body(self) -> Result:
        compiler = self._compiler
        expr = self._expr

        if self._is_for:
            if self._for_body:
                body = compiler._compile_branch(self._for_body)
                return body + body.expr_as_stmt()
            return Result(stmts=[asty.Pass(expr)])

        if self._ends_with_unpack:
            # Loop over the unpacked value, yielding each of its elements (or key-value pairs, for a mapping).
            self._ends_with_unpack = False

            if self._dict_unpack:
                key = check.not_none(self._key)
                to_loop = Result(expr=asty.Call(
                    key,
                    args=[],
                    keywords=[],
                    func=asty.Attribute(key, value=key.force_expr, attr='items', ctx=ast.Load()),
                ))
            else:
                to_loop = Result(expr=check.isinstance(check.not_none(self._elt).expr, ast.Starred).value)

            temp_var = compiler.get_anon_var()
            self._elt = compiler.compile(Symbol(temp_var).replace(self._final))
            return self._build_loops([_CompiledLooper(
                'for',
                to_loop,
                asty.Name(self._final, id=mangle(temp_var), ctx=ast.Store()),
            )])

        elt = check.not_none(self._elt)
        if self._is_dict and not self._dict_unpack:
            key = check.not_none(self._key)
            ret = key + elt
            val = asty.Tuple(key, ctx=ast.Load(), elts=[key.force_expr, elt.force_expr])
        else:
            ret = elt
            val = ret.force_expr

        return ret + asty.Expr(elt, value=asty.Yield(elt, value=val))

    def _build_loops(self, loopers: ta.Sequence[_CompiledLooper]) -> Result:
        """Build the nested loops of `loopers`, innermost of which is the loop body (or the `yield` of a value)."""

        if not loopers:
            return self._build_loop_body()

        looper, rest = loopers[0], loopers[1:]
        value = looper.value

        if looper.tag in ('for', 'afor'):
            orelse: list[ResultStatement] = []
            if self._for_orelse is not None:
                orelse, self._for_orelse = self._for_orelse.stmts, None

            self._any_async = self._any_async or looper.tag == 'afor'
            node = asty.AsyncFor if looper.tag == 'afor' else asty.For
            return value + node(
                value,
                target=looper.target,
                iter=value.force_expr,
                body=self._build_loops(rest).stmts,
                orelse=orelse,
            )

        elif looper.tag == 'setv':
            return value + asty.Assign(value, targets=[looper.target], value=value.force_expr) + self._build_loops(rest)

        elif looper.tag == 'if':
            return value + asty.If(value, test=value.force_expr, body=self._build_loops(rest).stmts, orelse=[])

        elif looper.tag == 'do':
            return value + value.expr_as_stmt() + self._build_loops(rest)

        else:
            raise ValueError("can't happen")

    def _build_exposed_assignments(self, scope: ScopeGen, names: list[str]) -> tuple[ast.stmt, ast.stmt]:
        """
        Build the statements exposing assignments within a comprehension function to its enclosing scope: a `global` or
        `nonlocal` declaration for the function, and a never-executed assignment for the enclosing scope, so that Python
        places the names there.
        """

        expr = self._expr

        unlocal_type = asty.Nonlocal if is_inside_function_scope(check.not_none(scope.parent)) else asty.Global
        declaration = unlocal_type(expr, names=names)

        if_body: list[ast.stmt] = []
        if scope.nonlocal_vars:
            if_body.append(asty.Nonlocal(expr, names=sorted(scope.nonlocal_vars)))

        assignments = asty.Tuple(
            expr,
            elts=[asty.Name(expr, id=var, ctx=ast.Store()) for var in names],
            ctx=ast.Store(),
        )
        if_body.append(asty.Assign(expr, targets=[assignments], value=asty.Constant(expr, value=None)))

        return declaration, asty.If(expr, test=asty.Constant(expr, value=False), body=if_body, orelse=[])

    def _build_function(self, scope: ScopeGen, loopers: ta.Sequence[_CompiledLooper]) -> Result:
        """
        Build the comprehension as a generator function of nested loops, and a call of it. Unless a generator is wanted,
        the call is wrapped in another comprehension to get the right type - rather than just using e.g. `list(...)`,
        which wouldn't work if `list` were rebound, nor for async generators.
        """

        compiler = self._compiler
        expr = self._expr

        fname = compiler.get_anon_var()

        stmts: list[ast.stmt] = []
        ret = Result()
        assignment_names = scope.finalize()
        if scope.exposing_assignments and assignment_names:
            declaration, fake_assignment = self._build_exposed_assignments(scope, assignment_names)
            stmts.append(declaration)
            ret += fake_assignment

        # This must be built before the function definition, as it determines `_any_async`.
        body = self._build_loops(loopers).stmts

        ret += (asty.AsyncFunctionDef if self._any_async else asty.FunctionDef)(
            expr,
            name=fname,
            args=ast.arguments(
                args=[],
                vararg=None,
                kwarg=None,
                posonlyargs=[],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=stmts + body,
            decorator_list=[],
            type_params=[],
        )

        delims = '[]' if self._root == 'lfor' else '{}'
        if self._is_dict:
            k, v = compiler.get_anon_var(), compiler.get_anon_var()
            elt, target = f'{k}: {v}', f'{k}, {v}'
        else:
            # Note that these names are taken even for `gfor`, which doesn't use them.
            elt = target = compiler.get_anon_var()

        if self._root == 'gfor':
            call_source = f'{fname}()'
        else:
            call_source = '{}{} {} for {} in {}(){}'.format(
                delims[0],
                elt,
                'async' if self._any_async else '',
                target,
                fname,
                delims[1],
            )

        return ret + Result(expr=asty.parse(expr, call_source).body[0].value)

    ##

    def _compile_in_scope(self, scope: ScopeGen | None, parts: ta.Any, final: ta.Any) -> Result | ast.AST:
        compiler = self._compiler

        loopers: ta.Any = parts[0] if self._is_for else parts

        if self._is_dict:
            self._dict_unpack = bool(final)
            if not (self._dict_unpack or (loopers and loopers[-1].tag == 'for')):
                compiler._syntax_error(
                    loopers[-1] if loopers else loopers,
                    '`dfor` must end with key and value forms, or `#** FORM`',
                )
            final = final or loopers.pop().value

        if not loopers:
            return Result(expr=asty.parse(self._expr, _EMPTY_COMPREHENSION_SOURCES[self._root]).body[0].value)

        compiled_loopers = self._compile_loopers(scope, loopers)

        if self._is_for:
            self._for_body, else_expr = final
            if else_expr is not None:
                orelse = compiler._compile_branch(else_expr)
                self._for_orelse = orelse + orelse.expr_as_stmt()

            return self._build_loops(compiled_loopers)

        self._compile_final(final)

        if self._can_be_real_comprehension(compiled_loopers):
            return self._build_real_comprehension(compiled_loopers)

        return self._build_function(check.not_none(scope), compiled_loopers)

    def compile(self, parts: ta.Any, final: ta.Any) -> Result | ast.AST:
        compiler = self._compiler

        scope_ctx = contextlib.nullcontext() if self._is_for else compiler.scope.create(ScopeGen)
        local_state_ctx = contextlib.nullcontext() if self._is_for else compiler.local_state()
        with local_state_ctx, scope_ctx as scope:
            return self._compile_in_scope(scope, parts, final)


@pattern_macro(['for'], [
    brackets(_LOOPERS, name='square-bracketed loop clauses'),
    many(notpexpr('else')) + maybe(dolike('else')),
])
@pattern_macro(['lfor', 'sfor', 'gfor'], [_LOOPERS, FORM])
# Here `finished` is a hack replacement for FORM + FORM: https://github.com/vlasovskikh/funcparserlib/issues/75
@pattern_macro(['dfor'], [_LOOPERS, finished | unpack('mapping')])
def compile_comprehension(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        parts: ta.Any,
        final: ta.Any,
) -> Result | ast.AST:
    return _ComprehensionCompiler(compiler, expr, root).compile(parts, final)
