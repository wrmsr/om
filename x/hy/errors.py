import contextlib
import importlib.util
import os
import re
import sys
import traceback
import types
import typing as ta

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


class HyLanguageError(HyError):
    """
    Errors caused by invalid use of the Hy language.

    This, and any errors inheriting from this, are user-facing.
    """

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
        Args:
            message (str): The message to display for this error.
            expression (Optional[Object]): The Hy expression generating this error.
            filename (Optional[str]): The filename for the source code generating this error.
                Expression-provided information will take precedence of this value. Defaults to `None`.
            source (Optional[str]): The actual source code generating this error.  Expression-provided
                information will take precedence of this value. Defaults to `None`.
            lineno (int): The line number of the error.  Expression-provided information will
                take precedence of this value. Defaults to `1`.
            colno (int): The column number of the error.  Expression-provided information
                will take precedence of this value. Defaults to `1`.
        """

        self.msg = message
        self.compute_lineinfo(expression, filename, source, lineno, colno)

        if issubclass(type(self), SyntaxError):
            syntax_error_args = (self.filename, self.lineno, self.offset, self.text)
            super().__init__(message, syntax_error_args)
        else:
            super().__init__(message)

    def compute_lineinfo(
            self,
            expression: Object | None,
            filename: str | None,
            source: str | None,
            lineno: int,
            colno: int,
    ) -> None:
        # NOTE: We use `SyntaxError`'s field names (i.e. `text`, `offset`, `msg`) for compatibility and print-outs.
        self.text = getattr(expression, 'source', source)
        self.filename = getattr(expression, 'filename', filename)

        if self.text:
            lines = self.text.splitlines()

            self.lineno = getattr(expression, 'start_line', lineno)
            self.offset = getattr(expression, 'start_column', colno)
            end_line = getattr(expression, 'end_line', self.lineno)

            # Trim the source down to the essentials.
            self.text = '\n'.join(lines[self.lineno - 1: end_line])

        else:
            # We could attempt to extract the source given a filename, but we don't.
            self.lineno = lineno
            self.offset = colno

    def __str__(self) -> str:
        """Provide an exception message that includes SyntaxError-like source line information when available."""

        # Syntax errors are special and annotate the traceback (instead of what we would do in the message that follows
        # the traceback).
        if isinstance(self, SyntaxError):
            return super().__str__()
        # When there isn't extra source information, use the normal message.
        elif not self.text:
            return super().__str__()

        # Re-purpose Python's builtin syntax error formatting.
        output = traceback.format_exception_only(
            SyntaxError,
            SyntaxError(self.msg, (self.filename, self.lineno, self.offset, self.text)),
        )

        arrow_idx, _ = next(
            ((i, x) for i, x in enumerate(output) if set(x.strip()) == {'^'}),
            (None, None),
        )
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
    Errors arising during the use of `require`

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
    """Error during the Lexing of a Hython expression."""


class HyWrapperError(HyError, TypeError):
    """
    Errors caused by language model object wrapping.

    These can be caused by improper user-level use of a macro, so they're not really "internal".  If they arise due to
    anything else, they're an internal/compiler problem, though.
    """


def _module_filter_name(module_name: str) -> str | None:
    try:
        module_name = importlib.util.resolve_name(module_name, __package__)
        spec = importlib.util.find_spec(module_name)
        if not spec:
            return None

        compiler_loader = spec.loader
        if not compiler_loader:
            return None

        get_filename = getattr(compiler_loader, 'get_filename', None)
        if get_filename is None:
            return None
        filename = get_filename(module_name)
        if not filename:
            return None

        if getattr(compiler_loader, 'is_package', lambda _: False)(module_name):
            # Use the package directory (e.g. instead of `.../__init__.py`) so that we can filter all modules in a
            # package.
            return os.path.dirname(filename)
        else:
            # Normalize filename endings, because tracebacks will use `pyc` when the loader says `py`.
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
                '.cmdline',
                '.__main__',
                '.repl',
                '.reader.parser',
                '.globalruntime',
                '.importing',
                '.runtime',
                '.compat',
                '.macros',
                '.models',
                '.core.result_macros',
            ],
        )
        if m is not None
    }

    # We can't derive these easily from just their module names due to missing magic attributes in internal importlib
    # modules
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
    Produce exceptions print-outs with all frames originating from the modules in `_tb_hidden_modules` filtered out.

    The frames are actually filtered by each module's filename and only when a subclass of `HyLanguageError` is emitted.

    This does not remove the frames from the actual tracebacks, so debugging will show everything.
    """

    hidden_modules = _tb_hidden_modules()

    # frame = (filename, line number, function name*, text)
    new_tb = []
    for frame in traceback.extract_tb(exc_traceback):
        if not (
            frame[0].replace('.pyc', '.py') in hidden_modules
            or os.path.dirname(frame[0]) in hidden_modules
            or os.path.basename(os.path.dirname(frame[0])) == 'hy.exe'
        ):
            new_tb += [frame]

    lines = traceback.format_list(new_tb)

    lines.insert(0, 'Traceback (most recent call last):\n')

    lines.extend(traceback.format_exception_only(exc_type, exc_value))
    output = ''.join(lines)

    return output


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
        return sys.__excepthook__(exc_type, exc_value, exc_traceback)
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
        hy_exc_handler(exc_type, exc_value, exc_traceback, show_internal_errors=show_internal_errors)

    current_hook = sys.excepthook
    sys.excepthook = hook
    try:
        yield
    finally:
        sys.excepthook = current_hook
