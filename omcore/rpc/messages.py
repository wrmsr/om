# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The two message vocabularies of the toolbox.

Envelopes are what crosses the wire: seven frozen dataclasses, symmetric between the two ends of a connection. Request
ids are opaque values scoped to the direction they were issued in, so the same id may be in flight independently in
both directions. Params and results are opaque: the envelope codec hands them to the wire value codec untouched, so they
must be whatever that codec can represent, which is what a serde sitting above the connection guarantees.

Session messages are the vocabulary between a connection (the code driving a pipeline driver) and the session handler
sitting innermost in its pipeline. Commands are fed inbound at the pipeline boundary via a driver's `enqueue`, pass
untouched through the byte-level handlers, and are consumed by the session. Events are fed outbound by the session and,
being unhandled by any driver, are returned to the connection from the driver's `next`.

Commands are marked `AfterFinalInput` so that responses to in-flight inbound requests may still be sent after the peer
half-closes its side of the transport.
"""
import dataclasses as dc
import typing as ta

from ..io.pipelines.core import IoPipelineMessages
from ..lite.abstract import Abstract
from ..lite.check import check
from ..lite.namespaces import NamespaceClass
from .errors import RpcProtocolError
from .errors import RpcRemoteErrorData


RpcResponseMessage = ta.Union['RpcResultMessage', 'RpcErrorMessage']  # ta.TypeAlias


##


class RpcUnspecified:
    """A sentinel type - the class itself is the value - for 'use the configured default', as distinct from None."""

    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError


##


class RpcEnvelope(Abstract):
    """Base class of everything which crosses the wire."""

    @staticmethod
    def _check_id(id: ta.Any) -> None:  # noqa
        # Ids key the sessions' bookkeeping, so one off the wire must be hashable: a list or mapping is a protocol
        # violation, not a crash.
        if id is None:
            raise RpcProtocolError('message id must not be None')
        try:
            hash(id)
        except TypeError:
            raise RpcProtocolError(f'message id must be hashable: {id!r}') from None


@dc.dataclass(frozen=True)
class RpcRequestMessage(RpcEnvelope):
    id: ta.Any
    method: str
    params: ta.Any = None

    def __post_init__(self) -> None:
        self._check_id(self.id)
        check.non_empty_str(self.method, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcResultMessage(RpcEnvelope):
    id: ta.Any
    result: ta.Any = None

    def __post_init__(self) -> None:
        self._check_id(self.id)


@dc.dataclass(frozen=True)
class RpcErrorMessage(RpcEnvelope):
    id: ta.Any
    error: RpcRemoteErrorData

    def __post_init__(self) -> None:
        self._check_id(self.id)
        check.isinstance(self.error, RpcRemoteErrorData, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcCancelMessage(RpcEnvelope):
    """Tells the peer this side no longer wants the response to one of its requests. Advisory: the peer need not act."""

    id: ta.Any

    def __post_init__(self) -> None:
        self._check_id(self.id)


@dc.dataclass(frozen=True)
class RpcNotificationMessage(RpcEnvelope):
    method: str
    params: ta.Any = None

    def __post_init__(self) -> None:
        check.non_empty_str(self.method, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcPingMessage(RpcEnvelope):
    """Answered with a pong carrying the same id by the receiving session itself, without involving its host."""

    id: ta.Any

    def __post_init__(self) -> None:
        self._check_id(self.id)


@dc.dataclass(frozen=True)
class RpcPongMessage(RpcEnvelope):
    id: ta.Any

    def __post_init__(self) -> None:
        self._check_id(self.id)


@dc.dataclass(frozen=True)
class RpcHelloMessage(RpcEnvelope):
    """
    A handshake greeting: opaque fields agreed between the peers, such as a protocol name, version, or instance id.
    Never sent by the session; only by an `RpcHandshakeIoPipelineHandler`, which also consumes the peer's.
    """

    fields: ta.Mapping[str, ta.Any]

    def __post_init__(self) -> None:
        if not isinstance(self.fields, ta.Mapping) or not all(isinstance(k, str) for k in self.fields):
            raise RpcProtocolError(f'hello fields must be a string-keyed mapping: {self.fields!r}')


##


class RpcInfoEvent(Abstract):
    """
    Marks an event an optional handler emits toward the host for whoever cares, such as a completed handshake. A
    connection which does not consume one passes it by quietly; any other event it does not recognize is a mistake, and
    warned of.
    """


##


class RpcSessionMessages(NamespaceClass):
    ##
    # commands: connection -> session

    class Command(
        IoPipelineMessages.NeverOutbound,
        IoPipelineMessages.AfterFinalInput,
        Abstract,
    ):
        pass

    @dc.dataclass(frozen=True)
    class SendRequest(Command):
        """
        Send a request and track its response. The request must already carry an id unique among this side's pending
        requests.

        A timeout of RpcUnspecified uses the session's default; None disables the timeout for this request.
        """

        request: RpcRequestMessage

        timeout_s: ta.Union[float, None, ta.Type[RpcUnspecified]] = RpcUnspecified

    @dc.dataclass(frozen=True)
    class SendNotification(Command):
        notification: RpcNotificationMessage

    @dc.dataclass(frozen=True)
    class SendResponse(Command):
        """Answer an in-flight inbound request. Exactly one response per inbound request is accepted."""

        response: RpcResponseMessage

    @dc.dataclass(frozen=True)
    class CancelRequest(Command):
        """
        Stop waiting for the response to a previously sent request. A late response is silently dropped.

        With `notify_peer` a cancel envelope is also sent, so the peer may stop handling it.
        """

        id: ta.Any

        notify_peer: bool = True

    @dc.dataclass(frozen=True)
    class SendPing(Command):
        """Send a ping and track its pong. The ping must carry an id unique among this side's pending pings."""

        ping: RpcPingMessage

        timeout_s: ta.Union[float, None, ta.Type[RpcUnspecified]] = RpcUnspecified

    @dc.dataclass(frozen=True)
    class Close(Command):
        """
        Close the session.

        A graceful close stops accepting new outbound requests, waits for pending outbound requests to be answered and
        for in-flight inbound requests to be answered by the host (up to the configured drain timeout), and then
        completes output. An abortive close fails and aborts everything immediately.
        """

        graceful: bool = True

    ##
    # events: session -> connection

    class Event(
        IoPipelineMessages.NeverInbound,
        IoPipelineMessages.AfterShutdownOutput,  # for the connection, not the peer: deliverable after an output half-close  # noqa
        Abstract,
    ):
        pass

    @dc.dataclass(frozen=True)
    class RequestReceived(Event):
        """The peer sent a request which must eventually be answered with a SendResponse."""

        request: RpcRequestMessage

    @dc.dataclass(frozen=True)
    class NotificationReceived(Event):
        notification: RpcNotificationMessage

    @dc.dataclass(frozen=True)
    class ResponseReceived(Event):
        """The peer answered a request sent with SendRequest."""

        request: RpcRequestMessage
        response: RpcResponseMessage

    @dc.dataclass(frozen=True)
    class RequestFailed(Event):
        """
        A sent request will never receive a response: it timed out, could not be encoded, exceeded a limit, or the
        session closed. Exactly one of ResponseReceived or RequestFailed is emitted per accepted SendRequest, unless the
        request was cancelled first.
        """

        request: RpcRequestMessage
        exc: Exception

    @dc.dataclass(frozen=True)
    class RequestHandlingAborted(Event):
        """
        The session stopped waiting for the host to answer an inbound request: the peer cancelled it, handling timed
        out, or the session is closing. Any SendResponse for it will be ignored, and the host should cancel its
        handler.
        """

        request: RpcRequestMessage
        exc: Exception

    @dc.dataclass(frozen=True)
    class PongReceived(Event):
        ping: RpcPingMessage
        pong: RpcPongMessage

    @dc.dataclass(frozen=True)
    class PingFailed(Event):
        """A sent ping will never be answered: it timed out, could not be encoded, or the session closed."""

        ping: RpcPingMessage
        exc: Exception

    @dc.dataclass(frozen=True)
    class Sent(Event):
        """
        A SendRequest, SendNotification, or SendPing has been fully handled and its bytes, if any, have crossed the
        transport boundary (the flush fence following it completed). Connections block sends on this, which is what
        makes backpressure real: a peer which stops reading stalls the sender rather than growing its buffers without
        bound.

        Not emitted for a command handled after the session closed; closure fails such sends instead.
        """

        command: 'RpcSessionMessages.Command'

    @dc.dataclass(frozen=True)
    class OutputPaused(Event):
        """The transport's write buffer is over its high watermark; the host should stop producing output."""

    @dc.dataclass(frozen=True)
    class OutputResumed(Event):
        """The transport's write buffer drained below its low watermark."""

    @dc.dataclass(frozen=True)
    class Closed(Event):
        """
        The session reached its terminal state. Emitted exactly once, after every pending request has been failed and
        every in-flight inbound request aborted, and before the session completes pipeline output. The exception, if
        any, is why the connection failed; a clean close carries None, and a graceful close which had to give up on
        in-flight work carries an RpcTimeoutError.
        """

        exc: ta.Optional[BaseException] = None

    ##
    # internal: codec -> session

    @dc.dataclass(frozen=True)
    class OutboundEncodeFailed(IoPipelineMessages.NeverOutbound):
        """
        The codec could not encode an outbound envelope, most often because its payload is not representable or it
        exceeded the maximum frame size.

        Rather than raising, which the pipeline would turn into a connection-fatal error, the codec drops the envelope
        and feeds this inward so the session can fail only the affected request or substitute an error response.
        """

        envelope: RpcEnvelope
        exc: Exception
