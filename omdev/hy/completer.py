"""Tab completion of (unmangled) Hy names, and the `readline` integration of the REPL."""
import builtins
import contextlib
import importlib
import os
import re
import sys
import types
import typing as ta

from omcore import check
from omcore import lang

from .reader import mangle
from .reader import unmangle


##


@lang.cached_function
def init_readline() -> types.ModuleType | None:
    """
    Import and return the `readline` module, or return None if it's unavailable. It's imported lazily, rather than at
    module import, to work around https://github.com/python/cpython/issues/46927#issuecomment-1093418916.
    """

    try:
        return importlib.import_module('readline')

    except AttributeError as e:
        # https://github.com/pyreadline/pyreadline/issues/65
        if "module 'collections' has no attribute 'Callable'" not in str(e):
            raise
        return None

    except ImportError:
        return None


##


def maybe_unmangle(text: str) -> tuple[str, str]:
    """Return a pair of the unmangled form of `text` (or `text` itself, if it can't be unmangled) and `text`."""

    try:
        unmangled = unmangle(text)
    except KeyError:
        unmangled = text

    return (unmangled, text)


def canonicalize(text: str) -> str:
    try:
        return unmangle(mangle(text)) if text else ''
    except KeyError:
        return text


class Completer:
    """
    A `readline` completer of the names visible in a namespace - its globals, the builtins, and its macros - and of
    attributes of the objects they refer to, in their unmangled forms.

    The namespace, if given, must be a dict, which gets the `_hy_macros` and `_hy_reader_macros` entries of a Hy module
    namespace if it lacks them.
    """

    def __init__(self, namespace: dict[str, ta.Any] | None = None) -> None:
        super().__init__()

        if namespace is None:
            namespace = {}
        check.isinstance(namespace, dict)

        namespace.setdefault('_hy_macros', {})
        namespace.setdefault('_hy_reader_macros', {})

        self._namespace = namespace
        self._path: ta.Sequence[ta.Mapping[ta.Any, ta.Any]] = [
            builtins.__dict__,
            namespace,
            namespace['_hy_macros'],
        ]

    def attr_matches(self, text: str) -> list[str]:
        # Borrowed from IPython's completer
        if (m := re.match(r'(\S+(\.[\S]+)*)\.([\S]*)$', text)) is None:
            return []

        expr, orig_attr = m.group(1, 3)
        attr = canonicalize(orig_attr)

        try:
            sym, *syms = expr.split('.')
            obj = self._namespace[mangle(sym)]
            for sym in syms:
                obj = getattr(obj, mangle(sym))
            names = dir(obj)
        except Exception:  # noqa: BLE001
            return []

        return [
            f'{expr}.{unmangled}'
            for unmangled, name in map(maybe_unmangle, names)
            if unmangled.startswith(attr) or name.startswith(orig_attr)
        ]

    def global_matches(self, text: str) -> list[str]:
        canonicalized = canonicalize(text)

        matches: list[str] = []
        for p in self._path:
            for k in p:
                if not isinstance(k, str):
                    continue

                unmangled, name = maybe_unmangle(k)
                if unmangled.startswith(canonicalized) or name.startswith(text):
                    matches.append(unmangled)

        return matches

    def complete(self, text: str, state: int) -> str | None:
        if '.' in text:
            matches = self.attr_matches(text)
        else:
            matches = self.global_matches(text)

        try:
            return matches[state]
        except IndexError:
            return None


##


def _take_readline_history(readline: types.ModuleType) -> list[str | None]:
    """Remove and return all of the current `readline` history."""

    items: list[str | None] = []
    for _ in range(readline.get_current_history_length()):
        # The first item is numbered 1 by one method, and 0 by the other.
        items.append(readline.get_history_item(1))
        readline.remove_history_item(0)

    return items


def _restore_readline_history(readline: types.ModuleType, items: ta.Iterable[str | None]) -> None:
    readline.clear_history()

    for item in items:
        if item is not None:
            readline.add_history(item)


def default_history_file() -> str:
    return os.environ.get('HY_HISTORY', os.path.expanduser('~/.hy-history'))


@contextlib.contextmanager
def completion(
        completer: Completer | None = None,
        *,
        history_file: str | None = None,
) -> ta.Iterator[None]:
    """
    Use `completer` (by default, one of an empty namespace) for tab completion with `readline` for the duration, with
    the history of `history_file` (by default, the file named by the `HY_HISTORY` environment variable, or else
    `~/.hy-history`) in place of the current history. Does nothing if `readline` is unavailable.
    """

    if (readline := init_readline()) is None:
        yield
        return

    if completer is None:
        completer = Completer()

    if sys.platform == 'darwin' and 'libedit' in (readline.__doc__ or ''):
        readline_bind = 'bind ^I rl_complete'
    else:
        readline_bind = 'tab: complete'

    readline.set_completer(completer.complete)
    readline.set_completer_delims('()[]{} ')

    if history_file is None:
        history_file = default_history_file()
    readline.parse_and_bind('set blink-matching-paren on')

    saved_history = _take_readline_history(readline)

    try:
        readline.read_history_file(history_file)
    except OSError:
        pass

    readline.parse_and_bind(readline_bind)

    try:
        yield

    finally:
        try:
            readline.write_history_file(history_file)
        except OSError:
            pass

        _restore_readline_history(readline, saved_history)
