# ruff: noqa: SLF001
import typing as ta

from ..errors import HySyntaxError


if ta.TYPE_CHECKING:
    from .reader import Reader


##


class LexException(HySyntaxError):  # noqa: N818
    @classmethod
    def from_reader(cls, message: str, reader: Reader) -> ta.Self:
        """Create an exception located at the last non-whitespace character `reader` has consumed."""

        lineno, colno = reader._eof_tracker
        return cls(
            message,
            filename=reader._filename,
            source=reader._source,
            lineno=lineno,
            colno=colno,
        )


class PrematureEndOfInput(LexException):
    """Raised when input ends unexpectedly during parsing."""

    __module__ = __package__.rpartition('.')[0]
