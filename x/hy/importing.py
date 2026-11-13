"""
Module systems for Hy runtimes.

A :class:`HyRuntime <.runtime.HyRuntime>` delegates the resolution, loading, and registration of modules to a
:class:`HyModules` instance, of which there are two kinds:

  - :class:`IsolatedHyModules`, the default, keeps a module registry private to its runtime, finds Hy modules through a
    configurable list of :class:`HyModuleFinder <.finders.HyModuleFinder>`'s, and touches no global interpreter state:
    nothing is added to ``sys.modules``, and no import hooks are installed. Hy code running in such a runtime gets a
    private ``__builtins__`` with an ``__import__`` which first consults the runtime, falling back to Python's import
    system for regular Python modules.

  - :class:`SysHyModules` simply uses ``sys.modules`` and Python's import system, and is what the opt-in global runtime
    (see :mod:`.globalruntime`) uses - in which case Hy modules are found through Python's import system by way of an
    installed path hook.
"""
import abc
import builtins
import importlib
import importlib.util
import sys
import threading
import types
import typing as ta

from omcore import check
from omcore import lang

from .finders import HyModuleFinder
from .finders import HyModuleSource


if ta.TYPE_CHECKING:
    from .runtime import HyRuntime


HyModulesFactory: ta.TypeAlias = ta.Callable[['HyRuntime'], 'HyModules']


##


class HyModules(lang.Abstract):
    @abc.abstractmethod
    def import_module(self, name: str) -> types.ModuleType:
        """Import a module by absolute name, as visible to Hy code running in the owning runtime."""

        raise NotImplementedError

    @abc.abstractmethod
    def get_module(self, name: str) -> types.ModuleType | None:
        """Return the already-loaded module of the given name, if any, without importing anything."""

        raise NotImplementedError

    @abc.abstractmethod
    def add_module(self, module: types.ModuleType) -> None:
        """Register a module under its `__name__`, making it importable."""

        raise NotImplementedError

    @abc.abstractmethod
    def remove_module(self, name: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def module_builtins(self) -> dict[str, ta.Any] | None:
        """The `__builtins__` given to modules prepared by the owning runtime, or `None` for Python's own."""

        raise NotImplementedError

    @abc.abstractmethod
    def preamble_hy_import(self) -> str | None:
        """
        The absolute name of a module from which compiled module code can import ``hy`` itself, for code which is to be
        executed somewhere its runtime can't inject it (such as bytecode loaded by Python's import system). `None` if
        there's no such module.
        """

        raise NotImplementedError


##


class SysHyModules(HyModules):
    """Python's own module system: modules live in ``sys.modules`` and are imported through ``importlib``."""

    def __init__(self, *, preamble_hy_import: str | None = None) -> None:
        super().__init__()

        self._preamble_hy_import = preamble_hy_import

    def import_module(self, name: str) -> types.ModuleType:
        return importlib.import_module(name)

    def get_module(self, name: str) -> types.ModuleType | None:
        return sys.modules.get(name)

    def add_module(self, module: types.ModuleType) -> None:
        sys.modules[module.__name__] = module

    def remove_module(self, name: str) -> None:
        sys.modules.pop(name, None)

    def module_builtins(self) -> dict[str, ta.Any] | None:
        return None

    def preamble_hy_import(self) -> str | None:
        return self._preamble_hy_import


##


class HyModuleOverlay(types.ModuleType):
    """
    A view of a module with some extra attributes overlaid on top of it.

    Isolated runtimes never add attributes to modules they don't own, so when a runtime-owned Hy module lives inside of
    a regular Python package, ``import pkg.hymod`` and ``from pkg import hymod`` are given an overlay of ``pkg`` through
    which the Hy module is visible as an attribute, rather than ``pkg`` itself.
    """

    def __init__(self, base: types.ModuleType, overlays: ta.Mapping[str, ta.Any]) -> None:
        super().__init__(base.__name__, base.__doc__)

        self.__dict__['_hy_overlay_base'] = base
        self.__dict__.update(overlays)

    def __getattr__(self, name: str) -> ta.Any:
        return getattr(self.__dict__['_hy_overlay_base'], name)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} of {self.__dict__["_hy_overlay_base"]!r}>'


class IsolatedHyModules(HyModules):
    """
    A module registry private to a single runtime.

    Hy modules are found through ``finders`` (and the runtime's own core Hy modules are always available); everything
    else is imported through Python's import system. Results of finder lookups - including misses - are cached for the
    life of the registry (see :meth:`invalidate_caches`).

    Limitations, compared to Python's import system:

      - Python modules can't be found inside of runtime-owned Hy packages.
      - Hy modules have no ``__spec__``, and so aren't visible to tools which go through ``sys.modules`` or importlib
        (such as ``inspect.getmodule``, or ``pickle``-ing classes defined in them by reference).
    """

    def __init__(
            self,
            runtime: HyRuntime,
            *,
            finders: ta.Iterable[HyModuleFinder] = (),
    ) -> None:
        super().__init__()

        self._runtime = runtime
        self._finders = list(finders)

        self._lock = threading.RLock()
        self._modules: dict[str, types.ModuleType] = {}
        self._not_hy: set[str] = set()

        self._builtins: dict[str, ta.Any] | None = None

    @property
    def finders(self) -> ta.Sequence[HyModuleFinder]:
        return self._finders

    def invalidate_caches(self) -> None:
        with self._lock:
            self._not_hy.clear()

    #

    def get_module(self, name: str) -> types.ModuleType | None:
        if (m := self._modules.get(name)) is not None:
            return m
        return self._runtime.get_core_module(name)

    def add_module(self, module: types.ModuleType) -> None:
        with self._lock:
            self._modules[module.__name__] = module

    def remove_module(self, name: str) -> None:
        with self._lock:
            self._modules.pop(name, None)

    def preamble_hy_import(self) -> str | None:
        return None

    #

    def _find_source(self, name: str, parent: types.ModuleType | None) -> HyModuleSource | None:
        if name in self._not_hy:
            return None

        for finder in self._finders:
            if (src := finder.find_hy_module(name, parent)) is not None:
                return src

        self._not_hy.add(name)
        return None

    def _load(self, src: HyModuleSource, parent: types.ModuleType | None) -> types.ModuleType:
        module = self._runtime.new_module(
            src.name,
            filename=src.filename if src.is_file else None,
            search_locations=src.search_locations,
        )

        # As with Python's import system, the module is registered before it's executed (supporting circular imports)
        # and unregistered if executing it fails.
        self._modules[src.name] = module
        try:
            self._runtime.exec_module_source(
                module,
                src.source,
                filename=src.filename or f'<hy:{src.name}>',
            )
        except BaseException:
            self._modules.pop(src.name, None)
            raise

        if parent is not None and parent.__name__ in self._modules:
            setattr(parent, src.name.rpartition('.')[2], module)

        return module

    def import_module(self, name: str) -> types.ModuleType:
        check.non_empty_str(name)
        if name.startswith('.'):
            raise ValueError(f'Module name must be absolute: {name!r}')

        if (m := self.get_module(name)) is not None:
            return m

        if (core := self._runtime.load_core_module(name)) is not None:
            return core

        parent: types.ModuleType | None = None
        if '.' in name:
            parent = self.import_module(name.rpartition('.')[0])

        with self._lock:
            if (m := self._modules.get(name)) is not None:
                return m

            if (src := self._find_source(name, parent)) is not None:
                return self._load(src, parent)

        if parent is not None and parent.__name__ in self._modules and parent.__name__ not in sys.modules:
            raise ModuleNotFoundError(f'No module named {name!r}', name=name)

        return importlib.import_module(name)

    #

    def _attribute_view(self, module_name: str, target_name: str) -> types.ModuleType:
        """
        The module named `module_name`, viewed such that the chain of attribute lookups down to the module named
        `target_name` - which must be within it - succeeds.
        """

        module = check.not_none(self.get_module(module_name) or sys.modules.get(module_name))
        if module_name == target_name:
            return module

        child_attr = target_name[len(module_name) + 1:].partition('.')[0]
        child = self._attribute_view(f'{module_name}.{child_attr}', target_name)
        if getattr(module, child_attr, None) is child:
            return module
        return HyModuleOverlay(module, {child_attr: child})

    def _handle_fromlist(self, module: types.ModuleType, fromlist: ta.Sequence[str]) -> types.ModuleType:
        names = list(fromlist)
        if '*' in names:
            names.remove('*')
            names.extend(getattr(module, '__all__', ()))

        overlays: dict[str, types.ModuleType] = {}
        if hasattr(module, '__path__'):
            for x in names:
                if hasattr(module, x):
                    continue

                sub_name = f'{module.__name__}.{x}'
                try:
                    sub = self.import_module(sub_name)
                except ModuleNotFoundError as e:
                    # As in Python, a missing name is left to fail at the `from ... import` itself - but other import
                    # failures propagate.
                    if e.name != sub_name:
                        raise
                    continue

                if getattr(module, x, None) is not sub:
                    overlays[x] = sub

        return HyModuleOverlay(module, overlays) if overlays else module

    def _dunder_import(
            self,
            name: str,
            globals: ta.Mapping[str, ta.Any] | None = None,  # noqa: A002
            locals: ta.Mapping[str, ta.Any] | None = None,  # noqa: A002
            fromlist: ta.Sequence[str] | None = (),
            level: int = 0,
    ) -> types.ModuleType:
        if level:
            package = _calc_package(globals or {})
            abs_name = importlib.util.resolve_name('.' * level + name, package)
        else:
            abs_name = name

        module = self.import_module(abs_name)

        if fromlist:
            return self._handle_fromlist(module, fromlist)

        if not name:
            return module

        # As in Python: `import a.b.c` evaluates to (a view of) `a`.
        cut_off = len(name) - len(name.partition('.')[0])
        return self._attribute_view(abs_name[:len(abs_name) - cut_off], abs_name)

    def module_builtins(self) -> dict[str, ta.Any] | None:
        if (b := self._builtins) is None:
            b = dict(builtins.__dict__)
            b['__import__'] = self._dunder_import
            self._builtins = b
        return b


def _calc_package(globals: ta.Mapping[str, ta.Any]) -> str:  # noqa: A002
    if (package := globals.get('__package__')) is not None:
        return package

    if (spec := globals.get('__spec__')) is not None:
        return spec.parent

    package = globals['__name__']
    if '__path__' not in globals:
        package = package.rpartition('.')[0]
    return package
