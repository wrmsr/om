"""
Sources of Hy modules for isolated runtimes.

An isolated :class:`HyRuntime <.runtime.HyRuntime>` doesn't use Python's import system to find Hy modules - instead it
asks its configured finders, in order, for the source of each module being imported. Anything no finder claims is
imported as a regular Python module.
"""
import abc
import importlib.resources
import os.path
import types
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True)
class HyModuleSource:
    """The source of a single Hy module, as found by a :class:`HyModuleFinder`."""

    name: str
    source: str

    _: dc.KW_ONLY

    # Used for error messages, tracebacks, and source inspection. If the source came from an actual file this should be
    # its path, in which case it's also set as the module's `__file__`.
    filename: str | None = None
    is_file: bool = False

    # Non-None for packages: where their submodules may be found, set as the module's `__path__`.
    search_locations: ta.Sequence[str] | None = None

    def __post_init__(self) -> None:
        check.non_empty_str(self.name)
        check.arg(not self.is_file or self.filename is not None)

    @property
    def is_package(self) -> bool:
        return self.search_locations is not None


class HyModuleFinder(lang.Abstract):
    @abc.abstractmethod
    def find_hy_module(self, name: str, parent: types.ModuleType | None) -> HyModuleSource | None:
        """
        Return the source of the Hy module with the given absolute name, or `None` if it's not found by this finder.
        For dotted names, `parent` is the already-imported parent package (which may itself be a Python package).
        """

        raise NotImplementedError


##


class MappingHyModuleFinder(HyModuleFinder):
    """
    Finds Hy modules in a mapping of absolute module names to their source code. A name which prefixes other names in
    the mapping is a package, with an empty body if it isn't in the mapping itself.
    """

    def __init__(self, sources: ta.Mapping[str, str]) -> None:
        super().__init__()

        self._sources = dict(sources)
        self._packages = frozenset(
            prefix
            for name in self._sources
            for prefix in ('.'.join(name.split('.')[:i]) for i in range(1, name.count('.') + 1))
        )

    def find_hy_module(self, name: str, parent: types.ModuleType | None) -> HyModuleSource | None:
        is_package = name in self._packages
        if (source := self._sources.get(name)) is None:
            if not is_package:
                return None
            source = ''

        return HyModuleSource(
            name,
            source,
            filename=f'<hy:{name}>',
            search_locations=[] if is_package else None,
        )


class DirectoryHyModuleFinder(HyModuleFinder):
    """
    Finds Hy modules in a directory tree on the filesystem, mapping module ``a.b`` to ``<root>/a/b.hy`` or, as a
    package, ``<root>/a/b/__init__.hy``. Directories containing no ``__init__.hy`` are treated as empty packages.
    """

    def __init__(self, root: str) -> None:
        super().__init__()

        self._root = os.path.abspath(root)

    def find_hy_module(self, name: str, parent: types.ModuleType | None) -> HyModuleSource | None:
        base = os.path.join(self._root, *name.split('.'))

        if os.path.isdir(base):
            init = os.path.join(base, '__init__.hy')
            if os.path.isfile(init):
                return _read_hy_module_file(name, init, search_locations=[base])
            return HyModuleSource(name, '', filename=base, search_locations=[base])

        if os.path.isfile(fp := base + '.hy'):
            return _read_hy_module_file(name, fp)

        return None


class PackageHyModuleFinder(HyModuleFinder):
    """
    Finds ``.hy`` files living alongside regular Python modules inside of importable packages - including Hy packages
    within them (directories with an ``__init__.hy``). Only submodules are found - never top-level modules. Resources of
    Python packages are accessed through :mod:`importlib.resources`, so packages need not live on a filesystem.

    If ``prefixes`` are given, only modules within the packages they name are considered.
    """

    def __init__(self, *, prefixes: ta.Iterable[str] | None = None) -> None:
        super().__init__()

        self._prefixes = frozenset(prefixes) if prefixes is not None else None

    def _is_allowed(self, name: str) -> bool:
        if self._prefixes is None:
            return True
        return any(name == p or name.startswith(p + '.') for p in self._prefixes)

    def find_hy_module(self, name: str, parent: types.ModuleType | None) -> HyModuleSource | None:
        if parent is None or not self._is_allowed(name):
            return None

        child = name.rpartition('.')[2]

        # Python packages: go through their resource readers.
        if (spec := getattr(parent, '__spec__', None)) is not None and spec.loader is not None:
            try:
                files = importlib.resources.files(parent)
            except (TypeError, ValueError, ModuleNotFoundError):
                return None

            if (fp := files.joinpath(child + '.hy')).is_file():
                return _hy_module_source_from_traversable(name, fp)

            if (pkg := files.joinpath(child)).is_dir() and (init := pkg.joinpath('__init__.hy')).is_file():
                return _hy_module_source_from_traversable(name, init, package_dir=pkg)

            return None

        # Packages loaded by a runtime from the filesystem: go through their `__path__`.
        for location in getattr(parent, '__path__', None) or ():
            if os.path.isfile(file_path := os.path.join(location, child + '.hy')):
                return _read_hy_module_file(name, file_path)

            if os.path.isfile(init_path := os.path.join(location, child, '__init__.hy')):
                return _read_hy_module_file(name, init_path, search_locations=[os.path.join(location, child)])

        return None


##


def _read_hy_module_file(
        name: str,
        file_path: str,
        *,
        search_locations: ta.Sequence[str] | None = None,
) -> HyModuleSource:
    with open(file_path, encoding='utf-8') as f:
        source = f.read()

    return HyModuleSource(
        name,
        source,
        filename=file_path,
        is_file=True,
        search_locations=search_locations,
    )


def _hy_module_source_from_traversable(
        name: str,
        file: importlib.resources.abc.Traversable,
        *,
        package_dir: importlib.resources.abc.Traversable | None = None,
) -> HyModuleSource:
    # Resources on a real filesystem get real filenames (and thus working tracebacks and `inspect` support), and
    # packages there get real search locations.
    file_path = os.fspath(file) if isinstance(file, os.PathLike) else None
    package_path = os.fspath(package_dir) if isinstance(package_dir, os.PathLike) else None

    return HyModuleSource(
        name,
        file.read_text(encoding='utf-8'),
        filename=file_path if file_path is not None else f'<hy:{name}>',
        is_file=file_path is not None,
        search_locations=(
            ([package_path] if package_path is not None else [])
            if package_dir is not None
            else None
        ),
    )
