# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
import dataclasses as dc
import enum
import typing as ta

from ....lite.namespaces import NamespaceClass
from ..core import IoPipeline
from ..core import IoPipelineMessages
from ..core import IoPipelineMetadata
from ..errors import AbortedIoPipelineError
from ..errors import IoPipelineError


IoPipelineMultiplexStreamKey = ta.Hashable  # ta.TypeAlias

IoPipelineMultiplexStreamOrigin = ta.Literal['local', 'remote']  # ta.TypeAlias

IoPipelineMultiplexFlowControlScope = ta.Literal['stream', 'connection']  # ta.TypeAlias


##


class IoPipelineMultiplexStreamState(enum.Enum):
    """
    The reported lifecycle state of a stream, derived from its two half states and any terminal outcome.

    ENDED means both directions have ended their ordinary output but the stream is not yet closed - for example while a
    protocol still awaits its close handshake, or while typed messages may still follow end-of-data.
    """

    OPENING = 'opening'
    OPEN = 'open'
    HALF_CLOSED_LOCAL = 'half_closed_local'
    HALF_CLOSED_REMOTE = 'half_closed_remote'
    ENDED = 'ended'

    CLOSED = 'closed'
    RESET = 'reset'
    REFUSED = 'refused'


TERMINAL_IO_PIPELINE_MULTIPLEX_STREAM_STATES: ta.FrozenSet[IoPipelineMultiplexStreamState] = frozenset([
    IoPipelineMultiplexStreamState.CLOSED,
    IoPipelineMultiplexStreamState.RESET,
    IoPipelineMultiplexStreamState.REFUSED,
])


##


class MultiplexIoPipelineError(IoPipelineError):
    pass


class StreamStateMultiplexIoPipelineError(MultiplexIoPipelineError):
    """An operation was attempted in a stream state which does not permit it."""


class UnknownStreamMultiplexIoPipelineError(MultiplexIoPipelineError):
    pass


class DuplicateStreamMultiplexIoPipelineError(MultiplexIoPipelineError):
    pass


class StreamLimitMultiplexIoPipelineError(MultiplexIoPipelineError):
    """Opening a stream would exceed the concurrent stream limit for its origin."""


class StreamRefusedMultiplexIoPipelineError(MultiplexIoPipelineError):
    def __init__(self, reason: ta.Any = None) -> None:
        super().__init__(reason)

        self.reason = reason


class StreamResetMultiplexIoPipelineError(MultiplexIoPipelineError, AbortedIoPipelineError):
    def __init__(self, reason: ta.Any = None, *, by: ta.Optional[IoPipelineMultiplexStreamOrigin] = None) -> None:
        super().__init__(reason, by)

        self.reason = reason
        self.by = by


class StreamTruncatedMultiplexIoPipelineError(MultiplexIoPipelineError, AbortedIoPipelineError):
    """The connection's input ended before the peer ended its output on the stream."""


class FlowControlMultiplexIoPipelineError(MultiplexIoPipelineError):
    """The peer sent more flow-controlled input than the advertised credit allowed."""

    def __init__(
            self,
            scope: IoPipelineMultiplexFlowControlScope,
            key: ta.Optional[IoPipelineMultiplexStreamKey] = None,
    ) -> None:
        super().__init__(scope, key)

        self.scope = scope
        self.key = key


class InputLimitMultiplexIoPipelineError(MultiplexIoPipelineError):
    """Too many uncontrolled inbound items are queued for a stream."""


class ControlOutputLimitMultiplexIoPipelineError(MultiplexIoPipelineError):
    """Control output kept accumulating while the connection's output was paused."""


class UnclaimedOutputMultiplexIoPipelineError(MultiplexIoPipelineError):
    """A stream's pipeline produced a message which the protocol adapter did not claim."""

    def __init__(self, msg: ta.Any) -> None:
        super().__init__(msg)

        self.msg = msg


class ConnectionClosedMultiplexIoPipelineError(MultiplexIoPipelineError, AbortedIoPipelineError):
    """The multiplexed connection ended, or the multiplexer was removed, before the stream finished."""


##


@dc.dataclass(frozen=True)
class IoPipelineMultiplexStreamOpening:
    """Describes a stream being opened, as given to a stream spec factory."""

    key: IoPipelineMultiplexStreamKey
    origin: IoPipelineMultiplexStreamOrigin

    # Protocol-specific opening information, opaque to the core.
    info: ta.Any = None


@dc.dataclass(frozen=True)
class IoPipelineMultiplexRefusal:
    """Returned by a stream spec factory to refuse a stream."""

    reason: ta.Any = None


MultiplexStreamSpecFactory = ta.Callable[  # ta.TypeAlias  # om-amalg-typing-no-move
    [
        IoPipelineMultiplexStreamOpening,
    ],
    ta.Union[
        IoPipeline.Spec,
        IoPipelineMultiplexRefusal,
    ],
]


@ta.final
class IoPipelineMultiplexStreamMetadata(IoPipelineMetadata):
    """Attached to each stream's child pipeline."""

    def __init__(self, opening: IoPipelineMultiplexStreamOpening) -> None:
        super().__init__()

        self._opening = opening

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._opening!r})'

    @property
    def opening(self) -> IoPipelineMultiplexStreamOpening:
        return self._opening

    @property
    def key(self) -> IoPipelineMultiplexStreamKey:
        return self._opening.key

    @property
    def origin(self) -> IoPipelineMultiplexStreamOrigin:
        return self._opening.origin

    @property
    def info(self) -> ta.Any:
        return self._opening.info


##


class IoPipelineMultiplexMessages(NamespaceClass):
    @ta.final
    @dc.dataclass(frozen=True, eq=False)
    class OpenStream(IoPipelineMessages.Completable['IoPipelineMultiplexOpenedStream'], IoPipelineMessages.AfterFinalInput):  # noqa
        """
        Requests a locally opened stream running a child pipeline built from `spec`.

        Fed to the multiplexing handler, inbound from a handler outside it or outbound from a handler inside it (or from
        outside the pipeline with `IoPipeline.feed_in_to`). Completes with a `MultiplexOpenedStream` once the stream is
        established, or fails - for example with `StreamRefusedMultiplexError` or `StreamLimitMultiplexError`.
        """

        spec: IoPipeline.Spec
        info: ta.Any = None

        def __repr__(self) -> str:
            return f'{type(self).__name__}@{id(self):x}({self.info!r})'

    @ta.final
    @dc.dataclass(frozen=True)
    class FeedStream(IoPipelineMessages.AfterFinalInput):
        """
        Feeds `msgs` into a stream's pipeline at its boundary - as a driver's `enqueue` feeds a top-level pipeline,
        bypassing the stream's input flow - during a turn of the multiplexing handler. Fed like OpenStream. Ignored if
        the stream has no running pipeline.
        """

        key: IoPipelineMultiplexStreamKey
        msgs: ta.Sequence[ta.Any]

    @ta.final
    @dc.dataclass(frozen=True)
    class Shutdown(IoPipelineMessages.AfterFinalInput):
        """
        Requests a graceful shutdown of the multiplexed connection: no new streams, existing ones run to completion,
        then the connection's output is finished. Fed like OpenStream; the protocol adapter may announce it to the peer.
        """


@ta.final
@dc.dataclass(frozen=True)
class IoPipelineMultiplexOpenedStream:
    key: IoPipelineMultiplexStreamKey
    pipeline: IoPipeline
