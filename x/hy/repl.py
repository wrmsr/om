# ruff: noqa: A002, S307
import ast
import builtins
import code
import codeop
import contextlib
import importlib
import linecache
import os
import platform
import pydoc
import sys
import time
import traceback
import types
import typing as ta

from omcore import check

from .. import hy
from .compat import PY3_12
from .compiler import HyASTCompiler
from .compiler import hy_compile
from .completer import Completer
from .completer import completion
from .errors import HyLanguageError
from .errors import HyMacroExpansionError
from .errors import HyRequireError
from .errors import filtered_hy_exceptions
from .importer import HyLoader
from .macros import enable_readers
from .macros import require
from .macros import require_reader
from .reader import mangle
from .reader import read_many
from .reader.exceptions import PrematureEndOfInput
from .reader.hy_reader import HyReader


CacheEntry: ta.TypeAlias = tuple[int, float, list[str], str]
CodePair: ta.TypeAlias = tuple[types.CodeType, types.CodeType]
AstCallback: ta.TypeAlias = ta.Callable[[ast.Module | ast.Interactive, ast.Expression | None], None]
ExcInfo: ta.TypeAlias = tuple[type[BaseException] | None, BaseException | None, types.TracebackType | None]


##


class HyQuitter:
    def __init__(self, name: str) -> None:
        super().__init__()

        self.name = name

    def __repr__(self) -> str:
        return f'Use ({self.name}) or Ctrl-D (i.e. EOF) to exit'

    __str__ = __repr__

    def __call__(self, code: object = None) -> ta.NoReturn:
        try:
            sys.stdin.close()
        except:  # noqa
            pass
        raise SystemExit(code)


class HyHelper:
    def __repr__(self) -> str:
        return 'Use (help) for interactive help, or (help object) for help about object.'

    def __call__(self, *args: ta.Any, **kwds: ta.Any) -> None:
        return pydoc.help(*args, **kwds)


@contextlib.contextmanager
def extend_linecache(add_cmdline_cache: ta.Mapping[str, CacheEntry]) -> ta.Iterator[None]:
    _linecache_checkcache = linecache.checkcache

    def _cmdline_checkcache(filename: str | None = None) -> None:
        _linecache_checkcache(filename)
        linecache.cache.update(add_cmdline_cache)

    linecache.checkcache = _cmdline_checkcache
    try:
        yield
    finally:
        linecache.checkcache = _linecache_checkcache


_codeop_maybe_compile = getattr(codeop, '_maybe_compile')


def _maybe_compile(
        compiler: codeop.Compile,
        source: str,
        filename: str,
        symbol: str,
        *args: ta.Any,
        **kwargs: ta.Any,
) -> CodePair | types.CodeType | None:
    # Python 3.14 passes `flags` either positionally or by keyword.
    if isinstance(compiler, HyCompile):
        return compiler(source, filename, symbol)
    return _codeop_maybe_compile(compiler, source, filename, symbol, *args, **kwargs)


setattr(codeop, '_maybe_compile', _maybe_compile)


class HyCompile(codeop.Compile):
    """This compiler uses `linecache` like `IPython.core.compilerop.CachingCompiler`."""

    def __init__(
            self,
            module: types.ModuleType,
            locals: dict[str, ta.Any],
            ast_callback: AstCallback | None = None,
            hy_compiler: HyASTCompiler | None = None,
            cmdline_cache: dict[str, CacheEntry] | None = None,
    ) -> None:
        self.module = module
        self.locals = locals
        self.ast_callback = ast_callback
        self.hy_compiler = hy_compiler or HyASTCompiler(module)
        self.reader = HyReader()
        self.skip_next_shebang = False

        super().__init__()

        if hasattr(self.module, '_hy_reader_macros'):
            enable_readers(
                self.module, self.reader, self.module.__dict__['_hy_reader_macros'].keys(),
            )

        self.cmdline_cache = cmdline_cache if cmdline_cache is not None else {}

    def _cache(self, source: str, name: str) -> None:
        entry = (
            len(source),
            time.time(),
            [line + '\n' for line in source.splitlines()],
            name,
        )

        linecache.cache[name] = entry
        self.cmdline_cache[name] = entry

    def _update_exc_info(self) -> None:
        t, v, tb = set_last_exc()
        # Skip our frame.
        self.locals['_hy_exc_info'] = (t, v, getattr(tb, 'tb_next', tb))

    # Hy produces separate executable and value code objects through codeop's single-code interface.
    def __call__(  # type: ignore[override]
            self,
            source: str,
            filename: str = '<input>',
            symbol: str | None = None,
            flags: int = 0,
    ) -> CodePair:
        symbol = 'exec'
        # This parameter is required by `codeop.Compile`, but we ignore it in favor of always using "exec".

        name = f'{filename}-{len(self.cmdline_cache)}'

        self._cache(source, name)

        try:
            # Our compiler doesn't correspond to a real, fixed source file, so we need to [re]set these.
            self.hy_compiler.filename = name
            self.hy_compiler.source = source
            hy_ast = read_many(
                source, filename=name, reader=self.reader,
                skip_shebang=self.skip_next_shebang,
            )
            self.skip_next_shebang = False
            exec_ast, eval_ast = hy_compile(
                hy_ast,
                self.module,
                root=ast.Module,
                get_expr=True,
                compiler=self.hy_compiler,
                filename=name,
                source=source,
                import_stdlib=False,
            )

            if self.ast_callback:
                self.ast_callback(exec_ast, eval_ast)

            compile_ast: ta.Callable[..., types.CodeType] = super().__call__
            exec_code = compile_ast(exec_ast, name, symbol)
            eval_code = compile_ast(eval_ast, name, 'eval')

        except Exception as e:
            self._update_exc_info()
            if isinstance(e, (PrematureEndOfInput, SyntaxError)):
                raise
            else:
                # Hy will raise exceptions during compile-time that Python would raise during run-time (e.g. import
                # errors for `require`).  In order to work gracefully with the Python world, we convert such Hy errors
                # to code that purposefully reraises those exceptions in the places where Python code expects them.
                # Capture a traceback without the compiler/REPL frames.
                exec_code = super().__call__(
                    'raise _hy_exc_info[1].with_traceback(_hy_exc_info[2])',
                    name,
                    symbol,
                )
                eval_code = super().__call__('None', name, 'eval')

        return exec_code, eval_code


class HyCommandCompiler(codeop.CommandCompiler):
    compiler: HyCompile

    def __init__(self, *args: ta.Any, allow_incomplete: bool = True, **kwargs: ta.Any) -> None:
        super().__init__()

        self.compiler = HyCompile(*args, **kwargs)
        self.allow_incomplete = allow_incomplete

    def __call__(self, *args: ta.Any, **kwargs: ta.Any) -> CodePair | None:  # type: ignore[override]
        try:
            return ta.cast('CodePair | None', super().__call__(*args, **kwargs))
        except PrematureEndOfInput:
            # We have to do this here, because `codeop._maybe_compile` won't take `None` for a return value (at least
            # not in Python 2.7) and this exception type is also a `SyntaxError`, so it will be caught by
            # `code.InteractiveConsole` base methods before it reaches our `runsource`.
            if not self.allow_incomplete:
                raise
            return None


class REPL(code.InteractiveConsole):
    """
    A subclass of :class:`code.InteractiveConsole` for Hy.

    A convenient way to use this class to interactively debug code is to insert the following in the code you want to
    debug::

        (.run (hy.REPL :locals {#** (globals) #** (locals)}))

    Or in Python, with Hy bound to ``hy``:

    .. code-block:: python

       hy.REPL(locals = {**globals(), **locals()}).run()

    Note that as with :func:`code.interact`, changes to local variables inside the REPL are not propagated back to the
    original scope.
    """

    __module__ = __package__

    compile: HyCommandCompiler

    def __init__(
            self,
            spy: bool = False,
            spy_delimiter: str = '-' * 30,
            output_fn: ta.Callable[[ta.Any], ta.Any] | str | None = None,
            locals: dict[str, ta.Any] | None = None,
            filename: str = '<stdin>',
            allow_incomplete: bool = True,
    ) -> None:
        # Create a proper module for this REPL so that we can obtain it easily (e.g. using `importlib.import_module`).
        # We let `InteractiveConsole` initialize `self.locals` when it's `None`.
        super().__init__(locals=locals, filename=filename)

        module_name = self.locals.get('__name__', '__console__')
        # Make sure our newly created module is properly introduced to `sys.modules`, and consistently use its namespace
        # as `self.locals` from here on.
        self.module = sys.modules.setdefault(module_name, types.ModuleType(module_name))
        self.module.__dict__.update(self.locals)
        self.locals = self.module.__dict__

        self.ps1 = '=> '
        self.ps2 = '... '

        startup = os.environ.get('HYSTARTUP')
        if startup:
            try:
                loader = HyLoader('__hystartup__', startup)
                spec = importlib.util.spec_from_loader(loader.name, loader)
                mod = importlib.util.module_from_spec(check.not_none(spec))
                sys.modules.setdefault(mod.__name__, mod)
                loader.exec_module(mod)
                imports = mod.__dict__.get(
                    '__all__',
                    [name for name in mod.__dict__ if not name.startswith('_')],
                )
                imports = {name: mod.__dict__[name] for name in imports}
                spy = spy or bool(imports.get('repl_spy'))
                output_fn = output_fn or imports.get('repl_output_fn')
                self.ps1 = imports.get('repl_ps1', self.ps1)
                self.ps2 = imports.get('repl_ps2', self.ps2)

                # Load imports and defs
                self.locals.update(imports)

                # load module macros
                require(mod, self.module, assignments='ALL')
                require_reader(mod, self.module, assignments='ALL')
            except Exception as e:  # noqa: BLE001
                print(e)

        self.hy_compiler = HyASTCompiler(self.module, module_name)

        self.cmdline_cache: dict[str, CacheEntry] = {}
        self.compile = HyCommandCompiler(
            self.module,
            self.locals,
            ast_callback=self.ast_callback,
            hy_compiler=self.hy_compiler,
            cmdline_cache=self.cmdline_cache,
            allow_incomplete=allow_incomplete,
        )

        self.spy = spy
        self.spy_delimiter = spy_delimiter
        self.last_value = None
        self.print_last_value = True

        if output_fn is None:
            self.output_fn = hy.repr
        elif callable(output_fn):
            self.output_fn = output_fn
        elif '.' in output_fn:
            parts = [mangle(x) for x in output_fn.split('.')]
            module, f = '.'.join(parts[:-1]), parts[-1]
            self.output_fn = getattr(importlib.import_module(module), f)
        else:
            self.output_fn = getattr(builtins, mangle(output_fn))

        # Pre-mangle symbols for repl recent results: *1, *2, *3
        self._repl_results_symbols = [mangle(f'*{i + 1}') for i in range(3)]
        self.locals.update({sym: None for sym in self._repl_results_symbols})

        # Allow access to the running REPL instance
        self.locals['_hy_repl'] = self

        # Compile an empty statement to load the standard prelude
        exec_ast = hy_compile(
            read_many(''), self.module, compiler=self.hy_compiler, import_stdlib=True,
        )
        if callable(self.ast_callback):
            self.ast_callback(exec_ast, None)

    def ast_callback(self, exec_ast: ast.Module | ast.Interactive, eval_ast: ast.Expression | None) -> None:
        if self.spy:
            try:
                # Mush the two AST chunks into a single module for conversion into Python.
                new_ast = ast.Module(
                    exec_ast.body
                    + ([] if eval_ast is None else [ast.Expr(eval_ast.body)]),
                    type_ignores=[],
                )
                print(ast.unparse(new_ast))
                print(self.spy_delimiter)
            except Exception:  # noqa: BLE001
                msg = f'Exception in AST callback:\n{traceback.format_exc()}\n'
                self.write(msg)

    def _error_wrap(self, exc_info_override: bool = False, *args: ta.Any, **kwargs: ta.Any) -> None:
        # When `exc_info_override` is true, use a traceback that doesn't have the REPL frames.
        t, v, tb = set_last_exc(
            self.locals.get('_hy_exc_info') if exc_info_override else None)
        sys.excepthook(check.not_none(t), check.not_none(v), tb)
        self.locals[mangle('*e')] = v

    def showsyntaxerror(self, filename: str | None = None, source: str | None = None) -> None:
        if filename is None:
            filename = self.filename
        self.print_last_value = False

        self._error_wrap(exc_info_override=True, filename=filename)

    def showtraceback(self) -> None:
        self._error_wrap()

    def runcode(self, code: types.CodeType | CodePair) -> None:
        if isinstance(code, types.CodeType):
            return super().runcode(code)
        try:
            eval(code[0], self.locals)
            self.last_value = eval(code[1], self.locals)
            # Don't print `None` values.
            self.print_last_value = self.last_value is not None
        except SystemExit:
            raise
        except Exception:  # noqa: BLE001
            # Set this to avoid a print-out of the last value on errors.
            self.print_last_value = False
            self.showtraceback()

    def runsource(self, source: str, filename: str = '<stdin>', symbol: str = 'exec') -> bool:
        try:
            res = super().runsource(source, filename, symbol)
        except (HyMacroExpansionError, HyRequireError):
            # We need to handle these exceptions ourselves, because the base method only handles `OverflowError`,
            # `SyntaxError` and `ValueError`.
            self.showsyntaxerror(filename)
            return False
        except (HyLanguageError):
            # Our compiler will also raise `TypeError`s
            self.showtraceback()
            return False

        # Shift exisitng REPL results
        if not res:
            next_result = self.last_value
            for sym in self._repl_results_symbols:
                self.locals[sym], next_result = next_result, self.locals[sym]

            # Print the value.
            if self.print_last_value:
                try:
                    output = self.output_fn(self.last_value)
                except Exception:  # noqa: BLE001
                    self.showtraceback()
                    return False

                print(output)

        return res

    def run(self) -> int:
        """Start running the REPL. Return 0 when done."""

        sentinel = object()
        saved_values: tuple[ta.Any, ...] = (
            getattr(sys, 'ps1', sentinel),
            getattr(sys, 'ps2', sentinel),
            builtins.quit,
            builtins.exit,
            builtins.help,
        )
        try:
            sys.ps1 = self.ps1
            sys.ps2 = self.ps2
            builtins.__dict__.update(quit=HyQuitter('quit'), exit=HyQuitter('exit'), help=HyHelper())

            namespace = self.locals
            with filtered_hy_exceptions(), extend_linecache(
                self.cmdline_cache,
            ), completion(Completer(namespace)):
                self.interact(self.banner())

        finally:
            sys.ps1, sys.ps2, builtins.quit, builtins.exit, builtins.help = saved_values
            for a in 'ps1', 'ps2':
                if getattr(sys, a) is sentinel:
                    delattr(sys, a)

        return 0

    def banner(self) -> str:
        return (
            f'Hy using {platform.python_implementation()}({platform.python_build()[0]}) '
            f'{platform.python_version()} on {platform.system()}'
        )


def set_last_exc(exc_info: ExcInfo | None = None) -> ExcInfo:
    """
    Setting `sys.last_exc`, or `sys.last_type` on earlier Pythons, makes it easier for the user to call the debugger.
    """

    t, v, tb = exc_info or sys.exc_info()
    if PY3_12:
        setattr(sys, 'last_exc', v)
    else:
        sys.last_type, sys.last_value, sys.last_traceback = t, v, tb
    return t, v, tb
