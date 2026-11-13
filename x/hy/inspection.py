# ruff: noqa: A002
"""
Get useful information from live Hy or Python objects.

This module provides Hy compatibility with CPython's inspect module. Within Hy, Hy macros are supported via Hy's
`get_macro` macro, for example `(inspect.getsource (get-macro get-macro))`. The Hy-aware functions are patched into
`inspect` only by :func:`install`, which is done as part of installing the global runtime.
"""
import inspect
import linecache
import typing as ta

from omcore import dataclasses as dc

from .errors import HySyntaxError
from .models import Expression
from .models import Lazy
from .models import Object
from .reader import HyReader
from .reader import read
from .reader.exceptions import LexException
from .reader.reader import ReaderMeta


##


class HySafeReader(HyReader):
    """
    A HyReader that skips over non-default reader macros.

    Skip over undefined reader macros so that no code is executed at read time. Do this by replacing the tag reader
    method to return None, as comments do.
    """

    if ta.TYPE_CHECKING:
        reader_for = ReaderMeta._attach_reader  # noqa: SLF001

    @reader_for(')')
    @reader_for(']')
    @reader_for('}')
    def _skip(self, key: str) -> None:
        return None

    @reader_for('#')
    def _safe_tag_dispatch(self, key: str) -> Object | None:
        try:
            return super().tag_dispatch(key)
        except LexException:
            return None


def is_expression(obj: object) -> ta.TypeIs[Expression]:
    return isinstance(obj, Expression)


def is_lazy(obj: object) -> ta.TypeIs[Lazy]:
    return isinstance(obj, Lazy)


##


@dc.dataclass(frozen=True)
class _HyInspectFunctions:
    """The functions of :mod:`inspect` which are replaced by Hy-aware versions while installed."""

    findsource: ta.Callable[..., tuple[list[str], int]]
    getcomments: ta.Callable[..., str | None]
    getfile: ta.Callable[..., str]
    getsource: ta.Callable[..., str]
    getsourcelines: ta.Callable[..., tuple[list[str], int]]


_HY_INSPECT_FUNCTION_NAMES: ta.Sequence[str] = tuple(f.name for f in dc.fields(_HyInspectFunctions))

_HY_INSPECT_ORIGINALS_ATTR = '_hy_originals'


def _get_originals() -> _HyInspectFunctions:
    # While installed, the originals are stashed on the `inspect` module itself.
    if (o := getattr(inspect, _HY_INSPECT_ORIGINALS_ATTR, None)) is not None:
        return o

    return _HyInspectFunctions(**{n: getattr(inspect, n) for n in _HY_INSPECT_FUNCTION_NAMES})


def _set_inspect_functions(fns: _HyInspectFunctions) -> None:
    for name in _HY_INSPECT_FUNCTION_NAMES:
        setattr(inspect, name, getattr(fns, name))


def py_findsource(obj: ta.Any) -> tuple[list[str], int]:
    return _get_originals().findsource(obj)


def py_getcomments(obj: ta.Any) -> str | None:
    return _get_originals().getcomments(obj)


def py_getfile(obj: ta.Any) -> str:
    return _get_originals().getfile(obj)


def py_getsource(obj: ta.Any) -> str:
    return _get_originals().getsource(obj)


def py_getsourcelines(obj: ta.Any) -> tuple[list[str], int]:
    return _get_originals().getsourcelines(obj)


##


def getfile(object: ta.Any) -> str:
    """Work out which source or compiled file an object was defined in."""

    obj = object

    if is_lazy(obj) or is_expression(obj):
        filename = getattr(obj, 'filename', None)
        if filename and filename != '<string>':
            return filename

        # Python's `inspect.getfile` raises OSError when there's no `__file__`.
        raise OSError('source code not available')

    try:
        return py_getfile(obj)
    except TypeError:
        # Python's `inspect.getfile` raises TypeError for unhandled types.
        raise TypeError(
            'module, class, method, function, traceback, frame, code, Expression or Lazy object was expected, got '
            f'{type(obj).__name__}',
        ) from None


def findsource(object: ta.Any) -> tuple[list[str], int]:
    """
    Return the entire source file and starting line number for an object, deferring to the original
    `inspect.findsource` for non-Hy objects.

    The argument may be a module, class, method, function, traceback, frame, code, Lazy or Expression object. The
    source code is returned as a list of all the lines in the file and the line number indexes a line in that list. An
    OSError is raised if the source code cannot be retrieved.
    """

    obj = object

    file = getfile(obj)

    fname = inspect.getsourcefile(obj)
    if fname is None:
        raise OSError('source code not available')

    if is_expression(obj) or is_lazy(obj):
        if getattr(obj, 'start_line', None) is None:
            raise OSError('source code not available')
        return linecache.getlines(fname), obj.start_line

    # Other Hy objects are identified by their file extension.
    if not file.endswith('.hy') or inspect.isframe(obj):
        return py_findsource(obj)

    module = inspect.getmodule(obj, fname)
    lines = linecache.getlines(fname, module.__dict__) if module else linecache.getlines(fname)

    if inspect.ismodule(obj):
        return lines, 0
    elif hasattr(obj, '__code__') and hasattr(obj.__code__, 'co_firstlineno'):
        # `co_firstlineno` is 1-based, the returned line number is an index into `lines`.
        return lines, obj.__code__.co_firstlineno - 1
    elif inspect.iscode(obj):
        return lines, obj.co_firstlineno - 1
    elif inspect.isclass(obj):
        return py_findsource(obj)
    else:
        raise OSError('source code not available')


def _get_hy_comments(obj: ta.Any, lines: list[str], lnum: int) -> str | None:
    """Roughly follows the logic of `inspect.getcomments`, but for Hy comments."""

    if not lines:
        return None

    comments: list[str] = []

    if inspect.ismodule(obj) or is_expression(obj) or is_lazy(obj):
        # Skip a shebang, and then any textless comments.
        start = 1 if lines[0][:2] == '#!' else 0
        while start < len(lines) and set(lines[start].strip()) == {';'}:
            start += 1

        if not (start < len(lines) and lines[start].lstrip().startswith(';')):
            return None

        end = start
        while end < len(lines) and lines[end].lstrip().startswith(';'):
            comments.append(lines[end].expandtabs())
            end += 1

        return ''.join(comments)

    if not (0 < lnum < len(lines)):
        return None

    # Look for a comment block preceding the object, working upwards.
    end = lnum - 1
    while end >= 0 and lines[end].lstrip().startswith(';'):
        comments.append(lines[end].expandtabs().lstrip())
        end -= 1

    return ''.join(reversed(comments)) if comments else None


def getcomments(object: ta.Any) -> str | None:
    """
    Get comments immediately preceding an object's source code, deferring to the original `inspect.getcomments` for
    non-Hy objects. Returns None when the source can't be found.
    """

    obj = object

    try:
        lines, lnum = findsource(obj)
    except (OSError, TypeError):
        return None

    if not getfile(obj).endswith('.hy'):
        return py_getcomments(obj)

    return _get_hy_comments(obj, lines, lnum)


def hy_getblock(lines: list[str]) -> list[str]:
    """
    Extract the lines of code corresponding to the first Hy form from the given list of lines.

    Built-in Hy reader macros are allowed as safe, since they do not execute code. User-defined reader macros could
    execute code, so we use `HySafeReader`.
    """

    try:
        form = read(''.join(lines), reader=HySafeReader())
    except HySyntaxError as e:
        raise e from None

    return lines[:form.end_line]


def getsourcelines(object: ta.Any) -> tuple[list[str], int]:
    """
    Return a list of source lines and starting line number for a Hy or python object, deferring to the original
    `inspect.getsourcelines` for non-Hy objects.

    The argument may be a module, class, method, function, traceback, frame, code, Lazy or Expression object. The source
    code is returned as a list of the lines corresponding to the object and the line number indicates where in the
    original source file the first line of code was found. An OSError is raised if the source code cannot be retrieved.
    """

    obj = inspect.unwrap(object)
    lines, lnum = findsource(obj)

    if inspect.istraceback(obj):
        obj = obj.tb_frame

    # For a module, or a frame that corresponds to a module, return all source lines.
    if inspect.ismodule(obj) or (inspect.isframe(obj) and obj.f_code.co_name == '<module>'):
        return lines, 0

    # `inspect.getblock` relies on `inspect.BlockFinder`, which assumes Python tokenization, so Hy objects need
    # `hy_getblock`.
    elif getfile(obj).endswith('.hy'):
        return hy_getblock(lines[lnum:]), lnum + 1

    else:
        return py_getsourcelines(obj)


def getsource(object: ta.Any) -> str:
    """
    Return the text of the source code for an object as a single string. The argument may be a module, class, method,
    function, traceback, frame, or code object. An OSError is raised if the source code cannot be retrieved.
    """

    return ''.join(getsourcelines(object)[0])


##


def is_installed() -> bool:
    return hasattr(inspect, _HY_INSPECT_ORIGINALS_ATTR)


def install() -> None:
    """
    Monkey-patch the source-inspecting functions of :mod:`inspect` to be Hy-aware. This is global interpreter state, and
    is done as part of installing the global runtime - see :mod:`.globalruntime`.
    """

    if is_installed():
        return

    setattr(inspect, _HY_INSPECT_ORIGINALS_ATTR, _get_originals())

    _set_inspect_functions(_HyInspectFunctions(
        findsource=findsource,
        getcomments=getcomments,
        getfile=getfile,
        getsource=getsource,
        getsourcelines=getsourcelines,
    ))


def uninstall() -> None:
    if (o := getattr(inspect, _HY_INSPECT_ORIGINALS_ATTR, None)) is None:
        return

    _set_inspect_functions(o)
    delattr(inspect, _HY_INSPECT_ORIGINALS_ATTR)
