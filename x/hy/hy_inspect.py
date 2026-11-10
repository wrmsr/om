# ruff: noqa: A002
"""
Get useful information from live Hy or Python objects.

This module provides Hy compatibility with CPython's inspect module. Within Hy, Hy macros are supported via Hy's
`get_macro` macro, for example `(inspect.getsource (get-macro get-macro))`. The Hy-specific functionality is
monkey-patched into `inspect` at run-time.
"""
import inspect
import linecache
import typing as ta

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
        """Skip over undefined reader macros so that no code is executed at read time."""

        try:
            return super().tag_dispatch(key)
        except LexException:
            return None


def is_expression(obj: object) -> ta.TypeIs[Expression]:
    """Check if object is a Hy Expression instance."""

    return isinstance(obj, Expression)


def is_lazy(obj: object) -> ta.TypeIs[Lazy]:
    """Check if object is a Hy Lazy instance."""

    return isinstance(obj, Lazy)


def getfile(object: ta.Any) -> str:
    """Work out which source or compiled file an object was defined in."""

    obj = object

    if is_lazy(obj) or is_expression(obj):
        filename = getattr(obj, 'filename', None)
        if filename and filename != '<string>':
            return filename
        else:
            # python's inspect.getfile raises OSError where there's no __file__
            raise OSError('source code not available')

    try:
        return py_getfile(obj)
    except TypeError:
        # python's inspect.getfile raises TypeError for unhandled types
        raise TypeError(
            'module, class, method, function, traceback, frame, '
            'code, Expression or Lazy object was expected, got '
            f'{type(obj).__name__}',
        ) from None


def findsource(object: ta.Any) -> tuple[list[str], int]:
    """
    Return the entire source file and starting line number for an object.

    First looks for Hy source, otherwise defers to the original `inspect.findsource`. The argument may be a module,
    class, method, function, traceback, frame, code, Lazy or Expression object. The source code is returned as a list of
    all the lines in the file and the line number indexes a line in that list. An OSError is raised if the source code
    cannot be retrieved.
    """

    obj = object

    if getfile(obj) is None:
        raise OSError('source code not available')

    fname = inspect.getsourcefile(obj)
    if fname is None:
        raise OSError('source code not available')

    if is_expression(obj) or is_lazy(obj):
        if getattr(obj, 'start_line', None) is None:
            raise OSError('source code not available')
        return (linecache.getlines(fname), obj.start_line)
    elif getfile(obj).endswith('.hy') and not inspect.isframe(obj):
        # We identify other Hy objects from the file extension.
        module = inspect.getmodule(obj, fname)
        # List of source code lines.
        lines = (
            linecache.getlines(fname, module.__dict__)
            if module
            else linecache.getlines(fname)
        )
        if inspect.ismodule(obj):
            return (lines, 0)
        # Some objects already have the information we need.
        elif hasattr(obj, '__code__') and hasattr(obj.__code__, 'co_firstlineno'):
            # This indexing offset is actually correct.
            return (lines, obj.__code__.co_firstlineno - 1)
        elif inspect.iscode(obj):
            return (lines, obj.co_firstlineno - 1)
        elif inspect.isclass(obj):
            return py_findsource(obj)
        else:
            raise OSError('source code not available')
    else:
        # Non-Hy object
        return py_findsource(obj)


def getcomments(object: ta.Any) -> str | None:
    """
    Get comments immediately preceding an object's source code.

    First checks for Hy source, otherwise defers to the original `inspect.getcomments`. Returns None when the source
    can't be found.
    """

    obj = object

    try:
        lines, lnum = findsource(obj)
    except (OSError, TypeError):
        # Return None when the source can't be found.
        return None

    if getfile(obj).endswith('.hy'):
        # Roughly follows the logic of inspect.getcomments, but for Hy comments
        if not lines:
            return None

        comments = []
        if inspect.ismodule(obj) or is_expression(obj) or is_lazy(obj):
            # Remove shebang.
            start = 1 if lines and lines[0][:2] == '#!' else 0
            # Remove preceding empty lines and textless comments.
            while start < len(lines) and set(lines[start].strip()) == {';'}:
                start += 1
            if start < len(lines) and lines[start].lstrip().startswith(';'):
                end = start
                while end < len(lines) and lines[end].lstrip().startswith(';'):
                    comments.append(lines[end].expandtabs())
                    end += 1
                return ''.join(comments)
            else:
                return None
        # Look for a comment block preceding the object
        elif lnum > 0 and lnum < len(lines):
            # Look for comments above the object and work up.
            end = lnum - 1
            while end >= 0 and lines[end].lstrip().startswith(';'):
                comments = [lines[end].expandtabs().lstrip(), *comments]
                end -= 1
            return ''.join(comments) if comments else None
        else:
            return None

    else:
        # Non-Hy object
        return py_getcomments(obj)


def getsource(object: ta.Any) -> str:
    """
    Return the text of the source code for an object.

    The argument may be a module, class, method, function, traceback, frame, or code object.  The source code is
    returned as a single string.  An OSError is raised if the source code cannot be retrieved.
    """

    obj = object

    return ''.join(getsourcelines(obj)[0])


def hy_getblock(lines: list[str]) -> list[str]:
    """
    Extract the lines of code corresponding to the first Hy form from the given list of lines.

    Built-in Hy reader macros are allowed as safe, since they do not execute code. User-defined reader macros could
    execute code, so we use `HySafeReader`.
    """

    # Read the first form and use its attributes
    try:
        form = read(''.join(lines), reader=HySafeReader())
    except HySyntaxError as e:
        raise e from None
    return lines[: form.end_line]


def getsourcelines(object: ta.Any) -> tuple[list[str], int]:
    """
    Return a list of source lines and starting line number for a Hy or python object.

    First checks for Hy source, otherwise defers to the original `inspect.getsourcelines`.

    The argument may be a module, class, method, function, traceback, frame, code, Lazy or Expression object. The source
    code is returned as a list of the lines corresponding to the object and the line number indicates where in the
    original source file the first line of code was found. An OSError is raised if the source code cannot be retrieved.
    """

    obj = object

    obj = inspect.unwrap(obj)
    lines, lnum = findsource(obj)

    if inspect.istraceback(obj):
        obj = obj.tb_frame

    # For module or frame that corresponds to module, return all source lines.
    if inspect.ismodule(obj) or (
        inspect.isframe(obj) and obj.f_code.co_name == '<module>'
    ):
        return lines, 0

    # Almost everything already works with python's inspect. The inspect.getblock function relies on inspect.BlockFinder
    # which assumes python tokenization. So deal with this as a special case using hy_getblock.
    elif getfile(obj).endswith('.hy'):
        return hy_getblock(lines[lnum:]), lnum + 1
    else:
        # Non-Hy object
        return py_getsourcelines(obj)


if hasattr(inspect, '_hy_originals'):
    # Retrieve saved versions of `inspect`'s original functions.
    (
        py_findsource,
        py_getcomments,
        py_getfile,
        py_getsource,
        py_getsourcelines,
    ) = getattr(inspect, '_hy_originals')
else:
    # Save the originals and then monkey-patch.
    (
        py_findsource,
        py_getcomments,
        py_getfile,
        py_getsource,
        py_getsourcelines,
    ) = (
        inspect.findsource,
        inspect.getcomments,
        inspect.getfile,
        inspect.getsource,
        inspect.getsourcelines,
    )
    setattr(inspect, '_hy_originals', (
        py_findsource,
        py_getcomments,
        py_getfile,
        py_getsource,
        py_getsourcelines,
    ))
    (
        inspect.findsource,
        inspect.getcomments,
        inspect.getfile,
        inspect.getsource,
        inspect.getsourcelines,
    ) = (
        findsource,
        getcomments,
        getfile,
        getsource,
        getsourcelines,
    )
