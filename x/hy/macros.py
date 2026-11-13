# ruff: noqa: SLF001
import ast
import importlib.machinery
import importlib.util
import inspect
import os
import re
import sys
import traceback
import types
import typing as ta

from omcore import check

from .errors import HyLanguageError
from .errors import HyMacroExpansionError
from .errors import HyRequireError
from .errors import HyTypeError
from .funcparserlib.parser import NoParseError
from .model_patterns import ModelParser
from .model_patterns import whole
from .models import Expression
from .models import Object
from .models import Symbol
from .models import as_model
from .models import is_unpack
from .models import replace_hy_obj
from .reader import HyReader
from .reader import mangle
from .reader.mangling import slashes2dots
from .results import Result


if ta.TYPE_CHECKING:
    from .compiler import HyASTCompiler


FunctionT = ta.TypeVar('FunctionT', bound=ta.Callable[..., ta.Any])
MacroNames: ta.TypeAlias = str | list[str] | tuple[tuple[int, ...], str | list[str]]
RequireAssignments: ta.TypeAlias = ta.Literal['ALL', 'EXPORTS'] | ta.Sequence[tuple[str, str]]
ModuleImporter: ta.TypeAlias = ta.Callable[[str], types.ModuleType]


##


def macro(name: str) -> ta.Callable[[FunctionT], FunctionT]:
    """Decorator to define a macro called `name`."""

    return lambda fn: install_macro(name, fn, fn)


def reader_macro(name: str, fn: ta.Callable[..., ta.Any]) -> None:
    fn = rename_function(fn, name)
    check.isinstance(fn, types.FunctionType).__globals__.setdefault('_hy_reader_macros', {})[name] = fn


def pattern_macro(
        names: MacroNames,
        pattern: ta.Sequence[ModelParser],
        shadow: bool | None = None,
) -> ta.Callable[[FunctionT], FunctionT]:
    parsed_pattern = whole(pattern)
    py_version_required = None
    if isinstance(names, tuple):
        py_version_required, names = names

    def dec(fn: FunctionT) -> FunctionT:
        def wrapper_maker(name: str) -> ta.Callable[..., ta.Any]:
            def wrapper(_hy_compiler: HyASTCompiler, *args: Object) -> ta.Any:
                if shadow and any(is_unpack('iterable', x) for x in args):
                    # Try a shadow function call with this name instead.
                    return Expression(
                        [Expression(map(Symbol, ['.', 'hy', 'pyops', name])), *args],
                    ).replace(check.not_none(_hy_compiler.this))

                expr = check.not_none(_hy_compiler.this)

                if py_version_required and sys.version_info < py_version_required:
                    _hy_compiler._syntax_error(
                        expr,
                        '`{}` requires Python {} or later'.format(
                            name, '.'.join(map(str, py_version_required)),
                        ),
                    )

                try:
                    parse_tree = parsed_pattern.parse(args)
                except NoParseError as e:
                    _hy_compiler._syntax_error(
                        expr[min(e.state.pos + 1, len(expr) - 1)],
                        "parse error for pattern macro '{}': {}".format(
                            name, e.msg.replace('end of input', 'end of macro call'),
                        ),
                    )
                return fn(_hy_compiler, expr, name, *parse_tree)

            return wrapper

        for name in [names] if isinstance(names, str) else names:
            install_macro(name, wrapper_maker(name), fn)
        return fn

    return dec


def install_macro(name: str, fn: FunctionT, module_of: ta.Callable[..., ta.Any]) -> FunctionT:
    name = mangle(name)
    fn = rename_function(fn, name)
    check.isinstance(module_of, types.FunctionType).__globals__.setdefault('_hy_macros', {})[name] = fn
    return fn


def _same_modules(source_module: types.ModuleType | str | None, target_module: types.ModuleType | str | None) -> bool:
    """
    Compare the filenames associated with the given modules names.

    This tries to not actually load the modules.
    """

    if not (source_module or target_module):
        return False

    if target_module is source_module:
        return True

    def get_filename(module: types.ModuleType | str | None) -> str | None:
        if module is None:
            return None
        if inspect.ismodule(module):
            return inspect.getfile(module)
        elif (
                (spec := importlib.util.find_spec(module)) and
                isinstance(spec.loader, importlib.machinery.SourceFileLoader)):
            return spec.loader.get_filename()
        return None

    try:
        source_filename = get_filename(source_module)
        target_filename = get_filename(target_module)
        return bool(source_filename and target_filename and os.path.samefile(source_filename, target_filename))
    except (ValueError, TypeError, ImportError, FileNotFoundError):
        return False


def derive_target_module(
        target_module: types.ModuleType | str | None,
        target_globals: ta.Mapping[str, ta.Any] | None,
        *,
        importer: ModuleImporter = importlib.import_module,
) -> tuple[types.ModuleType | str, dict[str, ta.Any]]:
    """
    Resolve a macro target into a (module or module name, namespace) pair. A `None` target means the module whose
    globals are `target_globals` - usually those of the calling frame.
    """

    if target_module is None:
        target_namespace = ta.cast('dict[str, ta.Any]', check.not_none(target_globals))
        target_module = target_namespace.get('__name__', 'builtins')
        # Why "builtins"? Because that's what Python produces with `exec("print(__name__)", globals = {})`.
    elif isinstance(target_module, str):
        target_module = importer(target_module)
        target_namespace = target_module.__dict__
    elif inspect.ismodule(target_module):
        target_namespace = target_module.__dict__
    else:
        raise HyTypeError(f'`target_module` is not a recognized type: {type(target_module)}')
    return target_module, target_namespace


def import_module_from_string(
        module_name: str,
        package_module: types.ModuleType | str,
        *,
        importer: ModuleImporter = importlib.import_module,
) -> types.ModuleType:
    if module_name.startswith('.'):
        package = getattr(package_module, '__package__', None)
        if not package:
            package = getattr(package_module, '__name__', package_module).rpartition('.')[0]
        module_name = importlib.util.resolve_name(module_name, package)
    try:
        return importer(module_name)
    except ImportError as e:
        raise HyRequireError(e.args[0]).with_traceback(None) from None


def require_reader(
        source_module: types.ModuleType | str,
        target_module: types.ModuleType | str | None,
        assignments: ta.Literal['ALL'] | ta.Iterable[str],
        *,
        target_globals: ta.Mapping[str, ta.Any] | None = None,
        importer: ModuleImporter = importlib.import_module,
) -> bool:
    if target_module is None and target_globals is None:
        target_globals = sys._getframe(1).f_globals
    target_module, target_namespace = derive_target_module(target_module, target_globals, importer=importer)

    if _same_modules(source_module, target_module):
        return False

    if not inspect.ismodule(source_module):
        source_module = import_module_from_string(source_module, target_module, importer=importer)

    source_macros = source_module.__dict__.setdefault('_hy_reader_macros', {})
    target_macros = target_namespace.setdefault('_hy_reader_macros', {})

    assignments = source_macros.keys() if assignments == 'ALL' else assignments

    for name in assignments:
        if name in source_macros:
            target_macros[name] = source_macros[name]
        else:
            raise HyRequireError(f'Could not require name {name} from {source_module}')

    return True


def enable_readers(
        module: types.ModuleType | str | None,
        reader: HyReader,
        names: ta.Literal['ALL'] | ta.Iterable[str],
        *,
        target_globals: ta.Mapping[str, ta.Any] | None = None,
        importer: ModuleImporter = importlib.import_module,
) -> None:
    if module is None and target_globals is None:
        target_globals = sys._getframe(1).f_globals
    _, namespace = derive_target_module(module, target_globals, importer=importer)
    names = namespace['_hy_reader_macros'].keys() if names == 'ALL' else names
    for name in names:
        if name not in namespace['_hy_reader_macros']:
            raise NameError(f'reader {name} is not defined')
        reader.reader_macros[name] = namespace['_hy_reader_macros'][name]


def require(
        source_module: types.ModuleType | str,
        target: types.ModuleType | str | dict[str, ta.Any] | None,
        assignments: RequireAssignments,
        prefix: str = '',
        target_module_name: str | None = None,
        compiler: HyASTCompiler | None = None,
        *,
        target_globals: ta.Mapping[str, ta.Any] | None = None,
        importer: ModuleImporter | None = None,
) -> list[tuple[str, str, ta.Callable[..., ta.Any]]]:
    """
    Load macros from a module. Return a list of (new name, source name, macro object) tuples, including only macros that
    were actually transferred.

    - `target` can be a a string (naming a module), a module object, a dictionary, or `None` (meaning the module whose
      globals are `target_globals`, by default those of the calling frame).
    - `assignments` can be "ALL", "EXPORTS", or a list of (macro name, alias) pairs.
    - `importer` is used to import source modules named by strings, defaulting to that of the `compiler`'s runtime if
      given, and otherwise to Python's import system.
    """

    if importer is None:
        importer = compiler.runtime.import_module if compiler is not None else importlib.import_module

    if isinstance(target, dict):
        target_module = None
    else:
        if target is None and target_globals is None:
            target_globals = sys._getframe(1).f_globals
        target_module, target_namespace = derive_target_module(target, target_globals, importer=importer)
        # Let's do a quick check to make sure the source module isn't actually the module being compiled (e.g. when
        # `runpy` executes a module's code in `__main__`). We use the module's underlying filename for this (when they
        # exist), since it's the most "fixed" attribute.
        if _same_modules(source_module, target_module):
            return []

    if not inspect.ismodule(source_module):
        source_module = import_module_from_string(
            source_module,
            target_module_name or target_module or '',
            importer=importer,
        )

    source_macros = source_module.__dict__.setdefault('_hy_macros', {})
    source_exports = getattr(
        source_module,
        '_hy_export_macros',
        [k for k in source_macros if not k.startswith('_')],
    )

    if not source_macros:
        if isinstance(assignments, str):
            return []
        out = []
        for name, alias in assignments:
            try:
                out.extend(require(
                    f'{source_module.__name__}.{mangle(name)}',
                    target_module or target,
                    'ALL',
                    prefix=alias,
                    target_globals=target_globals,
                    importer=importer,
                ))
            except HyRequireError:
                raise HyRequireError(
                    f"Cannot import name '{name}'"
                    f" from '{source_module.__name__}'"
                    f" ({source_module.__file__})",
                ) from None
        return out

    target_macros = target_namespace.setdefault('_hy_macros', {}) if target_module else check.isinstance(target, dict)

    if prefix:
        prefix += '.'
    out = []

    for name, alias in (
        assignments
        if not isinstance(assignments, str) else
        (
            (k, k)
            for k in source_macros
            if assignments == 'ALL' or k in source_exports
        )
    ):
        _name = mangle(name)
        if compiler:
            compiler.warn_on_core_shadow(prefix + alias)
        alias = mangle(prefix + alias)
        if _name in source_macros:
            target_macros[alias] = source_macros[_name]
            out.append((alias, _name, source_macros[_name]))
        else:
            raise HyRequireError(
                f'Could not require name {_name} from {source_module}',
            )

    return out


def require_vals(*args: ta.Any, **kwargs: ta.Any) -> list[ta.Callable[..., ta.Any]]:
    return [value for _, _, value in require(*args, **kwargs)]


def local_macro_name(original: str) -> str:
    return '_hy_local_macro__' + (
        # Mangle periods as well as the characters handled by `mangle`.
        mangle(original)
        .replace('D', 'DN')
        .replace('.', 'DD')
    )


class MacroExceptions:
    """
    wrap non ``HyLanguageError``'s in ``HyMacroExpansionError`` preserving stack trace

    used in lieu of ``@contextmanager`` to ensure stack trace contains only internal hy modules for consistent
    filtering.
    """

    def __init__(self, module: types.ModuleType, macro_tree: Expression, compiler: HyASTCompiler | None = None) -> None:
        super().__init__()

        self.module = module
        self.macro_tree = macro_tree
        self.compiler = compiler

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_traceback: types.TracebackType | None,
    ) -> bool:
        if exc_type is None:
            return True

        elif not issubclass(exc_type, HyLanguageError):
            if self.compiler:
                filename = self.compiler.filename
                source = self.compiler.source
            else:
                filename = None
                source = None

            exc_msg = '  '.join(
                traceback.format_exception_only(sys.exc_info()[0], sys.exc_info()[1]),
            )

            msg = f'expanding macro {self.macro_tree[0]!s}\n  '
            msg += exc_msg

            raise HyMacroExpansionError(msg, self.macro_tree, filename, source)

        else:
            return False


def macroexpand(
        tree: Object,
        module: types.ModuleType | str,
        compiler: HyASTCompiler | None = None,
        once: bool = False,
        result_ok: bool = True,
) -> Object | Result | ast.AST:
    """
    If `tree` isn't an `Expression` that might be a macro call, return it unchanged. Otherwise, try to expand it. Do
    this repeatedly unless `once` is true. Call `as_model` after each expansion. If the return value is a compiler
    `Result` object, and `result_ok` is false, return the previous value. Otherwise, return the final expansion.
    """

    if not inspect.ismodule(module):
        module = compiler.runtime.import_module(module) if compiler is not None else importlib.import_module(module)

    check.state(not compiler or compiler.module == module)

    core_macros: ta.Mapping[str, ta.Callable[..., ta.Any]] = (
        compiler.runtime.core_macros if compiler is not None else {}
    )

    while isinstance(tree, Expression) and tree:

        fn = tree[0]
        if (
            isinstance(fn, Expression) and
            fn and
            fn[0] == Symbol('.') and
            all(isinstance(x, Symbol) for x in fn)
        ):
            fn = '.'.join(map(mangle, fn[1:]))
        elif isinstance(fn, Symbol):
            fn = mangle(fn)
        else:
            break

        if fn.startswith('hy.R.'):
            # Special syntax for a one-shot `require`.
            req_from, _, fn = fn[len('hy.R.'):].partition('.')
            req_from = slashes2dots(req_from)
            try:
                m = (
                    compiler.runtime.import_module(req_from)
                    if compiler is not None
                    else importlib.import_module(req_from)
                ).__dict__['_hy_macros'][fn]
            except ImportError as e:
                raise HyRequireError(e.args[0]).with_traceback(None) from None
            except (AttributeError, KeyError):
                raise HyRequireError(f'Could not require name {fn} from {req_from}') from None

        else:
            # Choose the first namespace with the macro.
            m = (
                (
                    compiler and
                    next((
                        d[fn]
                        for d in [
                            compiler.extra_macros,
                            *(s['macros'] for s in reversed(compiler.local_state_stack)),
                        ]
                        if fn in d
                    ), None)
                ) or
                module.__dict__.get('_hy_macros', {}).get(fn) or
                core_macros.get(fn)
            )
            if not m:
                break

        with MacroExceptions(module, tree, compiler):
            if compiler:
                compiler.this = tree
            obj = m(  # noqa
                # If the macro's first parameter is named `_hy_compiler`, pass in the current compiler object in its
                # place.
                *([compiler] if m.__code__.co_varnames[:1] == ('_hy_compiler',) else []),
                *map(as_model, tree[1:]),
            )
            if isinstance(obj, (Result, ast.AST)):
                return obj if result_ok else tree

            tree = replace_hy_obj(obj, tree)

        if once:
            break

    return tree


def rename_function(f: FunctionT, new_name: str) -> FunctionT:
    """Create a copy of a function, but with a new name."""

    function = check.isinstance(f, types.FunctionType)
    renamed = types.FunctionType(
        function.__code__.replace(
            co_name=new_name,
            co_qualname=(
                re.sub(r'\.[^.+]\Z', '.' + new_name, function.__code__.co_qualname)
                if '.' in function.__code__.co_qualname
                else new_name),
        ),
        function.__globals__,
        str(new_name),
        function.__defaults__,
        function.__closure__,
    )
    renamed.__dict__.update(function.__dict__)
    renamed.__kwdefaults__ = function.__kwdefaults__.copy() if function.__kwdefaults__ is not None else None
    renamed.__annotate__ = function.__annotate__
    return ta.cast(FunctionT, renamed)
