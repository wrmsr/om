# ruff: noqa: A002, S307
"""The Hy REPL: a `code.InteractiveConsole` which reads, compiles, and runs Hy."""
import ast
import builtins
import code
import codeop
import contextlib
import linecache
import platform
import pydoc
import sys
import time
import traceback
import types
import typing as ta

from omcore import check

from .compat import unparse
from .compiler import HyASTCompiler
from .compiler import hy_compile
from .completer import Completer
from .completer import completion
from .errors import HyLanguageError
from .errors import HyMacroExpansionError
from .errors import HyRequireError
from .errors import filtered_hy_exceptions
from .macros import enable_readers
from .macros import require
from .macros import require_reader
from .reader import mangle
from .reader import read_many
from .reader.exceptions import PrematureEndOfInput
from .reader.hyreader import HyReader
from .runtime import HyRuntime


# A `linecache.cache` entry: (size, mtime, lines, fullname).
CacheEntry: ta.TypeAlias = tuple[int, float, list[str], str]

# The code objects of an input: one executing it, and one then evaluating its resulting value.
CodePair: ta.TypeAlias = tuple[types.CodeType, types.CodeType]

AstCallback: ta.TypeAlias = ta.Callable[[ast.Module | ast.Interactive, ast.Expression | None], None]
ExcInfo: ta.TypeAlias = tuple[type[BaseException] | None, BaseException | None, types.TracebackType | None]
OutputFn: ta.TypeAlias = ta.Callable[[ta.Any], ta.Any]


##


def set_last_exc(exc_info: ExcInfo | None = None) -> ExcInfo:
    """
    Set `sys.last_exc` to the exception of `exc_info` (by default, the one being handled), making it easier for the
    user to call the debugger, and return `exc_info`.
    """

    t, v, tb = exc_info if exc_info is not None else sys.exc_info()
    setattr(sys, 'last_exc', v)  # typeshed doesn't permit setting it to None
    return t, v, tb


class HyQuitter:
    def __init__(self, name: str) -> None:
        super().__init__()

        self._name = name

    def __repr__(self) -> str:
        return f'Use ({self._name}) or Ctrl-D (i.e. EOF) to exit'

    __str__ = __repr__

    def __call__(self, code: object = None) -> ta.NoReturn:
        # As with Python's own `quit` and `exit`, closing stdin is best-effort.
        try:
            sys.stdin.close()
        except BaseException:  # noqa: BLE001, S110
            pass

        raise SystemExit(code)


class HyHelper:
    def __repr__(self) -> str:
        return 'Use (help) for interactive help, or (help object) for help about object.'

    def __call__(self, *args: ta.Any, **kwargs: ta.Any) -> None:
        return pydoc.help(*args, **kwargs)


@contextlib.contextmanager
def extend_linecache(cmdline_cache: ta.Mapping[str, CacheEntry]) -> ta.Iterator[None]:
    """
    Keep the entries of `cmdline_cache` in `linecache` for the duration, which `linecache.checkcache` would otherwise
    evict as not being of real files.
    """

    orig_checkcache = linecache.checkcache

    def checkcache(filename: str | None = None) -> None:
        orig_checkcache(filename)
        linecache.cache.update(cmdline_cache)

    linecache.checkcache = checkcache
    try:
        yield
    finally:
        linecache.checkcache = orig_checkcache


##


class HyCompile(codeop.Compile):
    """
    Compiles Hy source into a `CodePair`, through `codeop`'s single-code interface. Like
    `IPython.core.compilerop.CachingCompiler`, each source is kept in `linecache`, under a unique fake filename.
    """

    def __init__(
            self,
            module: types.ModuleType,
            locals: dict[str, ta.Any],
            *,
            hy_compiler: HyASTCompiler,
            ast_callback: AstCallback | None = None,
            cmdline_cache: dict[str, CacheEntry] | None = None,
    ) -> None:
        super().__init__()

        self._module = module
        self._locals = locals
        self._hy_compiler = hy_compiler
        self._ast_callback = ast_callback
        self._cmdline_cache: dict[str, CacheEntry] = cmdline_cache if cmdline_cache is not None else {}

        self._reader = HyReader()
        self._skip_next_shebang = False

        if hasattr(module, '_hy_reader_macros'):
            enable_readers(module, self._reader, module.__dict__['_hy_reader_macros'].keys())

    @property
    def skip_next_shebang(self) -> bool:
        """Whether to skip a shebang line at the start of the next source compiled."""

        return self._skip_next_shebang

    @skip_next_shebang.setter
    def skip_next_shebang(self, value: bool) -> None:
        self._skip_next_shebang = value

    def _cache_source(self, source: str, name: str) -> None:
        entry: CacheEntry = (
            len(source),
            time.time(),
            [line + '\n' for line in source.splitlines()],
            name,
        )

        linecache.cache[name] = entry
        self._cmdline_cache[name] = entry

    def _store_exc_info(self) -> None:
        t, v, tb = set_last_exc()

        # Skip our frame.
        self._locals['_hy_exc_info'] = (t, v, getattr(tb, 'tb_next', tb))

    def _compile(self, source: str, name: str) -> CodePair:
        # Our compiler doesn't correspond to a real, fixed source file, so we need to [re]set these.
        self._hy_compiler.filename = name
        self._hy_compiler.source = source

        hy_ast = read_many(
            source,
            filename=name,
            reader=self._reader,
            skip_shebang=self._skip_next_shebang,
        )
        self._skip_next_shebang = False

        exec_ast, eval_ast = hy_compile(
            hy_ast,
            self._module,
            root=ast.Module,
            get_expr=True,
            compiler=self._hy_compiler,
            filename=name,
            source=source,
        )

        if self._ast_callback is not None:
            self._ast_callback(exec_ast, eval_ast)

        compile_ast: ta.Callable[..., types.CodeType] = super().__call__
        return (
            compile_ast(exec_ast, name, 'exec'),
            compile_ast(eval_ast, name, 'eval'),
        )

    def __call__(  # type: ignore[override]
            self,
            source: str,
            filename: str = '<input>',
            symbol: str | None = None,
            flags: int = 0,
    ) -> CodePair:
        # `symbol` is required by `codeop.Compile`, but is ignored: the source is always compiled in 'exec' mode.

        name = f'{filename}-{len(self._cmdline_cache)}'
        self._cache_source(source, name)

        try:
            return self._compile(source, name)

        except (PrematureEndOfInput, SyntaxError):
            self._store_exc_info()
            raise

        except Exception:  # noqa: BLE001
            self._store_exc_info()

            # Hy will raise exceptions during compile-time that Python would raise during run-time (e.g. import errors
            # for `require`). In order to work gracefully with the Python world, we convert such Hy errors to code that
            # purposefully reraises those exceptions in the places where Python code expects them - with the traceback
            # captured above, without the compiler / REPL frames.
            return (
                super().__call__('raise _hy_exc_info[1].with_traceback(_hy_exc_info[2])', name, 'exec'),
                super().__call__('None', name, 'eval'),
            )


class HyCommandCompiler(codeop.CommandCompiler):
    compiler: HyCompile

    def __init__(
            self,
            compiler: HyCompile,
            *,
            allow_incomplete: bool = True,
    ) -> None:
        super().__init__()

        self.compiler = compiler
        self._allow_incomplete = allow_incomplete

    def __call__(  # type: ignore[override]
            self,
            source: str,
            filename: str = '<input>',
            symbol: str = 'single',
            flags: int = 0,
    ) -> CodePair | None:
        # Hy's compiler handles incomplete input itself (by raising `PrematureEndOfInput`), so none of `codeop`'s
        # heuristics are necessary.
        try:
            return self.compiler(source, filename, symbol)

        except PrematureEndOfInput:
            # Catch this here because it is also a `SyntaxError`, which `code.InteractiveConsole` would otherwise
            # handle before it reaches our `runsource`.
            if not self._allow_incomplete:
                raise
            return None


##


class REPL(code.InteractiveConsole):
    """
    A `code.InteractiveConsole` for Hy.

    A convenient way to use this class to interactively debug code is to insert the following in the code you want to
    debug:

        (.run (hy.REPL :locals {#** (globals) #** (locals)}))

    Or in Python, with Hy bound to `hy`:

        hy.REPL(locals={**globals(), **locals()}).run()

    Note that as with `code.interact`, changes to local variables inside the REPL are not propagated back to the
    original scope.
    """

    # It's exposed as `hy.REPL`.
    __module__ = __package__

    compile: HyCommandCompiler

    def __init__(
            self,
            spy: bool = False,
            spy_delimiter: str = '-' * 30,
            output_fn: OutputFn | str | None = None,
            locals: dict[str, ta.Any] | None = None,
            filename: str = '<stdin>',
            allow_incomplete: bool = True,
            *,
            runtime: HyRuntime | None = None,
            startup: str | None = None,
    ) -> None:
        """
        Code is run in `runtime` - a new isolated one by default. `startup`, if given, is the path of a Hy file to run
        first (see the `HYSTARTUP` environment variable of the `hy` command).

        `output_fn` converts values to the text printed for them - given as a callable, or as the (possibly dotted) name
        of one, and by default `hy.repr`. With `spy`, the Python translation of each input is printed too, followed by
        `spy_delimiter`.
        """

        # We let `InteractiveConsole` initialize `self.locals` when it's `None`.
        super().__init__(locals=locals, filename=filename)

        if runtime is None:
            runtime = HyRuntime()
        self._runtime = runtime

        # Use a proper module (registered with the runtime's module system) for this REPL, and consistently use its
        # namespace as `self.locals` from here on.
        module_name = self.locals.get('__name__', '__console__')
        if (module := runtime.modules.get_module(module_name)) is None:
            module = runtime.new_module(module_name)
            runtime.modules.add_module(module)
        self._module = module
        self._module.__dict__.update(self.locals)
        self.locals = self._module.__dict__

        self._ps1: object = '=> '
        self._ps2: object = '... '

        if startup:
            try:
                startup_module, startup_exports = self._exec_startup(startup)

                spy = spy or bool(startup_exports.get('repl_spy'))
                output_fn = output_fn or startup_exports.get('repl_output_fn')
                self._ps1 = startup_exports.get('repl_ps1', self._ps1)
                self._ps2 = startup_exports.get('repl_ps2', self._ps2)

                self.locals.update(startup_exports)

                require(startup_module, self._module, assignments='ALL', importer=runtime.import_module)
                require_reader(startup_module, self._module, assignments='ALL', importer=runtime.import_module)

            except Exception as e:  # noqa: BLE001
                print(e)

        self._hy_compiler = HyASTCompiler(self._module, filename=module_name, runtime=runtime)

        self._cmdline_cache: dict[str, CacheEntry] = {}
        self.compile = HyCommandCompiler(
            HyCompile(
                self._module,
                self.locals,
                hy_compiler=self._hy_compiler,
                ast_callback=self._ast_callback,
                cmdline_cache=self._cmdline_cache,
            ),
            allow_incomplete=allow_incomplete,
        )

        self._spy = spy
        self._spy_delimiter = spy_delimiter
        self._output_fn = self._resolve_output_fn(output_fn)

        self._last_value: ta.Any = None
        self._print_last_value = True

        # The pre-mangled symbols of the recent results: *1, *2, *3
        self._result_syms: ta.Sequence[str] = tuple(mangle(f'*{i + 1}') for i in range(3))
        self.locals.update(dict.fromkeys(self._result_syms))

        # Allow access to the running REPL instance.
        self.locals['_hy_repl'] = self

        # Compile an empty statement, showing the standard preamble (when spying).
        exec_ast = hy_compile(read_many(''), self._module, compiler=self._hy_compiler, preamble=True)
        self._ast_callback(exec_ast, None)

    def _exec_startup(self, startup: str) -> tuple[types.ModuleType, dict[str, ta.Any]]:
        """Run the startup file, returning its module and its exports (by its `__all__`, or else its public names)."""

        mod = self._runtime.new_module('__hystartup__', filename=startup)
        with open(startup, encoding='utf-8') as f:
            src = f.read()
        self._runtime.exec_module_source(mod, src, filename=startup)

        names = mod.__dict__.get(
            '__all__',
            [name for name in mod.__dict__ if not name.startswith('_')],
        )
        return mod, {name: mod.__dict__[name] for name in names}

    def _resolve_output_fn(self, output_fn: OutputFn | str | None) -> OutputFn:
        if output_fn is None:
            return self._runtime.hy.repr

        if callable(output_fn):
            return output_fn

        if '.' in output_fn:
            *module_parts, fn_name = [mangle(x) for x in output_fn.split('.')]
            return getattr(self._runtime.import_module('.'.join(module_parts)), fn_name)

        return getattr(builtins, mangle(output_fn))

    def _ast_callback(self, exec_ast: ast.Module | ast.Interactive, eval_ast: ast.Expression | None) -> None:
        if not self._spy:
            return

        try:
            # Mush the two AST chunks into a single module for conversion into Python.
            body = list(exec_ast.body)
            if eval_ast is not None:
                body.append(ast.Expr(eval_ast.body))

            print(unparse(ast.Module(body, type_ignores=[])))
            print(self._spy_delimiter)

        except Exception:  # noqa: BLE001
            self.write(f'Exception in AST callback:\n{traceback.format_exc()}\n')

    def _show_exception(self, *, use_hy_exc_info: bool = False) -> None:
        # With `use_hy_exc_info`, use the exception info stored by `HyCompile`, the traceback of which doesn't have the
        # REPL's frames.
        t, v, tb = set_last_exc(self.locals.get('_hy_exc_info') if use_hy_exc_info else None)
        sys.excepthook(check.not_none(t), check.not_none(v), tb)
        self.locals[mangle('*e')] = v

    def showsyntaxerror(self, filename: str | None = None, source: str | None = None) -> None:
        self._print_last_value = False
        self._show_exception(use_hy_exc_info=True)

    def showtraceback(self) -> None:
        self._show_exception()

    def runcode(self, code: types.CodeType | CodePair) -> None:
        if isinstance(code, types.CodeType):
            super().runcode(code)
            return

        exec_code, eval_code = code
        try:
            eval(exec_code, self.locals)
            self._last_value = eval(eval_code, self.locals)

            # Don't print `None` values.
            self._print_last_value = self._last_value is not None

        except SystemExit:
            raise

        except Exception:  # noqa: BLE001
            # Set this to avoid a print-out of the last value on errors.
            self._print_last_value = False
            self.showtraceback()

    def _shift_results(self) -> None:
        next_result = self._last_value
        for sym in self._result_syms:
            self.locals[sym], next_result = next_result, self.locals[sym]

    def runsource(self, source: str, filename: str = '<stdin>', symbol: str = 'exec') -> bool:
        try:
            incomplete = super().runsource(source, filename, symbol)

        except (HyMacroExpansionError, HyRequireError):
            # We need to handle these exceptions ourselves, because the base method only handles `OverflowError`,
            # `SyntaxError` and `ValueError`.
            self.showsyntaxerror(filename)
            return False

        except HyLanguageError:
            self.showtraceback()
            return False

        if incomplete:
            return True

        self._shift_results()

        if self._print_last_value:
            try:
                output = self._output_fn(self._last_value)
            except Exception:  # noqa: BLE001
                self.showtraceback()
                return False

            print(output)

        return False

    @contextlib.contextmanager
    def _sys_prompts(self) -> ta.Iterator[None]:
        missing = object()
        saved = {name: getattr(sys, name, missing) for name in ('ps1', 'ps2')}

        sys.ps1 = self._ps1
        sys.ps2 = self._ps2
        try:
            yield

        finally:
            for name, value in saved.items():
                if value is not missing:
                    setattr(sys, name, value)
                elif hasattr(sys, name):
                    delattr(sys, name)

    @contextlib.contextmanager
    def _shadowed_builtins(self) -> ta.Iterator[None]:
        # Rather than replacing these in `builtins` (which would be visible to everything in the process), they're
        # shadowed in the REPL's own namespace for the duration.
        shadows: dict[str, ta.Any] = dict(
            quit=HyQuitter('quit'),
            exit=HyQuitter('exit'),
            help=HyHelper(),
        )

        missing = object()
        saved = {name: self.locals.get(name, missing) for name in shadows}

        self.locals.update(shadows)
        try:
            yield

        finally:
            for name, value in saved.items():
                if value is missing:
                    self.locals.pop(name, None)
                else:
                    self.locals[name] = value

    def banner(self) -> str:
        return (
            f'Hy using {platform.python_implementation()}({platform.python_build()[0]}) '
            f'{platform.python_version()} on {platform.system()}'
        )

    def run(self) -> int:
        """Start running the REPL. Return 0 when done."""

        with (
            self._sys_prompts(),
            self._shadowed_builtins(),
            filtered_hy_exceptions(),
            extend_linecache(self._cmdline_cache),
            completion(Completer(self.locals)),
        ):
            self.interact(self.banner())

        return 0
