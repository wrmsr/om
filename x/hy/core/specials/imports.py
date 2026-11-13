# ruff: noqa: SLF001
"""`import` and `require`."""
import importlib.util
import typing as ta

from ...compat import PY3_15
from ...compiler import HyASTCompiler
from ...compiler import mkexpr
from ...funcparserlib.parser import many
from ...funcparserlib.parser import maybe
from ...funcparserlib.parser import oneplus
from ...funcparserlib.parser import some
from ...macros import local_macro_name
from ...macros import pattern_macro
from ...macros import require
from ...macros import require_reader
from ...models import Dict
from ...models import Expression
from ...models import Keyword
from ...models import List
from ...models import Object
from ...models import String
from ...models import Symbol
from ...patterns import SYM
from ...patterns import brackets
from ...patterns import keepsym
from ...patterns import pexpr
from ...patterns import sym
from ...patterns import times
from ...reader import mangle
from ...results import Result
from ...results import asty
from .helpers import dotted


# Either `'EXPORTS'`, for all of a module's exports, or pairs of names and the names to bind them to.
_ImportAssignments: ta.TypeAlias = ta.Literal['EXPORTS'] | list[tuple[str, str]]


##


# A module name: a symbol, or a dotted name, which the reader reads as an expression - `foo.bar` as `(. foo bar)`, and
# `..foo.bar` as `(.. None foo bar)`.
_MODULE_NAME = SYM | pexpr(some(lambda x: isinstance(x, Symbol) and not str(x[0]).strip('.')), oneplus(SYM))

_IMPORTLIKE = (
    keepsym('*') |
    (keepsym(':as') + SYM) |
    brackets(many(SYM + maybe(sym(':as') + SYM)))
)


def _is_relative_module_name(module: Object) -> bool:
    return isinstance(module, Expression) and module[1][0] == Symbol('None')


def _module_name_str(module: Object) -> str:
    if isinstance(module, Expression):
        names = module[1]
        if names[0] == Symbol('None'):
            names = names[1:]
        return '.'.join(map(mangle, names))

    elif isinstance(module, Symbol) and not module.strip('.'):
        return str(module)

    else:
        return mangle(module)


def _assignment_shape(module: Object, rest: ta.Any) -> tuple[str, _ImportAssignments]:
    """Return the prefix with which, and the assignments by which, to import or require `module`."""

    prefix = ''
    assignments: _ImportAssignments = 'EXPORTS'

    if rest is None:
        # (import foo)
        prefix = _module_name_str(module)
    elif rest == Symbol('*'):
        # (import foo *)
        pass
    elif rest[0] == Keyword('as'):
        # (import foo :as bar)
        prefix = mangle(rest[1])
    else:
        # (import foo [bar baz :as MyBaz bing])
        assignments = [(k, v or k) for k, v in rest[0]]

    return prefix, assignments


##


def _resolve_require_module_name(compiler: HyASTCompiler, module: Object) -> str:
    module_name = _module_name_str(module)

    if _is_relative_module_name(module):
        # Prepend the leading dots.
        module_name = str(ta.cast(Expression, module)[0]) + module_name

    if module_name.startswith('.'):
        module_name = importlib.util.resolve_name(
            module_name,
            compiler.module.__package__ or compiler.module.__name__.rpartition('.')[0],
        )

    return module_name


def _compile_require_macros(
        compiler: HyASTCompiler,
        expr: Expression,
        module_name: str,
        *,
        assignments: _ImportAssignments,
        prefix: str,
) -> Result:
    ret = Result()

    if compiler.is_in_local_state():
        reqs = require(
            module_name,
            compiler.local_state_stack[-1]['macros'],
            assignments=assignments,
            prefix=prefix,
            compiler=compiler,
        )

        ret += compiler.compile(Expression([
            Symbol('setv'),
            List([Symbol(local_macro_name(m)) for m, _, _ in reqs]),
            Expression([
                dotted('hy.macros.require_vals'),
                String(module_name),
                Dict(),
                Keyword('assignments'),
                List([(String(m), String(m)) for _, m, _ in reqs]),
            ]),
        ]).replace(expr))
        ret += ret.expr_as_stmt()

    elif require(
            module_name,
            compiler.module,
            assignments=assignments,
            prefix=prefix,
            compiler=compiler,
    ):
        # Actually calling `require` is necessary for macro expansions occurring during compilation. The `require` we're
        # creating in AST is the same, but used at run-time (e.g. when modules are loaded via bytecode).
        ret += compiler.compile(Expression([
            dotted('hy.macros.require'),
            String(module_name),
            Symbol('None'),
            Keyword('target_module_name'),
            String(compiler.module.__name__),
            Keyword('assignments'),
            (
                String('EXPORTS')
                if assignments == 'EXPORTS'
                else List([List([String(k), String(v)]) for k, v in assignments])
            ),
            Keyword('prefix'),
            String(prefix),
        ]).replace(expr))
        ret += ret.expr_as_stmt()

    return ret


def _compile_require_readers(
        compiler: HyASTCompiler,
        expr: Expression,
        module_name: str,
        readers: ta.Any,
) -> Result:
    ret = Result()

    reader_assignments = 'ALL' if readers == Symbol('*') else [str(reader) for reader in readers[0]]

    if require_reader(
            module_name,
            compiler.module,
            reader_assignments,
            importer=compiler.runtime.import_module,
    ):
        ret += compiler.compile(mkexpr(
            'do',
            mkexpr(
                dotted('hy.macros.require-reader'),
                String(module_name),
                'None',
                [reader_assignments],
            ),
            mkexpr(
                'eval-when-compile',
                mkexpr(
                    dotted('hy.macros.enable-readers'),
                    'None',
                    mkexpr(dotted('hy.reader.HyReader.current-reader')),
                    [reader_assignments],
                ),
            ),
        ).replace(expr))
        ret += ret.expr_as_stmt()

    return ret


@pattern_macro(
    'require',
    [
        many(
            _MODULE_NAME +
            times(
                0,
                2,
                (maybe(sym(':macros')) + _IMPORTLIKE) |
                (keepsym(':readers') + (keepsym('*') | brackets(many(SYM)))),
            ),
        ),
    ],
)
def compile_require(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        entries: ta.Any,
) -> Result:
    ret = Result()

    for entry in entries:
        module, groups = entry

        reader_groups, import_groups = (
            [names for key, names in groups if (key == Keyword('readers')) == is_readers]
            for is_readers in (True, False)
        )
        if len(import_groups) > 1 or len(reader_groups) > 1:
            compiler._syntax_error(
                entry,
                f"redefinition of ':{'macros' if len(import_groups) > 1 else 'readers'}' brackets.",
            )

        rest = import_groups[0] if import_groups else None  # `None` means a prefixed macro import.
        readers = reader_groups and reader_groups[0]

        prefix, assignments = _assignment_shape(module, rest)
        module_name = _resolve_require_module_name(compiler, module)

        # Macros aren't all required with a prefix when only readers are being required, as by `(require a-module
        # :readers [!])`.
        if rest or not readers:
            ret += _compile_require_macros(compiler, expr, module_name, assignments=assignments, prefix=prefix)

        if readers:
            ret += _compile_require_readers(compiler, expr, module_name, readers)

    return ret


##


def _import_level(module: Object) -> int:
    if _is_relative_module_name(module):
        return len(ta.cast(Expression, module)[0])

    elif isinstance(module, Symbol) and not module.strip('.'):
        return len(module)

    else:
        return 0


@pattern_macro('import', [maybe(keepsym(':lazy')), many(_MODULE_NAME + maybe(_IMPORTLIKE))])
def compile_import(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        is_lazy: Keyword | None,
        entries: ta.Any,
) -> Result:
    if not PY3_15 and is_lazy:
        compiler._syntax_error(is_lazy, 'Lazy imports require Python 3.15 or later')

    lazy_kw: dict[str, ta.Any] = dict(is_lazy=True) if is_lazy else {}

    ret = Result()

    for entry in entries:
        module, _ = entry
        prefix, assignments = _assignment_shape(*entry)
        module_name = _module_name_str(module)

        if assignments == 'EXPORTS' and prefix == '':
            # (import foo *)
            ret += asty.ImportFrom(
                expr,
                names=[asty.alias(module, name='*', asname=None)],
                module=module_name if module_name and module_name.strip('.') else None,
                level=_import_level(module),
                **lazy_kw,
            )

        elif assignments == 'EXPORTS':
            compiler.scope.define(prefix)
            ret += asty.Import(
                expr,
                names=[asty.alias(module, name=module_name, asname=prefix if prefix != module_name else None)],
                **lazy_kw,
            )

        else:
            names = []
            for k, v in assignments:
                compiler.scope.define(mangle(v))
                names.append(asty.alias(module, name=mangle(k), asname=None if v == k else mangle(v)))

            ret += asty.ImportFrom(
                expr,
                names=names,
                module=module_name if module_name and module_name.strip('.') else None,
                level=_import_level(module),
                **lazy_kw,
            )

    return ret
