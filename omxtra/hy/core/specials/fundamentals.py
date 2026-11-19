# ruff: noqa: SLF001
"""Fundamental special forms: `do`, compile-time evaluation, inline Python, `pragma`, and placeholders."""
import ast
import itertools
import textwrap
import typing as ta

from ...compiler import HyASTCompiler
from ...errors import HyEvalError
from ...errors import HyInternalError
from ...funcparserlib.parser import many
from ...macros import pattern_macro
from ...models import Expression
from ...models import Keyword
from ...models import Object
from ...models import String
from ...models import Symbol
from ...models import as_model
from ...patterns import FORM
from ...patterns import KEYWORD
from ...patterns import STR
from ...reader import HyReader
from ...results import Result
from ...results import asty


##


@pattern_macro('do', [many(FORM)])
def compile_do(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        body: list[Object],
) -> Result:
    return compiler._compile_branch(body)


@pattern_macro(['eval-and-compile', 'eval-when-compile', 'do-mac'], [many(FORM)])
def compile_eval_foo_compile(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        body: list[Object],
) -> Result:
    new_expr = Expression([Symbol('do').replace(expr[0])]).replace(expr)

    try:
        value = compiler.eval(new_expr + body)
    except HyInternalError:
        # Unexpected 'meta' compilation errors need to be treated like normal (unexpected) compilation errors at this
        # level (or the compilation level preceding this one).
        raise
    except Exception as e:
        # These could be expected Hy language errors (e.g. syntax errors) or regular Python runtime errors that do not
        # signify errors in the compilation *process* (although compilation did technically fail). We wrap these
        # exceptions and pass them through.
        raise HyEvalError(str(e), new_expr + body, compiler.filename, compiler.source) from e

    if root == 'do-mac':
        return compiler.compile(as_model(value).replace(expr))
    elif root == 'eval-and-compile':
        return compiler._compile_branch(body)
    else:
        return Result()


@pattern_macro(['py', 'pys'], [STR])
def compile_inline_python(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        code: String,
) -> Result | ast.AST:
    exec_mode = root == 'pys'

    try:
        o = asty.parse(
            expr,
            textwrap.dedent(code) if exec_mode else '(' + code + '\n)',
            compiler.filename,
            'exec' if exec_mode else 'eval',
        ).body
    except (SyntaxError, ValueError) as e:
        compiler._syntax_error(expr, f"Python parse error in '{root}': {e}")

    return Result(stmts=o) if exec_mode else o


##


# The version of upstream Hy this is a fork of, against which `(pragma :hy ...)` checks.
_LAST_HY_VERSION = '1.3.1'


def _check_pragma_hy_version(compiler: HyASTCompiler, kw: Keyword, value: Object) -> None:
    min_version = compiler.eval(value)
    if not isinstance(min_version, str):
        compiler._syntax_error(value, 'The version given to the pragma `:hy` must be a string')

    parts = min_version.split('.')
    if not all(p.isdigit() for p in parts):
        compiler._syntax_error(
            value,
            'The string given to the pragma `:hy` must be a dot-separated sequence of integers',
        )

    for have, need in itertools.zip_longest(map(int, _LAST_HY_VERSION.split('.')), map(int, parts)):
        if need is None:
            break
        if have is None or have < need:
            compiler._syntax_error(kw, f'Hy version {min_version} or later required')
        if have > need:
            break


@pattern_macro('pragma', [many(KEYWORD + FORM)])
def compile_pragma(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        kwargs: list[tuple[Keyword, Object]],
) -> Result:
    for kw, value in kwargs:
        if kw == Keyword('hy'):
            _check_pragma_hy_version(compiler, kw, value)

        elif kw == Keyword('warn-on-core-shadow'):
            compiler.local_state_stack[-1]['warn_on_core_shadow'] = bool(compiler.eval(value))

        elif kw == Keyword('bracketed-templates'):
            reader = HyReader.current_reader(create=False)
            if reader:
                reader.bracketed_templates = bool(compiler.eval(value))

        else:
            compiler._syntax_error(kw, f"Unknown pragma `{kw}`. Perhaps it's implemented by a newer version of Hy.")

    return Result()


##


@pattern_macro(
    ['unquote', 'unquote-splice', 'unpack-mapping', 'except', 'except*', 'finally', 'else'],
    [many(FORM)],
)
def compile_placeholder(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        body: list[Object],
) -> ta.NoReturn:
    raise ValueError(f'`{root}` is not allowed here')
