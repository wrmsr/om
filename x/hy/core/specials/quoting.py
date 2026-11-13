# ruff: noqa: SLF001
"""Quoting and quasiquoting."""
import ast
import math

from omcore import dataclasses as dc

from ...compiler import HyASTCompiler
from ...errors import HyTypeError
from ...macros import pattern_macro
from ...models import Expression
from ...models import FComponent
from ...models import FString
from ...models import Keyword
from ...models import List
from ...models import Object
from ...models import Sequence
from ...models import String
from ...models import Symbol
from ...models import is_unpack
from ...patterns import FORM
from ...reader import mangle
from ...results import Result
from .helpers import dotted


##


@dc.dataclass(frozen=True)
class _QuotedForm:
    """
    A rendered quoted form. `splice` marks the forms of `unquote-splice`s, which are to be concatenated into their
    enclosing sequence rather than nested within it.
    """

    form: Object
    splice: bool = False


def _quoted_model_kwargs(form: Object) -> list[Object]:
    """The keyword arguments, beyond its contents, with which to reconstruct the model `form`."""

    kwargs: list[Object] = []

    if isinstance(form, FString):
        if form.brackets is not None:
            kwargs.extend([Keyword('brackets'), String(form.brackets)])
        if form.is_tstring:
            kwargs.extend([Keyword('is_tstring'), Symbol('True')])

    elif isinstance(form, FComponent):
        if form.conversion is not None:
            kwargs.extend([Keyword('conversion'), String(form.conversion)])
        if form.expression is not None:
            kwargs.extend([Keyword('expression'), String(form.expression)])
        if form.is_tstring:
            kwargs.extend([Keyword('is_tstring'), Symbol('True')])

    elif isinstance(form, String):
        if form.brackets is not None:
            kwargs.extend([Keyword('brackets'), String(form.brackets)])

    return kwargs


def _render_quoted_form(compiler: HyASTCompiler, form: Object, level: float) -> _QuotedForm:
    """
    Render a quoted form as a new Hy expression which constructs it. `level` is the level of quasiquoting of the
    current form: forms may only be unquoted at level 0.
    """

    if isinstance(form, Expression) and form and isinstance(form[0], Symbol):
        op = mangle(form[0]).replace('_', '-')
        if op in ('unquote', 'unquote-splice', 'quasiquote'):
            if level == 0 and op != 'quasiquote':
                if len(form) != 2:
                    raise HyTypeError(
                        f'`{op}` needs 1 argument, got {len(form) - 1}',
                        form,
                        compiler.filename,
                        compiler.source,
                    )
                return _QuotedForm(form[1], splice=op == 'unquote-splice')

            level += 1 if op == 'quasiquote' else -1

    body: list[Object]

    if isinstance(form, Sequence):
        contents: list[Object] = []
        for x in form:
            q = _render_quoted_form(compiler, x, level)
            f_contents = q.form
            if q.splice:
                if is_unpack('iterable', f_contents):
                    compiler._syntax_error(f_contents, '`unpack-iterable` is not allowed here')
                f_contents = Expression([
                    Symbol('unpack-iterable'),
                    Expression([Symbol('or'), f_contents, List()]),
                ])
            contents.append(f_contents)

        body = [List(contents), *_quoted_model_kwargs(form)]

    elif isinstance(form, Symbol):
        body = [String(form), Keyword('from_parser'), Symbol('True')]

    elif isinstance(form, Keyword):
        body = [String(form.name), Keyword('from_parser'), Symbol('True')]

    else:
        body = [form, *_quoted_model_kwargs(form)]

    return _QuotedForm(Expression([dotted('hy.models.' + form.__class__.__name__), *body]).replace(form))


@pattern_macro(['quote', 'quasiquote'], [FORM])
def compile_quote(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        arg: Object,
) -> Result | ast.AST:
    # Only quasiquotes can unquote.
    return compiler.compile(_render_quoted_form(compiler, arg, level=math.inf if root == 'quote' else 0).form)
