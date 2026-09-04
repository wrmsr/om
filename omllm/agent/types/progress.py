import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True)
class ToolProgressUpdate(
    lang.Abstract,
    lang.PackageSealed,
    sealed_package='.'.join(__package__.split('.')[:2]),
):
    """What a running tool has to say before it is done. For display only: it never reaches the model."""


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class OutputToolProgressUpdate(ToolProgressUpdate):
    text: str

    _: dc.KW_ONLY

    # Which of the tool's output streams the text came from, for tools with more than one.
    stream: ta.Literal['stdout', 'stderr'] | None = None


##


class ToolProgressSink(lang.Abstract):
    """Where a running tool reports progress. Reached through its ToolContext, which carries one when anyone listens."""

    @abc.abstractmethod
    def report(self, update: ToolProgressUpdate) -> ta.Awaitable[None]:
        raise NotImplementedError
