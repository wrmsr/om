"""
The message vocabulary between a connection's host (the code driving a pipeline driver) and the JSON-RPC session handler
sitting innermost in the pipeline.

Commands are fed inbound at the pipeline boundary via a driver's `enqueue`, pass untouched through the byte-level
handlers, and are consumed by the session. Events are fed outbound by the session and, being unhandled by any driver,
are returned to the host from the driver's `next`.

Commands are marked `AfterFinalInput` so that responses to in-flight inbound requests may still be sent after the peer
half-closes its side of the transport.
"""
import typing as ta

from .... import dataclasses as dc
from .... import lang
from ....io.pipelines import all as ipl
from ..types import Batch
from ..types import Id
from ..types import NotSpecified
from ..types import Request
from ..types import Response


##


class JsonrpcPipelineMessages(lang.Namespace):
    ##
    # commands: host -> session

    class Command(
        ipl.Messages.NeverOutbound,
        ipl.Messages.AfterFinalInput,
        lang.Abstract,
    ):
        pass

    @dc.dataclass(frozen=True)
    class SendRequest(Command):
        """
        Send a request and track its response. The request must already carry a unique id.

        A timeout of NotSpecified uses the session's default; None disables the timeout for this request.
        """

        request: Request

        _: dc.KW_ONLY

        timeout_s: float | None | type[NotSpecified] = NotSpecified

    @dc.dataclass(frozen=True)
    class SendNotification(Command):
        notification: Request

    @dc.dataclass(frozen=True)
    class SendResponse(Command):
        """Answer an in-flight inbound request. Exactly one response per inbound request is accepted."""

        response: Response

    @dc.dataclass(frozen=True)
    class SendBatch(Command):
        """
        Send requests and notifications as a single batch payload.

        Each request within is tracked exactly as if sent individually; the peer may answer with a batch or with
        individual responses.
        """

        batch: Batch

        _: dc.KW_ONLY

        timeout_s: float | None | type[NotSpecified] = NotSpecified

    @dc.dataclass(frozen=True)
    class CancelRequest(Command):
        """
        Stop waiting for the response to a previously sent request. A late response is silently dropped.

        This is purely local: protocols with a wire-level cancellation notification send it themselves.
        """

        id: Id

    @dc.dataclass(frozen=True)
    class Close(Command):
        """
        Close the session.

        A graceful close stops accepting new outbound requests, waits for pending outbound requests to be answered and
        for in-flight inbound requests to be answered by the host (up to the configured drain timeout), and then
        completes output. An abortive close fails and aborts everything immediately.
        """

        _: dc.KW_ONLY

        graceful: bool = True

    ##
    # events: session -> host

    class Event(
        ipl.Messages.NeverInbound,
        lang.Abstract,
    ):
        pass

    @dc.dataclass(frozen=True)
    class RequestReceived(Event):
        """The peer sent a request which must eventually be answered with a SendResponse."""

        request: Request

    @dc.dataclass(frozen=True)
    class NotificationReceived(Event):
        notification: Request

    @dc.dataclass(frozen=True)
    class ResponseReceived(Event):
        """The peer answered a request sent with SendRequest or SendBatch."""

        request: Request
        response: Response

    @dc.dataclass(frozen=True)
    class RequestFailed(Event):
        """
        A sent request will never receive a response: it timed out, was too large, exceeded a limit, or the session
        closed. Exactly one of ResponseReceived or RequestFailed is emitted per accepted SendRequest, unless the
        request was cancelled first.
        """

        request: Request
        exc: Exception

    @dc.dataclass(frozen=True)
    class RequestHandlingAborted(Event):
        """
        The session stopped waiting for the host to answer an inbound request, because handling timed out or the
        session is closing. Any SendResponse for it will be ignored, and the host should cancel its handler.
        """

        request: Request
        exc: Exception

    @dc.dataclass(frozen=True)
    class Sent(Event):
        """
        A SendRequest, SendNotification, or SendBatch has been fully handled and its bytes, if any, have crossed the
        transport boundary (the flush fence following it completed). Hosts block sends on this, which is what makes
        backpressure real: a peer which stops reading stalls the sender rather than growing its buffers without bound.

        Not emitted for a command handled after the session closed; closure fails such sends instead.
        """

        command: JsonrpcPipelineMessages.Command

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
        in-flight work carries a JsonrpcTimeoutError.
        """

        exc: BaseException | None = None

    ##
    # internal: codec -> session

    @dc.dataclass(frozen=True)
    class OutboundEncodeFailed(ipl.Messages.NeverOutbound):
        """
        The codec could not encode an outbound payload, most often because it exceeded the maximum frame size.

        Rather than raising, which the pipeline would turn into a connection-fatal error, the codec drops the payload
        and feeds this inward so the session can fail only the affected request or substitute an error response.
        """

        payload: ta.Any
        exc: Exception
