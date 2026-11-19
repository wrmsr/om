"""Running code from the command line."""
import contextlib
import importlib
import importlib.machinery
import importlib.util
import os
import runpy
import sys
import types
import typing as ta
import zipfile

from omcore import check

from .. import globalruntime
from ..compiler import hy_eval
from ..errors import HyLanguageError
from ..errors import filtered_hy_exceptions
from ..errors import hy_exc_handler
from ..reader import read_many
from ..runtime import HyRuntime


ExcInfo: ta.TypeAlias = tuple[type[BaseException] | None, BaseException | None, ta.Any]


##


def set_path(filename: str) -> None:
    """Emulate Python's command line by putting the directory of the file being run at the front of `sys.path`."""

    if sys.path[0] == '':
        sys.path.pop(0)
    sys.path.insert(0, os.path.realpath(os.path.dirname(os.path.normpath(filename))))


def show_internal_errors() -> bool:
    return bool(os.environ.get('HY_SHOW_INTERNAL_ERRORS', ''))


def filtered_exceptions() -> contextlib.AbstractContextManager[None]:
    return filtered_hy_exceptions(show_internal_errors=show_internal_errors())


def handle_exception(exc_info: ExcInfo | None = None) -> None:
    t, v, tb = exc_info if exc_info is not None else sys.exc_info()
    hy_exc_handler(check.not_none(t), check.not_none(v), tb, show_internal_errors=show_internal_errors())


def run_command(
        runtime: HyRuntime,
        source: str,
        *,
        filename: str | None = None,
) -> int:
    """Run Hy source in `__main__`, returning an exit code."""

    main = importlib.import_module('__main__')

    with filtered_exceptions():
        try:
            hy_eval(
                read_many(source, filename=filename),
                main.__dict__,
                main,
                filename=filename,
                source=source,
                runtime=runtime,
            )
        except HyLanguageError:
            handle_exception()
            return 1

    return 0


_PYTHON_FILE_SUFFIXES: ta.AbstractSet[str] = frozenset([
    *importlib.machinery.SOURCE_SUFFIXES,
    *importlib.machinery.BYTECODE_SUFFIXES,
])


def run_path(filename: str) -> None:
    """
    Run a file, directory, or zip archive as `__main__`. Files are treated as Hy source unless they have a Python
    extension. Requires the global runtime to be installed.
    """

    check.state(globalruntime.is_installed())

    if (
            os.path.isdir(filename) or
            zipfile.is_zipfile(filename) or
            os.path.splitext(filename)[1] in _PYTHON_FILE_SUFFIXES
    ):
        # With the global runtime installed, Python's machinery handles everything else - including finding a
        # `__main__.hy` in a directory or archive.
        runpy.run_path(filename, run_name='__main__')
        return

    # Load Hy source files with a `HyLoader` (meaning they're bytecode-cached, as imported modules are) into a fresh
    # `__main__` module.
    loader = globalruntime.HyLoader('__main__', filename)
    main = types.ModuleType('__main__')
    main.__file__ = filename
    main.__loader__ = loader

    # Give the main module a spec naming the script as a module - as Python itself does for `-m` - so that
    # `multiprocessing`'s `spawn` and `forkserver` children (which can't run Hy files by path) re-import it by name.
    base, ext = os.path.splitext(os.path.basename(filename))
    if ext == '.hy':
        main.__spec__ = importlib.util.spec_from_file_location(
            base,
            filename,
            loader=globalruntime.HyLoader(base, filename),
        )

    prev_main = sys.modules.get('__main__')
    sys.modules['__main__'] = main
    try:
        loader.exec_module(main)
    finally:
        if prev_main is not None:
            sys.modules['__main__'] = prev_main
