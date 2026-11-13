"""
The Hy engine.

A :class:`HyRuntime` is a self-contained instance of Hy: it holds its own copies of the core macros and the core Hy
modules (such as ``hy.pyops``), its own ``hy`` namespace object - which is what the name ``hy`` refers to in all Hy code
it compiles - and, by default, its own private registry of Hy modules (see :mod:`.importing`). Any number of runtimes
may coexist in a process without affecting one another or any global interpreter state.

All Hy code compiled by a runtime additionally sees the names of the runtime's *prelude*, by default just ``ta`` bound
to :mod:`typing`.
"""
import ast
import collections.abc
import contextlib
import dataclasses as dc
import functools
import importlib
import importlib.resources
import os
import sys
import threading
import types
import typing as ta
import weakref

from omcore import check
from omcore import lang

from . import macros as macros_
from . import models
from .compiler import hy_compile
from .compiler import hy_eval
from .core import result_macros
from .importing import HyModules
from .importing import HyModulesFactory
from .importing import IsolatedHyModules
from .models import Lazy
from .models import Object
from .models import as_model
from .reader import read
from .reader import read_many
from .reader.exceptions import PrematureEndOfInput
from .reader.hy_reader import HyReader
from .reader.mangling import mangle
from .reader.mangling import slashes2dots
from .reader.mangling import unmangle
from .reader.reader import Reader


if ta.TYPE_CHECKING:
    from . import repl as repl_
else:
    repl_ = lang.proxy_import('.repl', __package__)


##


_HY_PACKAGE = __package__


@dc.dataclass(frozen=True)
class HyPreludeImport:
    """A module bound to a name in all code compiled by a runtime, as by ``import <module> as <name>``."""

    name: str
    module: str

    def __post_init__(self) -> None:
        check.arg(self.name.isidentifier(), self.name)
        check.non_empty_str(self.module)


DEFAULT_HY_PRELUDE: ta.Sequence[HyPreludeImport] = (
    HyPreludeImport('ta', 'typing'),
)


##


class HyCoreCodeCache:
    """
    A cache of the compiled code of the core Hy modules. Core modules are compiled from source the first time a runtime
    needs them, which takes a moment - but the resulting code objects are immutable and independent of the runtime which
    compiled them, so they may be shared by any number of runtimes, each executing them into its own module objects.
    """

    def __init__(self) -> None:
        super().__init__()

        self._lock = threading.Lock()
        self._codes: dict[str, types.CodeType] = {}

    def get(self, name: str) -> types.CodeType | None:
        return self._codes.get(name)

    def put(self, name: str, code: types.CodeType) -> types.CodeType:
        with self._lock:
            return self._codes.setdefault(name, code)


# The process-wide default, shared by runtimes not given their own. This holds nothing but deterministic, immutable
# compiler output.
_DEFAULT_HY_CORE_CODE_CACHE = HyCoreCodeCache()


# Core Hy modules, by name relative to the package. `core.macros` provides the core macros written in Hy, the others are
# reached through the `hy` namespace.
_CORE_HY_MODULES: ta.AbstractSet[str] = frozenset([
    'core.macros',
    'core.util',
    'core.hy_repr',
    'pyops',
])


##


class _HyNamespaceImporter:
    """
    ``hy.I`` provides syntactic sugar for imports. It allows syntax like ``(hy.I.math.sqrt 2)`` to mean ``(import math)
    (math.sqrt 2)``, except without bringing ``math`` or ``math.sqrt`` into scope. This is useful in macros to avoid
    namespace pollution. To refer to a module with dots in its name, use slashes instead: ``hy.I.os/path.basename`` gets
    the function ``basename`` from the module ``os.path``.

    You can also call ``hy.I`` like a function, as in ``(hy.I "math")``, which is useful when the module name isn't
    known until run-time. This avoids (1) mangling due to attribute lookup, and (2) the translation of ``/`` to ``.`` in
    the module name.

    Modules are imported as they would be by Hy code running in the runtime to which this ``hy`` belongs.
    """

    def __init__(self, runtime: HyRuntime) -> None:
        super().__init__()

        self._runtime = runtime

    def __call__(self, module_name: str) -> types.ModuleType:
        return self._runtime.import_module(module_name)

    def __getattr__(self, s: str) -> types.ModuleType:
        return self(slashes2dots(s))


class _HyNamespaceMacros:
    """
    ``hy.macros``: the :mod:`.macros` module, but with those of its functions which import modules bound to the runtime
    to which this ``hy`` belongs. Compiled code calls these at run-time to (re-)establish macros.
    """

    def __init__(self, runtime: HyRuntime) -> None:
        super().__init__()

        self._runtime = runtime

    def __getattr__(self, name: str) -> ta.Any:
        return getattr(macros_, name)

    def require(
            self,
            source_module: types.ModuleType | str,
            target: types.ModuleType | str | dict[str, ta.Any] | None,
            assignments: macros_.RequireAssignments,
            prefix: str = '',
            target_module_name: str | None = None,
            compiler: ta.Any = None,
    ) -> list[tuple[str, str, ta.Callable[..., ta.Any]]]:
        return macros_.require(
            source_module,
            target,
            assignments,
            prefix,
            target_module_name,
            compiler,
            target_globals=sys._getframe(1).f_globals if target is None else None,  # noqa: SLF001
            importer=self._runtime.import_module,
        )

    def require_vals(self, *args: ta.Any, **kwargs: ta.Any) -> list[ta.Callable[..., ta.Any]]:
        return macros_.require_vals(*args, importer=self._runtime.import_module, **kwargs)

    def require_reader(
            self,
            source_module: types.ModuleType | str,
            target_module: types.ModuleType | str | None,
            assignments: ta.Literal['ALL'] | ta.Iterable[str],
    ) -> bool:
        return macros_.require_reader(
            source_module,
            target_module,
            assignments,
            target_globals=sys._getframe(1).f_globals if target_module is None else None,  # noqa: SLF001
            importer=self._runtime.import_module,
        )

    def enable_readers(
            self,
            module: types.ModuleType | str | None,
            reader: HyReader,
            names: ta.Literal['ALL'] | ta.Iterable[str],
    ) -> None:
        macros_.enable_readers(
            module,
            reader,
            names,
            target_globals=sys._getframe(1).f_globals if module is None else None,  # noqa: SLF001
            importer=self._runtime.import_module,
        )


class HyNamespace(types.ModuleType):
    """
    The ``hy`` visible to Hy code compiled by a particular runtime: a view of this package, but with stateful parts of
    the API (such as ``hy.eval``, ``hy.repr-register``, ``hy.gensym``, ``hy.pyops``, and ``hy.I``) bound to that
    runtime. It shares the package's name, but is distinct from (and not registered as) any real module.
    """

    __package__: str

    def __init__(self, runtime: HyRuntime) -> None:
        super().__init__(_HY_PACKAGE)

        self.__dict__.update(
            __package__=_HY_PACKAGE,

            runtime=runtime,

            eval=runtime._eval_from_hy,  # noqa: SLF001
            I=_HyNamespaceImporter(runtime),
            macros=_HyNamespaceMacros(runtime),

            models=models,
            as_model=as_model,
            read=read,
            read_many=read_many,
            mangle=mangle,
            unmangle=unmangle,
            Reader=Reader,
            HyReader=HyReader,
            PrematureEndOfInput=PrematureEndOfInput,
        )

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.__name__!r} of {self.__dict__["runtime"]!r}>'

    def _resolve(self, name: str) -> ta.Any:
        runtime: HyRuntime = self.__dict__['runtime']

        match name:
            case '_hy_macros':
                return runtime.core_macros
            case '_hy_reader_macros':
                return runtime.core_reader_macros

            case 'pyops':
                return runtime.load_core_module(f'{_HY_PACKAGE}.pyops')

            case 'repr' | 'repr_register':
                return getattr(
                    runtime.load_core_module(f'{_HY_PACKAGE}.core.hy_repr'),
                    f'hy_{name}',
                )

            case 'gensym' | 'macroexpand' | 'macroexpand_1':
                return getattr(runtime.load_core_module(f'{_HY_PACKAGE}.core.util'), name)

            case 'REPL':
                return functools.partial(repl_.REPL, runtime=runtime)

        # Otherwise, any (Python) submodule of the package.
        if name.startswith('_'):
            raise AttributeError(name)
        sub_name = f'{_HY_PACKAGE}.{name}'
        try:
            return importlib.import_module(sub_name)
        except ModuleNotFoundError as e:
            if e.name != sub_name:
                raise
        raise AttributeError(name)

    def __getattr__(self, name: str) -> ta.Any:
        value = self._resolve(name)
        self.__dict__[name] = value
        return value


##


class HyRuntime:
    """
    An instance of the Hy engine. See the module docstring.

    ``modules`` constructs the module system the runtime will use, defaulting to an :class:`IsolatedHyModules` with no
    finders (meaning only the core Hy modules, and regular Python modules, are importable by Hy code). Pass, for
    example, ``functools.partial(IsolatedHyModules, finders=[DirectoryHyModuleFinder('scripts')])`` to make Hy modules
    in a directory importable.

    ``core_code_cache`` may be given to avoid sharing the process-wide cache of compiled core module code.
    """

    def __init__(
            self,
            *,
            modules: HyModulesFactory | None = None,
            prelude: ta.Sequence[HyPreludeImport] = DEFAULT_HY_PRELUDE,
            core_code_cache: HyCoreCodeCache | None = None,
    ) -> None:
        super().__init__()

        self._prelude = tuple(prelude)
        self._core_code_cache = core_code_cache if core_code_cache is not None else _DEFAULT_HY_CORE_CODE_CACHE

        self._prelude_values: dict[str, ta.Any] | None = None
        self._prepared_modules: weakref.WeakValueDictionary[int, types.ModuleType] = weakref.WeakValueDictionary()

        self._core_lock = threading.RLock()
        self._core_modules: dict[str, types.ModuleType] = {}
        self._core_macros_state: ta.Literal['unloaded', 'loading', 'loaded'] = 'unloaded'

        # The core macros implemented in Python are always available. Those implemented in Hy are added once loaded.
        self._core_macros: dict[str, ta.Callable[..., ta.Any]] = dict(getattr(result_macros, '_hy_macros'))
        self._core_reader_macros: dict[str, ta.Callable[..., ta.Any]] = dict(
            getattr(result_macros, '_hy_reader_macros', {}),
        )

        self._hy = HyNamespace(self)

        self._modules = (modules if modules is not None else IsolatedHyModules)(self)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} at {id(self):#x}>'

    @property
    def hy(self) -> HyNamespace:
        """The ``hy`` namespace object seen by Hy code compiled by this runtime."""

        return self._hy

    @property
    def modules(self) -> HyModules:
        return self._modules

    @property
    def prelude(self) -> ta.Sequence[HyPreludeImport]:
        return self._prelude

    ##
    # Core macros and modules

    def _ensure_core_macros(self) -> None:
        if self._core_macros_state == 'loaded':
            return

        with self._core_lock:
            # While the core macros module is itself being compiled, only the macros implemented in Python are
            # available.
            if self._core_macros_state != 'unloaded':
                return

            self._core_macros_state = 'loading'
            try:
                module = check.not_none(self.load_core_module(f'{_HY_PACKAGE}.core.macros'))
            except BaseException:
                self._core_macros_state = 'unloaded'
                raise

            self._core_macros.update(module.__dict__['_hy_macros'])
            self._core_reader_macros.update(module.__dict__['_hy_reader_macros'])
            self._core_macros_state = 'loaded'

    @property
    def core_macros(self) -> dict[str, ta.Callable[..., ta.Any]]:
        """
        The macros available to all code compiled by this runtime, by mangled name - visible to Hy code as
        ``hy._hy_macros``. This is owned by the runtime, and may be mutated.
        """

        self._ensure_core_macros()
        return self._core_macros

    @property
    def core_reader_macros(self) -> dict[str, ta.Callable[..., ta.Any]]:
        self._ensure_core_macros()
        return self._core_reader_macros

    def get_core_module(self, name: str) -> types.ModuleType | None:
        """Return the given core Hy module by absolute name if it's been loaded, without loading it."""

        return self._core_modules.get(name)

    def _compile_core_module(self, name: str) -> types.CodeType:
        if (code := self._core_code_cache.get(name)) is not None:
            return code

        package, _, leaf = name.rpartition('.')
        file = importlib.resources.files(package).joinpath(leaf + '.hy')
        source = file.read_text(encoding='utf-8')
        filename = os.fspath(file) if isinstance(file, os.PathLike) else f'<hy:{name}>'

        # Compile-time evaluation happens in a scratch module - the module the code is executed in is always fresh.
        scratch = self.new_module(name, filename=filename)
        tree = hy_compile(
            read_many(source, filename=filename, skip_shebang=True),
            scratch,
            filename=filename,
            source=source,
            runtime=self,
        )
        code = compile(tree, filename, 'exec', dont_inherit=True)

        return self._core_code_cache.put(name, code)

    def load_core_module(self, name: str) -> types.ModuleType | None:
        """
        Return the given core Hy module by absolute name, loading it into this runtime if necessary, or `None` if it's
        not the name of a core Hy module.
        """

        if (m := self._core_modules.get(name)) is not None:
            return m

        if not name.startswith(_HY_PACKAGE + '.') or name[len(_HY_PACKAGE) + 1:] not in _CORE_HY_MODULES:
            return None

        with self._core_lock:
            if (m := self._core_modules.get(name)) is not None:
                return m

            code = self._compile_core_module(name)

            module = self.new_module(
                name,
                filename=code.co_filename if not code.co_filename.startswith('<') else None,
            )
            self._core_modules[name] = module
            try:
                exec(code, module.__dict__)  # noqa: S102
            except BaseException:
                del self._core_modules[name]
                raise

            return module

    ##
    # Modules

    def _get_prelude_values(self) -> dict[str, ta.Any]:
        if (pv := self._prelude_values) is None:
            pv = {p.name: importlib.import_module(p.module) for p in self._prelude}
            self._prelude_values = pv
        return pv

    def prepare_module(self, module: types.ModuleType) -> None:
        """
        Prepare a module for running Hy code compiled by this runtime: bind ``hy`` and the prelude (without overwriting
        existing prelude names), add the macro tables Hy expects, and - unless it has its own - give it the builtins of
        the runtime's module system.
        """

        ns = module.__dict__

        ns['hy'] = self._hy
        for k, v in self._get_prelude_values().items():
            ns.setdefault(k, v)

        ns.setdefault('_hy_macros', {})
        ns.setdefault('_hy_reader_macros', {})

        if (b := self._modules.module_builtins()) is not None:
            ns.setdefault('__builtins__', b)

        self._prepared_modules[id(ns)] = module

    def new_module(
            self,
            name: str = '__hy__',
            *,
            filename: str | None = None,
            search_locations: ta.Sequence[str] | None = None,
    ) -> types.ModuleType:
        """
        Create a new, prepared module. It isn't registered anywhere - use ``modules.add_module`` to make it importable.
        If ``search_locations`` is given the module is a package, with those as its ``__path__``.
        """

        module = types.ModuleType(name)

        if filename is not None:
            module.__file__ = filename

        if search_locations is not None:
            module.__path__ = list(search_locations)
            module.__package__ = name
        else:
            module.__package__ = name.rpartition('.')[0]

        self.prepare_module(module)
        return module

    def import_module(self, name: str) -> types.ModuleType:
        """Import a module by absolute name, as it would be imported by Hy code running in this runtime."""

        return self._modules.import_module(name)

    def module_for_globals(self, globals: ta.Mapping[str, ta.Any]) -> types.ModuleType | None:  # noqa: A002
        """Find the module whose namespace is ``globals``, if this runtime knows of it."""

        if (m := self._prepared_modules.get(id(globals))) is not None and m.__dict__ is globals:
            return m

        if (
                isinstance(name := globals.get('__name__'), str) and
                (m := self._modules.get_module(name)) is not None and
                m.__dict__ is globals
        ):
            return m

        return None

    def calling_module(self, frame: types.FrameType) -> types.ModuleType:
        """The module whose code is running in ``frame``, for Hy APIs which default to operating on their caller."""

        if (m := self.module_for_globals(frame.f_globals)) is not None:
            return m

        raise TypeError(
            f'Code in {frame.f_code.co_filename!r} is running in a namespace unknown to its Hy runtime, and so an '
            f'explicit module must be specified',
        )

    def preamble_statements(self) -> list[ast.stmt]:
        """Statements binding ``hy`` and the prelude, for compiled code which will be run outside of this runtime."""

        stmts: list[ast.stmt] = [
            ast.Import(names=[ast.alias(name=p.module, asname=p.name)])
            for p in self._prelude
        ]

        if (hy_from := self._modules.preamble_hy_import()) is not None:
            stmts.append(ast.ImportFrom(module=hy_from, names=[ast.alias(name='hy')], level=0))

        return [ast.fix_missing_locations(s) for s in stmts]

    ##
    # Reading, compiling, and evaluating

    @staticmethod
    def _as_tree(
            code: str | Object,
            *,
            filename: str | None,
    ) -> tuple[Object, str | None]:
        if isinstance(code, str):
            return read_many(code, filename=filename or '<string>'), code
        return code, None

    def compile(
            self,
            code: str | Object,
            module: types.ModuleType | None = None,
            *,
            filename: str | None = None,
            preamble: bool = False,
    ) -> ast.Module:
        """
        Compile Hy source code (or a model) into a Python AST, in the context of ``module`` (a fresh one by default).
        Note that compiling may itself evaluate code, such as macro definitions.
        """

        tree, source = self._as_tree(code, filename=filename)
        return ta.cast(ast.Module, hy_compile(
            tree,
            module if module is not None else self.new_module(),
            filename=filename,
            source=source,
            preamble=preamble,
            runtime=self,
        ))

    def exec_module_source(
            self,
            module: types.ModuleType,
            source: str,
            *,
            filename: str = '<string>',
    ) -> None:
        """Compile and run a whole Hy module's source in ``module``, as by importing it."""

        tree = read_many(source, filename=filename, skip_shebang=True)
        code = compile(
            hy_compile(tree, module, filename=filename, source=source, runtime=self),
            filename,
            'exec',
            dont_inherit=True,
        )
        exec(code, module.__dict__)  # noqa: S102

    def exec(
            self,
            code: str | Object,
            module: types.ModuleType | None = None,
            *,
            filename: str | None = None,
    ) -> types.ModuleType:
        """Run Hy source code (or a model) in ``module`` (a fresh one by default), returning the module."""

        if module is None:
            module = self.new_module()

        self.eval(code, module, filename=filename)
        return module

    @contextlib.contextmanager
    def _bound_into(
            self,
            globals: dict[str, ta.Any] | None,  # noqa: A002
            locals: ta.MutableMapping[str, ta.Any] | None,  # noqa: A002
    ) -> ta.Iterator[None]:
        """
        Code evaluated in explicitly given namespaces (rather than a prepared module's) still sees ``hy`` and the
        prelude: they're temporarily bound in the innermost namespace for the duration of the evaluation. Functions
        defined by the code, however, won't see them afterwards, unless they're also present in the given globals.
        """

        # Invalid namespaces are left for evaluation itself to reject.
        if isinstance(globals, dict) and (b := self._modules.module_builtins()) is not None:
            globals.setdefault('__builtins__', b)

        if not isinstance(ns := locals if locals is not None else globals, collections.abc.MutableMapping):
            yield
            return

        missing = object()
        saved: dict[str, ta.Any] = {}

        def bind(k: str, v: ta.Any, *, overwrite: bool) -> None:
            if (old := ns.get(k, missing)) is missing or (overwrite and old is not v):
                saved[k] = old
                ns[k] = v

        bind('hy', self._hy, overwrite=True)
        for k, v in self._get_prelude_values().items():
            bind(k, v, overwrite=False)

        try:
            yield
        finally:
            for k, old in saved.items():
                if old is missing:
                    ns.pop(k, None)
                else:
                    ns[k] = old

    def eval(
            self,
            code: str | Object,
            module: types.ModuleType | None = None,
            *,
            globals: dict[str, ta.Any] | None = None,  # noqa: A002
            locals: ta.MutableMapping[str, ta.Any] | None = None,  # noqa: A002
            filename: str | None = None,
            macros: ta.Mapping[str, ta.Callable[..., ta.Any]] | None = None,
    ) -> ta.Any:
        """
        Evaluate Hy source code (or a model), returning the value of its last form.

        Macros are looked up in, and compile-time code is run in, ``module`` - a fresh one by default. Code is run with
        ``module``'s namespace as its globals unless ``globals`` are given. ``macros`` may give additional macros, by
        mangled name.
        """

        tree, source = self._as_tree(code, filename=filename)
        with self._bound_into(globals, locals):
            return hy_eval(
                tree,
                locals,
                module if module is not None else self.new_module(),
                filename=filename,
                source=source,
                globals=globals,
                extra_macros=macros,
                runtime=self,
            )

    def _eval_from_hy(
            self,
            model: ta.Any,
            globals: dict[str, ta.Any] | None = None,  # noqa: A002
            locals: ta.MutableMapping[str, ta.Any] | None = None,  # noqa: A002
            module: types.ModuleType | str | None = None,
            macros: ta.Mapping[str, ta.Callable[..., ta.Any]] | None = None,
    ) -> ta.Any:
        """
        ``hy.eval``: an equivalent of Python's :func:`eval` for evaluating Hy code. The chief difference is that the
        first argument should be a :ref:`model <models>` rather than source text. If you have a string of source text
        you want to evaluate, convert it to a model first with :hy:func:`hy.read` or :hy:func:`hy.read-many`::

            (hy.eval '(+ 1 1))             ; => 2
            (hy.eval (hy.read "(+ 1 1)"))  ; => 2

        The optional arguments ``globals`` and ``locals`` work as in the case of :func:`eval`.

        Another optional argument, ``module``, can be a module object or a string naming a module. The module's
        ``__dict__`` attribute can fill in for ``globals`` (and hence also for ``locals``) if ``module`` is provided but
        ``globals`` isn't, but the primary purpose of ``module`` is to control where macro calls are looked up. Without
        this argument, the calling module of ``hy.eval`` is used instead.

        Finer control of macro lookup can be achieved by passing in a dictionary of macros as the ``macros`` argument.
        The keys of this dictionary should be mangled macro names, and the values should be function objects to
        implement those macros. This is the same structure as is produced by :hy:func:`local-macros
        <hy.core.macros.local-macros>`, and in fact, ``(hy.eval … :macros (local-macros))`` is useful to make local
        macros visible to ``hy.eval``, which otherwise doesn't see them. Macros provided in this dictionary shadow
        macros of the same name that are associated with the provided or implicit module - including core macros.
        """

        frame = sys._getframe(1)  # noqa: SLF001

        if locals is None:
            locals = globals  # noqa: A001

        target: types.ModuleType
        if isinstance(module, str):
            target = self.import_module(mangle(module))
        elif module is not None:
            target = module
        else:
            target = self.calling_module(frame)

        with self._bound_into(globals, locals):
            return hy_eval(
                model,
                locals=frame.f_locals if locals is None and module is None else locals,
                module=target,
                globals=globals,
                extra_macros=macros,
                runtime=self,
            )

    def read(self, source: str, *, filename: str | None = None) -> Object:
        return read(source, filename=filename)

    def read_many(self, source: str, *, filename: str | None = '<string>') -> Lazy:
        return read_many(source, filename=filename)
