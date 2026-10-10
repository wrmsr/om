# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""
The seam between the multiplexing core and a concrete wire protocol.

The core tells the adapter what to emit by asking it to encode: control output (opens, acceptances, refusals, resets,
credit grants) which bypasses stream queues and is never gated by credit, backlog, or connection writability; and
stream-ordered output (data, typed messages, end-of-output, finish) which keeps its place in its stream. The adapter
tells the core what arrived by calling a `MultiplexConnection` while handling the connection's inbound messages.

A `MultiplexConnection` is valid only for the duration of the adapter call it was passed to and must not be retained.
"""
import abc
import dataclasses as dc
import typing as ta

from ....lite.abstract import Abstract
from ...streambufs.segmented import SegmentedByteStreamBufferView
from .streams import UNSET
from .streams import IoPipelineMultiplexStream
from .streams import IoPipelineMultiplexStreamStats
from .types import IoPipelineMultiplexStreamKey
from .types import IoPipelineMultiplexStreamOpening


##


@ta.final
@dc.dataclass(frozen=True)
class IoPipelineMultiplexStreamParams:
    """What the adapter decides about a stream it is opening locally."""

    key: IoPipelineMultiplexStreamKey

    # Initial receive window advertised to the peer.
    recv_window: int

    # Initial send credit, if already known (implicit-open protocols); otherwise granted on confirmation.
    send_credit: int = 0

    # Whether the peer must confirm or refuse the stream before it is established.
    explicit: bool = True

    # The stream's share of the connection's output relative to the other streams', for the output scheduler.
    weight: int = 1


@ta.final
@dc.dataclass(frozen=True)
class IoPipelineMultiplexConnectionStats:
    """Read-only facts a protocol layer may use for its own defenses."""

    streams: IoPipelineMultiplexStreamStats

    # Control output emitted since the connection's output last became writable while it was paused.
    control_during_pause: int

    # Per stream: (queued flow-controlled input cost, queued uncontrolled input items).
    queued_input: ta.Mapping[IoPipelineMultiplexStreamKey, ta.Tuple[int, int]]


class IoPipelineMultiplexConnection(Abstract):
    """The multiplexing core as seen by its protocol adapter, for the duration of one adapter call."""

    #
    # inspection

    @abc.abstractmethod
    def get(self, key: IoPipelineMultiplexStreamKey) -> ta.Optional[IoPipelineMultiplexStream]:
        raise NotImplementedError

    @abc.abstractmethod
    def streams(self) -> ta.Sequence[IoPipelineMultiplexStream]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def stats(self) -> IoPipelineMultiplexConnectionStats:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def accepting(self) -> bool:
        """Whether new streams may currently be opened, in either direction."""

        raise NotImplementedError

    #
    # control output

    @abc.abstractmethod
    def send(self, *msgs: ta.Any) -> None:
        """Queues control output, emitted ahead of stream output and never gated by credit or writability."""

        raise NotImplementedError

    #
    # inbound stream events

    @abc.abstractmethod
    def open_remote(
            self,
            key: IoPipelineMultiplexStreamKey,
            info: ta.Any = None,
            *,
            recv_window: int,
            send_credit: int = 0,
            weight: int = 1,
    ) -> ta.Optional[IoPipelineMultiplexStream]:
        """
        A peer-opened stream. Returns the stream if it is accepted - by limits, shutdown state, and the stream spec
        factory (which may refuse it, or raise) - or None if it was refused, in which case the refusal has been encoded
        and queued.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def confirm(self, key: IoPipelineMultiplexStreamKey, *, send_credit: int = 0) -> None:
        """The peer confirmed a locally opened stream."""

        raise NotImplementedError

    @abc.abstractmethod
    def refuse(self, key: IoPipelineMultiplexStreamKey, reason: ta.Any = None) -> None:
        """The peer refused a locally opened stream."""

        raise NotImplementedError

    @abc.abstractmethod
    def data(self, key: IoPipelineMultiplexStreamKey, data: ta.Any, *, cost: ta.Optional[int] = None) -> None:
        """
        Flow-controlled stream data, costing `cost` (default: its length). Raises FlowControlMultiplexError if it
        exceeds advertised credit and StreamStateMultiplexError if the stream cannot receive data; the adapter decides
        whether either is a stream or a connection error. Data for a stream which already ended - reset, closed, or
        refused, with frames still in flight - is counted against any connection-level window and dropped.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def discard(self, cost: int) -> None:
        """
        Counts flow-controlled input arriving for no stream - one already released, which the adapter remembers -
        against any connection-level window, and frees it. Raises FlowControlMultiplexError if it exceeds advertised
        connection credit.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def message(self, key: IoPipelineMultiplexStreamKey, msg: ta.Any, *, cost: int = 0) -> None:
        """
        A typed message for the stream, ordered with its data. A positive cost makes it flow-controlled. Raises
        InputLimitMultiplexError when too many uncontrolled items are queued for the stream.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def end(self, key: IoPipelineMultiplexStreamKey) -> None:
        """The peer ended its output on the stream. Its pipeline sees FinalInput after everything queued before it."""

        raise NotImplementedError

    @abc.abstractmethod
    def close(self, key: IoPipelineMultiplexStreamKey) -> None:
        """
        The stream is closed by protocol agreement - the peer will neither send nor receive more on it.

        If the local side has finished, the stream is released now. Otherwise its pipeline still receives everything
        already queued, followed by FinalInput, while any further output from it is discarded (fences other than
        FinalOutput failing with StreamResetMultiplexError); the stream is released once the pipeline finishes.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def reset(self, key: IoPipelineMultiplexStreamKey, reason: ta.Any = None) -> None:
        """The peer abortively terminated the stream."""

        raise NotImplementedError

    @abc.abstractmethod
    def grant(self, key: ta.Optional[IoPipelineMultiplexStreamKey], delta: int) -> None:
        """Send credit from the peer: for one stream, or for the connection when `key` is None. May be negative."""

        raise NotImplementedError

    @abc.abstractmethod
    def adjust_all(self, delta: int) -> None:
        """Shifts every stream's send credit at once, possibly negative."""

        raise NotImplementedError

    #
    # local actions

    @abc.abstractmethod
    def reset_local(self, key: IoPipelineMultiplexStreamKey, reason: ta.Any = None) -> None:
        """Abortively terminates a stream from this side, encoding and queueing the reset."""

        raise NotImplementedError

    @abc.abstractmethod
    def set_limits(
            self,
            *,
            max_local: ta.Optional[int] = UNSET,
            max_remote: ta.Optional[int] = UNSET,
    ) -> None:
        """Changes the concurrent stream limits; `UNSET` leaves one unchanged and None removes it."""

        raise NotImplementedError

    @abc.abstractmethod
    def set_weight(self, key: IoPipelineMultiplexStreamKey, weight: int) -> None:
        """Changes a stream's output scheduling weight (an HTTP/2 PRIORITY, say); applies from its next turn."""

        raise NotImplementedError

    @abc.abstractmethod
    def begin_shutdown(self) -> None:
        """
        Gracefully shuts the connection down: no new streams in either direction; existing ones run to completion;
        then the connection's own output is finished with FinalOutput.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def fail(self, exc: BaseException) -> None:
        """A connection-level failure: every stream is aborted with `exc` and the connection is finished."""

        raise NotImplementedError


##


class IoPipelineMultiplexAdapter(Abstract):
    """
    A concrete protocol's half of multiplexing.

    Everything that encodes returns a (possibly empty) sequence of messages to feed outbound from the multiplexing
    handler, for the handlers outside it to encode further.
    """

    #
    # inbound

    @abc.abstractmethod
    def inbound(self, conn: IoPipelineMultiplexConnection, msg: ta.Any) -> bool:
        """
        Handles one message arriving at the multiplexing handler from outside it - normally a decoded protocol frame -
        by calling `conn`. Returns False if the message is not the adapter's, which is then forwarded inward.
        """

        raise NotImplementedError

    #
    # local opens

    @abc.abstractmethod
    def open_local(self, conn: IoPipelineMultiplexConnection, info: ta.Any) -> IoPipelineMultiplexStreamParams:
        """Allocates a key and initial windows for a stream being opened locally."""

        raise NotImplementedError

    #
    # control output

    def encode_open(self, stream: IoPipelineMultiplexStream) -> ta.Sequence[ta.Any]:
        return ()

    def encode_accept(self, stream: IoPipelineMultiplexStream) -> ta.Sequence[ta.Any]:
        return ()

    def encode_refuse(self, opening: IoPipelineMultiplexStreamOpening, reason: ta.Any) -> ta.Sequence[ta.Any]:
        return ()

    def encode_reset(self, stream: IoPipelineMultiplexStream, reason: ta.Any) -> ta.Sequence[ta.Any]:
        return ()

    @abc.abstractmethod
    def encode_credit(self, stream: ta.Optional[IoPipelineMultiplexStream], amount: int) -> ta.Sequence[ta.Any]:
        """
        Advertises receive credit for a stream, or for the connection when `stream` is None.

        Returning nothing declines the grant: the credit stays unadvertised in the core's accounting and is offered
        again as more is consumed. The core offers grants for a stream whose local side has finished, since the peer
        may still be sending on it; a protocol which may send nothing more on such a stream (SSH after its CLOSE)
        declines them, one which may (HTTP/2 after END_STREAM) encodes them.
        """

        raise NotImplementedError

    #
    # stream-ordered output

    @abc.abstractmethod
    def encode_data(
            self,
            stream: IoPipelineMultiplexStream,
            data: SegmentedByteStreamBufferView,
    ) -> ta.Sequence[ta.Any]:
        raise NotImplementedError

    def encode_message(
            self,
            stream: IoPipelineMultiplexStream,
            msg: ta.Any,
    ) -> ta.Sequence[ta.Any]:
        raise TypeError(msg)

    def encode_end(self, stream: IoPipelineMultiplexStream) -> ta.Sequence[ta.Any]:
        """End of the stream's local output (its pipeline sent ShutdownOutput)."""

        return ()

    def encode_finish(self, stream: IoPipelineMultiplexStream) -> ta.Sequence[ta.Any]:
        """
        The stream's local endpoint finished (its pipeline sent FinalOutput) - `stream.local_ended` says whether
        end-of-output was already encoded.
        """

        return ()

    #
    # sizing and costs

    def max_data_unit(self, stream: IoPipelineMultiplexStream) -> int:
        """The most data bytes one emitted unit may carry."""

        return 16 * 1024

    def data_unit_overhead(self, stream: IoPipelineMultiplexStream) -> int:
        """Credit cost of a data unit beyond its length (padding, say)."""

        return 0

    def claim_output(self, stream: IoPipelineMultiplexStream, msg: ta.Any) -> bool:
        """Whether a non-byte message produced by a stream's pipeline is a valid typed message of this protocol."""

        return False

    def message_cost(self, stream: IoPipelineMultiplexStream, msg: ta.Any) -> int:
        """The flow-control cost of a claimed typed message; zero for uncontrolled messages."""

        return 0

    def split_message(
            self,
            stream: IoPipelineMultiplexStream,
            msg: ta.Any,
            max_cost: int,
    ) -> ta.Optional[ta.Tuple[ta.Any, ta.Any]]:
        """Splits a flow-controlled typed message into a head costing at most `max_cost` and a tail, if possible."""

        return None

    #
    # lifecycle hooks

    def on_stream_finished(self, conn: IoPipelineMultiplexConnection, stream: IoPipelineMultiplexStream) -> None:
        """
        After a stream's finish was emitted. The adapter may close the stream now (`conn.close`), reset it, or leave it
        awaiting the peer's close.
        """

    def on_stream_released(self, stream: IoPipelineMultiplexStream) -> None:
        """The stream left the table. A protocol which must absorb late frames for a closed key remembers it here."""

    def on_shutdown(self, conn: IoPipelineMultiplexConnection) -> None:
        """A local graceful shutdown was requested. The adapter may announce it to the peer before shutting down."""

        conn.begin_shutdown()

    def on_input_ended(self, conn: IoPipelineMultiplexConnection) -> None:
        """
        The connection's input ended. Streams whose peer had not ended its output have already been aborted with
        StreamTruncatedMultiplexError. By default the connection shuts down gracefully.
        """

        conn.begin_shutdown()

    def encode_connection_error(self, exc: BaseException) -> ta.Sequence[ta.Any]:
        """Control output announcing a connection-level failure (a GOAWAY, say), emitted before finishing."""

        return ()
