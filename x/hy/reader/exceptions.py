# ruff: noqa: SLF001
import typing as ta

from ..errors import HySyntaxError


if ta.TYPE_CHECKING:
    from .reader import Reader


##


class LexException(HySyntaxError):  # noqa: N818
    @classmethod
    def from_reader(cls, message: str, reader: Reader) -> ta.Self:
        return cls(
            message,
            None,
            reader._filename,
            reader._source,
            *reader._eof_tracker,
        )


class PrematureEndOfInput(LexException):
    """Raised when input ends unexpectedly during parsing."""

    __module__ = __package__.rpartition('.')[0]
