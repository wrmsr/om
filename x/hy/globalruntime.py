"""
The opt-in global Hy runtime, integrated with Python's import system.

Nothing in this package touches global interpreter state unless :func:`install` is called. Once it is, a single
process-wide :class:`HyRuntime <.runtime.HyRuntime>` - using ``sys.modules`` as its module registry - backs:

  - ``.hy`` files becoming importable through Python's regular import system, from directories and zip archives on
    ``sys.path``, preferred over same-named ``.py`` files and bytecode-cached like them,
  - Hy-aware source inspection in :mod:`inspect` (see :mod:`.inspection`),
  - :mod:`multiprocessing` children (in ``spawn`` and ``forkserver`` modes) installing the global runtime themselves
    before running anything, so they can import Hy modules and run Hy main scripts.

Hy modules compiled by the global runtime bind ``hy`` (and the runtime's prelude) by importing them in a preamble, as
``from <package>.autoinstall import hy`` - so that, as with upstream Hy, merely running such compiled code (for instance
the output of ``hy2py``) installs the global runtime. Each part of the installation is reversed by :func:`uninstall`.
"""
import ast
import contextlib
import contextvars
import importlib.abc
import importlib.machinery
import importlib.util
import marshal
import os
import sys
import threading
import types
import typing as ta
import zipimport

from omcore import check

from . import inspection
from .compiler import hy_compile
from .importing import SysHyModules
from .reader import read_many
from .runtime import HyRuntime


##


def _new_global_runtime() -> HyRuntime:
    return HyRuntime(modules=lambda _: SysHyModules(preamble_hy_import=f'{__package__}.autoinstall'))


class _HyGlobalState:
    def __init__(self) -> None:
        super().__init__()

        self.lock = threading.RLock()

        self.runtime: HyRuntime | None = None

        self.path_hooks: list[ta.Callable[[str], ta.Any]] | None = None
        self.inspect_installed = False
        self.multiprocessing_installed: _HyMultiprocessingInstallation | None = None


_STATE = _HyGlobalState()


def get_global_runtime() -> HyRuntime:
    """
    Return the global runtime, creating it if necessary. Note that merely creating it doesn't install anything - see
    :func:`install`.
    """

    if (rt := _STATE.runtime) is not None:
        return rt

    with _STATE.lock:
        if (rt := _STATE.runtime) is None:
            rt = _STATE.runtime = _new_global_runtime()
        return rt


##
# Loaders


# The module currently being executed by a `HyLoader`, so that its code is compiled in the context of the actual module
# being loaded (which is where compile-time definitions like macros must go).
_LOADING_MODULE: contextvars.ContextVar[tuple[importlib.abc.Loader, types.ModuleType] | None] = contextvars.ContextVar(
    f'{__name__}._LOADING_MODULE',
    default=None,
)


@contextlib.contextmanager
def _loading_module(loader: importlib.abc.Loader, module: types.ModuleType) -> ta.Iterator[None]:
    token = _LOADING_MODULE.set((loader, module))
    try:
        yield
    finally:
        _LOADING_MODULE.reset(token)


def _compile_hy_module_source(
        loader: importlib.abc.Loader,
        fullname: str,
        data: bytes | str,
        path: str,
) -> ast.Module:
    runtime = get_global_runtime()

    source = data.decode('utf-8') if isinstance(data, bytes) else data

    if (lm := _LOADING_MODULE.get()) is not None and lm[0] is loader:
        module = lm[1]
    else:
        # The code is being compiled without being executed (such as by `py_compile` or `runpy`), so compile-time
        # evaluation gets a scratch module.
        module = runtime.new_module(fullname, filename=path)

    return ta.cast(ast.Module, hy_compile(
        read_many(source, filename=path, skip_shebang=True),
        module,
        filename=path,
        source=source,
        preamble=True,
        runtime=runtime,
    ))


class HyLoader(importlib.machinery.SourceFileLoader):
    """A loader of Hy source files from the filesystem, with bytecode caching as for Python source files."""

    def exec_module(self, module: types.ModuleType) -> None:
        with _loading_module(self, module):
            super().exec_module(module)

    def source_to_code(  # type: ignore[override]
            self,
            data: bytes | str,
            path: str,
            *,
            _optimize: int = -1,
    ) -> types.CodeType:
        return super().source_to_code(
            _compile_hy_module_source(self, self.name, data, path),
            path,
            _optimize=_optimize,
        )


class HyZipLoader(importlib.abc.SourceLoader):
    """A loader of Hy source files within zip archives on ``sys.path``. No bytecode caching is done."""

    def __init__(self, fullname: str, path: str, importer: zipimport.zipimporter) -> None:
        super().__init__()

        self.name = fullname
        self.path = path
        self._importer = importer

    def get_filename(self, fullname: str) -> str:
        return self.path

    def get_data(self, path: str) -> bytes:
        return self._importer.get_data(path)

    def exec_module(self, module: types.ModuleType) -> None:
        with _loading_module(self, module):
            super().exec_module(module)

    def source_to_code(  # type: ignore[override]
            self,
            data: bytes | str,
            path: str,
            *,
            _optimize: int = -1,
    ) -> types.CodeType:
        return compile(
            _compile_hy_module_source(self, self.name, data, path),
            path,
            'exec',
            dont_inherit=True,
            optimize=_optimize,
        )


class HyZipImporter(zipimport.zipimporter):
    """A zip importer which also finds Hy modules, though preferring Python modules of the same name."""

    def find_spec(self, fullname: str, target: types.ModuleType | None = None) -> importlib.machinery.ModuleSpec | None:
        spec = super().find_spec(fullname, target)
        if spec is not None and spec.loader is not None:
            return spec

        name = fullname.rpartition('.')[2]
        for rel, is_package in ((f'{name}/__init__.hy', True), (f'{name}.hy', False)):
            inner_path = self.prefix + rel
            try:
                self.get_data(inner_path)
            except OSError:
                continue

            path = os.path.join(self.archive, inner_path)
            hy_spec = importlib.util.spec_from_loader(
                fullname,
                HyZipLoader(fullname, path, self),
                origin=path,
                is_package=is_package,
            )
            hy_spec = check.not_none(hy_spec)
            if is_package:
                hy_spec.submodule_search_locations = [os.path.join(self.archive, self.prefix + name)]
            hy_spec.has_location = True
            return hy_spec

        # Possibly a namespace package portion.
        return spec


def _new_file_path_hook() -> ta.Callable[[str], importlib.abc.PathEntryFinder]:
    # The same loaders as Python's default `FileFinder` path hook, with Hy preferred over Python source.
    return importlib.machinery.FileFinder.path_hook(
        (importlib.machinery.ExtensionFileLoader, importlib.machinery.EXTENSION_SUFFIXES),
        (HyLoader, ['.hy']),
        (importlib.machinery.SourceFileLoader, importlib.machinery.SOURCE_SUFFIXES),
        (importlib.machinery.SourcelessFileLoader, importlib.machinery.BYTECODE_SUFFIXES),
    )


def _install_path_hooks() -> list[ta.Callable[[str], ta.Any]]:
    file_hook = _new_file_path_hook()

    # Insert ahead of the default hooks they shadow, so they take precedence for every path entry they can handle.
    try:
        zip_idx = sys.path_hooks.index(zipimport.zipimporter)
    except ValueError:
        zip_idx = 0
    sys.path_hooks.insert(zip_idx, HyZipImporter)

    file_idx = next(
        (i for i, h in enumerate(sys.path_hooks) if getattr(h, '__name__', None) == 'path_hook_for_FileFinder'),
        len(sys.path_hooks),
    )
    sys.path_hooks.insert(file_idx, file_hook)

    # Finders already created for existing path entries won't know about Hy.
    sys.path_importer_cache.clear()
    importlib.invalidate_caches()

    return [HyZipImporter, file_hook]


def _uninstall_path_hooks(hooks: ta.Iterable[ta.Callable[[str], ta.Any]]) -> None:
    for h in hooks:
        try:
            sys.path_hooks.remove(h)
        except ValueError:
            pass

    sys.path_importer_cache.clear()
    importlib.invalidate_caches()


def compile_hy_file(
        file: str,
        *,
        cfile: str | None = None,
        dfile: str | None = None,
        optimize: int = -1,
) -> str:
    """
    Byte-compile a Hy source file, as :func:`py_compile.compile` does for Python source files, writing a timestamp-based
    pyc file to ``cfile`` (by default, the file's cache location). ``dfile`` is the filename recorded in the code
    object, defaulting to ``file``. Returns the path of the written file.
    """

    if cfile is None:
        cfile = importlib.util.cache_from_source(file, optimization=optimize if optimize >= 0 else '')

    loader = HyLoader('<hyc>', file)
    source_bytes = loader.get_data(file)
    code = loader.source_to_code(source_bytes, dfile or file, _optimize=optimize)

    st = os.stat(file)
    data = b''.join([
        importlib.util.MAGIC_NUMBER,
        (0).to_bytes(4, 'little'),  # Flags: timestamp-based.
        (int(st.st_mtime) & 0xFFFFFFFF).to_bytes(4, 'little'),
        (st.st_size & 0xFFFFFFFF).to_bytes(4, 'little'),
        marshal.dumps(code),
    ])

    if dn := os.path.dirname(cfile):
        os.makedirs(dn, exist_ok=True)
    tmp = f'{cfile}.{os.getpid()}.tmp'
    try:
        with open(tmp, 'wb') as f:
            f.write(data)
        os.replace(tmp, cfile)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return cfile


##
# Multiprocessing


class _HyMultiprocessingInstallation:
    """
    Makes ``spawn`` children run :func:`install` before anything else (by way of their bootstrap command line), and
    makes the ``forkserver`` server process import :mod:`.autoinstall` (which does the same) as part of its preload.
    """

    def __init__(self) -> None:
        super().__init__()

        # These are patched, so they must be the real modules (not lazy proxies of them).
        self._spawn: ta.Any = importlib.import_module('multiprocessing.spawn')
        self._forkserver: ta.Any = importlib.import_module('multiprocessing.forkserver')

        self._orig_get_command_line = self._spawn.get_command_line
        self._preload_module = f'{__package__}.autoinstall'
        self._bootstrap = f'from {__name__} import install; install(); '

    def _get_command_line(self, **kwds: ta.Any) -> list[str]:
        cmd = self._orig_get_command_line(**kwds)
        for i in range(len(cmd) - 1):
            if cmd[i] == '-c' and cmd[i + 1].startswith('from multiprocessing.spawn import '):
                cmd[i + 1] = self._bootstrap + cmd[i + 1]
                break
        return cmd

    def install(self) -> None:
        self._spawn.get_command_line = self._get_command_line

        fs = self._forkserver._forkserver  # noqa: SLF001
        preload = list(getattr(fs, '_preload_modules', []))
        if self._preload_module not in preload:
            fs.set_forkserver_preload([self._preload_module, *preload])

    def uninstall(self) -> None:
        if self._spawn.get_command_line == self._get_command_line:
            self._spawn.get_command_line = self._orig_get_command_line

        fs = self._forkserver._forkserver  # noqa: SLF001
        preload = list(getattr(fs, '_preload_modules', []))
        if self._preload_module in preload:
            preload.remove(self._preload_module)
            fs.set_forkserver_preload(preload)


##


def is_installed() -> bool:
    return _STATE.path_hooks is not None


def install(
        *,
        no_inspect: bool = False,
        no_multiprocessing: bool = False,
) -> HyRuntime:
    """
    Install the global runtime into the interpreter - see the module docstring - returning it. Idempotent, and
    thread-safe.
    """

    with _STATE.lock:
        rt = get_global_runtime()

        if _STATE.path_hooks is None:
            _STATE.path_hooks = _install_path_hooks()

        if not no_inspect and not _STATE.inspect_installed:
            inspection.install()
            _STATE.inspect_installed = True

        if not no_multiprocessing and _STATE.multiprocessing_installed is None:
            mpi = _HyMultiprocessingInstallation()
            mpi.install()
            _STATE.multiprocessing_installed = mpi

        return rt


def uninstall() -> None:
    """
    Undo :func:`install`. Modules already imported through the global runtime are left alone, and the global runtime
    itself remains available through :func:`get_global_runtime`.
    """

    with _STATE.lock:
        if (mpi := _STATE.multiprocessing_installed) is not None:
            mpi.uninstall()
            _STATE.multiprocessing_installed = None

        if _STATE.inspect_installed:
            inspection.uninstall()
            _STATE.inspect_installed = False

        if (hooks := _STATE.path_hooks) is not None:
            _uninstall_path_hooks(hooks)
            _STATE.path_hooks = None
