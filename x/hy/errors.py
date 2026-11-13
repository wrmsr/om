import contextlib
import importlib.util
import os
import re
import sys
import traceback
import types
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .compat import PYPY


if ta.TYPE_CHECKING:
    from .models import Object


##


class HyError(Exception):
    pass


class HyInternalError(HyError):
    """
    Unexpected errors occurring during compilation or parsing of Hy code.

    Errors sub-classing this are not intended to be user-facing, and will, hopefully, never be seen by users!
    """


@dc.dataclass(frozen=True)
class _HyLanguageErrorLocation:
    filename: str | None
    text: str | None
    lineno: int
    offset: int


def _compute_hy_language_error_location(
        expression: Object | None,
        *,
        filename: str | None,
        source: str | None,
        lineno: int,
        colno: int,
) -> _HyLanguageErrorLocation:
    text = getattr(expression, 'source', source)
    filename = getattr(expression, 'filename', filename)

    if not text:
        # We could attempt to extract the source given a filename, but we don't.
        return _HyLanguageErrorLocation(
            filename=filename,
            text=text,
            lineno=lineno,
            offset=colno,
        )

    lineno = getattr(expression, 'start_line', lineno)
    offset = getattr(expression, 'start_column', colno)
    end_line = getattr(expression, 'end_line', lineno)

    # Trim the source down to the essentials.
    text = '\n'.join(text.splitlines()[lineno - 1:end_line])

    return _HyLanguageErrorLocation(
        filename=filename,
        text=text,
        lineno=lineno,
        offset=offset,
    )


class HyLanguageError(HyError):
    """
    Errors caused by invalid use of the Hy language.

    This, and any errors inheriting from this, are user-facing.
    """

    # These use `SyntaxError`'s field names and types, for compatibility with it and its print-outs.
    msg: str
    filename: str | None
    text: str | None
    lineno: int | None
    offset: int | None

    def __init__(
            self,
            message: str,
            expression: Object | None = None,
            filename: str | None = None,
            source: str | None = None,
            lineno: int = 1,
            colno: int = 1,
    ) -> None:
        """
        Information provided by `expression` (the Hy expression generating the error) takes precedence over the given
        `filename`, `source`, `lineno`, and `colno` of the code generating it.
        """

        loc = _compute_hy_language_error_location(
            expression,
            filename=filename,
            source=source,
            lineno=lineno,
            colno=colno,
        )

        if isinstance(self, SyntaxError):
            super().__init__(message, (loc.filename, loc.lineno, loc.offset, loc.text))
        else:
            super().__init__(message)

        self.msg = message
        self.filename = loc.filename
        self.text = loc.text
        self.lineno = loc.lineno
        self.offset = loc.offset

    def __str__(self) -> str:
        """Provide an exception message that includes SyntaxError-like source line information when available."""

        # Syntax errors are special and annotate the traceback (instead of what we would do in the message that follows
        # the traceback). When there isn't extra source information, use the normal message.
        if isinstance(self, SyntaxError) or not self.text:
            return super().__str__()

        # Re-purpose Python's builtin syntax error formatting.
        output = traceback.format_exception_only(
            SyntaxError,
            SyntaxError(self.msg, (self.filename, self.lineno, self.offset, self.text)),
        )

        arrow_idx = next((i for i, x in enumerate(output) if set(x.strip()) == {'^'}), None)
        if arrow_idx:
            msg_idx = arrow_idx + 1
        else:
            msg_idx = next(i for i, x in enumerate(output) if x.startswith('SyntaxError: '))

        # Get rid of erroneous error-type label.
        output[msg_idx] = re.sub('^SyntaxError: ', '', output[msg_idx])

        # This resulting string will come after a "<class-name>:" prompt, so put it down a line.
        output.insert(0, '\n')

        return ''.join(output)


class HyCompileError(HyInternalError):
    """Unexpected errors occurring within the compiler."""


class HyTypeError(HyLanguageError, TypeError):
    """TypeError occurring during the normal use of Hy."""


class HyRequireError(HyLanguageError):
    """
    Errors arising during the use of `require`.

    This, and any errors inheriting from this, are user-facing.
    """


class HyMacroExpansionError(HyLanguageError):
    """
    Errors caused by invalid use of Hy macros.

    This, and any errors inheriting from this, are user-facing.
    """


class HyEvalError(HyLanguageError):
    """
    Errors occurring during code evaluation at compile-time.

    These errors distinguish unexpected errors within the compilation process (i.e. `HyInternalError`s) from unrelated
    errors in user code evaluated by the compiler (e.g. in `eval-and-compile`).

    This, and any errors inheriting from this, are user-facing.
    """


class HySyntaxError(HyLanguageError, SyntaxError):
    """Error during the lexing of a Hy expression."""


class HyWrapperError(HyError, TypeError):
    """
    Errors caused by language model object wrapping.

    These can be caused by improper user-level use of a macro, so they're not really "internal". If they arise due to
    anything else, they're an internal/compiler problem, though.
    """


## Traceback filtering


def _module_filter_name(module_name: str) -> str | None:
    try:
        module_name = importlib.util.resolve_name(module_name, __package__)
        if (spec := importlib.util.find_spec(module_name)) is None or (loader := spec.loader) is None:
            return None

        get_filename = getattr(loader, 'get_filename', None)
        if get_filename is None or not (filename := get_filename(module_name)):
            return None

        if getattr(loader, 'is_package', lambda _: False)(module_name):
            # Use the package directory (rather than e.g. `.../__init__.py`) so that all modules in a package are
            # filtered.
            return os.path.dirname(filename)

        # Normalize filename endings, as tracebacks and loaders may disagree on `.py` vs `.pyc` (frame filenames are
        # normalized likewise).
        return filename.replace('.pyc', '.py')

    except Exception:  # noqa: BLE001
        return None


@lang.cached_function
def _tb_hidden_modules() -> frozenset[str]:
    hidden = {
        m
        for m in map(
            _module_filter_name,
            [
                '.compiler',
                '.reader',
                '.cli',
                '.__main__',
                '.repl',
                '.globalruntime',
                '.importing',
                '.runtime',
                '.compat',
                '.macros',
                '.models',
                '.core.specials',
            ],
        )
        if m is not None
    }

    # We can't derive these easily from just their module names due to missing magic attributes in internal importlib
    # modules.
    hidden.update(
        f'<builtin>/frozen {x}' if PYPY else f'<frozen {x}>'
        for x in ('importlib._bootstrap', 'importlib._bootstrap_external')
    )

    return frozenset(hidden)


def hy_exc_filter(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: types.TracebackType | None,
) -> str:
    """
    Produce exception print-outs with all frames originating from the modules in `_tb_hidden_modules` filtered out.

    The frames are filtered by each module's filename. This does not remove the frames from the actual tracebacks, so
    debugging will show everything.
    """

    hidden_modules = _tb_hidden_modules()

    frames = [
        frame
        for frame in traceback.extract_tb(exc_traceback)
        if not (
            frame.filename.replace('.pyc', '.py') in hidden_modules or
            os.path.dirname(frame.filename) in hidden_modules or
            os.path.basename(os.path.dirname(frame.filename)) == 'hy.exe'
        )
    ]

    return ''.join([
        'Traceback (most recent call last):\n',
        *traceback.format_list(frames),
        *traceback.format_exception_only(exc_type, exc_value),
    ])


def hy_exc_handler(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: types.TracebackType | None,
        *,
        show_internal_errors: bool = False,
) -> None:
    """
    A `sys.excepthook` handler that uses `hy_exc_filter` to remove internal Hy frames from a traceback print-out, unless
    `show_internal_errors` is true.
    """

    if show_internal_errors:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    try:
        output = hy_exc_filter(exc_type, exc_value, exc_traceback)
        sys.stderr.write(output)
        sys.stderr.flush()
    except Exception:  # noqa: BLE001
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


@contextlib.contextmanager
def filtered_hy_exceptions(*, show_internal_errors: bool = False) -> ta.Iterator[None]:
    """Temporarily apply a `sys.excepthook` that filters Hy internal frames from tracebacks."""

    def hook(
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_traceback: types.TracebackType | None,
    ) -> None:
        hy_exc_handler(
            exc_type,
            exc_value,
            exc_traceback,
            show_internal_errors=show_internal_errors,
        )

    current_hook = sys.excepthook
    sys.excepthook = hook
    try:
        yield
    finally:
        sys.excepthook = current_hook
