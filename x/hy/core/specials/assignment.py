# ruff: noqa: SLF001
"""Assignment, mutation, and annotation."""
import ast
import contextlib
import typing as ta

from omcore import check

from ...compiler import HyASTCompiler
from ...compiler import mkexpr
from ...funcparserlib.parser import many
from ...funcparserlib.parser import maybe
from ...funcparserlib.parser import oneplus
from ...macros import pattern_macro
from ...models import Expression
from ...models import Object
from ...models import Symbol
from ...patterns import FORM
from ...patterns import SYM
from ...patterns import Tag
from ...patterns import brackets
from ...patterns import sym
from ...patterns import tag
from ...patterns import times
from ...reader import mangle
from ...results import Result
from ...results import asty
from ...scoping import OuterVar
from ...scoping import ScopeLet
from .helpers import TYPE_PARAMS
from .helpers import digest_type_params
from .helpers import maybe_annotated


##


def _compile_assign(
        compiler: HyASTCompiler,
        target: Object | ta.Sequence[Object],
        value: Object | None,
        *,
        ann: Object | None = None,
        is_assignment_expr: bool = False,
        chained: bool = False,
        let_scope: ScopeLet | None = None,
) -> Result:
    """
    Compile the assignment of `value` to `target` (to each of the targets `target`, if `chained`), or, if `value` is
    `None`, the bare annotation of `target`.
    """

    # Assignment expressions have a value and no annotation.
    check.state(not is_assignment_expr or (value is not None and ann is None))

    annotate_only = value is None
    if annotate_only:
        result = Result()
    else:
        with let_scope if let_scope is not None else contextlib.nullcontext():
            result = compiler.compile(value)
        if let_scope is not None:
            target = check.isinstance(let_scope.add(check.isinstance(target, Object)), Object)

    if result.temp_variables and isinstance(target, Symbol):
        result.rename(compiler, compiler._nonconst(target))
        if not is_assignment_expr:
            # Throw away the expression context, so that `setv` returns `None`.
            result.expr = None
        return result

    st_targets = [
        compiler._storeize(t, compiler.compile(t))
        for t in (ta.cast('ta.Sequence[Object]', target) if chained else [check.isinstance(target, Object)])
    ]

    if ann is not None:
        ann_result = compiler.compile(ann)
        result = ann_result + result

    pos = target if hasattr(target, 'start_line') else result
    value_expr = result.force_expr if not annotate_only else None

    if is_assignment_expr:
        node = asty.NamedExpr(pos, value=value_expr, target=st_targets[0])
    elif ann is not None:
        node = asty.AnnAssign(
            pos,
            annotation=ann_result.force_expr,
            simple=int(isinstance(target, Symbol)),
            value=value_expr,
            target=st_targets[0],
        )
    else:
        node = asty.Assign(pos, value=value_expr, targets=st_targets)

    return result + node


@pattern_macro(
    'setv',
    [many(
        (
            tag('chained', sym(':chain') + brackets(oneplus(FORM))) |
            tag('maybe_annotated', maybe_annotated(FORM))
        ) + FORM,
    )],
)
@pattern_macro('setx', [times(1, 1, tag('setx', SYM) + FORM)])
def compile_def_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        decls: list[tuple[Tag, Object]],
) -> Result | ast.AST:
    if not decls:
        return asty.Constant(expr, value=None)

    result = Result()
    for (decl_tag, target), value in decls:
        ann = None
        if decl_tag == 'chained':
            [target] = target
        elif decl_tag == 'maybe_annotated':
            target, ann = target

        result += _compile_assign(
            compiler,
            target,
            value,
            ann=ann,
            is_assignment_expr=decl_tag == 'setx',
            chained=decl_tag == 'chained',
        )

    return result


@pattern_macro('let', [brackets(many(maybe_annotated(FORM) + FORM)), many(FORM)])
def compile_let(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        bindings: ta.Any,
        body: list[Object],
) -> Result:
    res = Result()
    scope = compiler.scope.create(ScopeLet)

    for (target, ann), value in bindings[0]:
        res += _compile_assign(compiler, target, value, ann=ann, let_scope=scope)

    with scope:
        return res + compiler.compile(mkexpr('do', *body).replace(expr))


@pattern_macro(['annotate'], [FORM, FORM])
def compile_basic_annotation(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        target: Object,
        ann: Object,
) -> Result:
    return _compile_assign(compiler, target, None, ann=ann)


@pattern_macro('deftype', [maybe(TYPE_PARAMS), SYM, FORM])
def compile_deftype(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        tp: ta.Any,
        name: Symbol,
        value: Object,
) -> ast.AST:
    return asty.TypeAlias(
        expr,
        name=asty.Name(name, id=mangle(name), ctx=ast.Store()),
        value=compiler.compile(value).force_expr,
        **digest_type_params(compiler, tp),
    )


@pattern_macro(['global', 'nonlocal'], [many(SYM)])
def compile_global_or_nonlocal(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        syms: list[Symbol],
) -> ast.AST:
    if not syms:
        return asty.Pass(expr)

    names = [mangle(s) for s in syms]
    ret: ast.Global | OuterVar
    if root == 'global':
        ret = asty.Global(expr, names=names)
    else:
        ret = OuterVar(expr, compiler.scope, names)

    try:
        compiler.scope.define_nonlocal(ret, root)
    except SyntaxError as e:
        compiler._syntax_error(expr, e.msg)

    return ret


@pattern_macro('del', [many(FORM)])
def compile_del_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        args: list[Object],
) -> Result | ast.AST:
    if not args:
        return asty.Pass(expr)

    del_targets = []
    ret = Result()
    for target in args:
        compiled_target = compiler.compile(target)
        ret += compiled_target
        del_targets.append(compiler._storeize(target, compiled_target, ast.Del))

    return ret + asty.Delete(expr, targets=del_targets)
