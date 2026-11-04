"""
The daemons protocol's connection pieces over `omcore.rpc`, shared by the sync, asyncio, and fdio hosts and clients.

A client connection is one handshaken, single-request conversation: connect, learn the service instance from its
greeting, send one request under the client-chosen identity, read its answer. Anything going wrong before the greeting
means the request never ran (`RpcUnavailableError`); after it, the request may have (`RpcCallIndeterminateError`). A
server connection answers that one request through the replay-aware dispatcher, under an activity lease from its
runtime, and closes.
"""
import typing as ta
import uuid

from omcore import check
from omcore.asyncs.asynclite.promises import AsynclitePromise
from omcore.rpc.configs import RpcConfig
from omcore.rpc.connection import RpcConnection
from omcore.rpc.dispatch import RpcHandler
from omcore.rpc.errors import RpcHandlerError
from omcore.rpc.errors import RpcRemoteErrorData
from omcore.rpc.handshake import RpcHandshakeCompletedEvent
from omcore.rpc.messages import RpcErrorMessage
from omcore.rpc.messages import RpcRequestMessage
from omcore.rpc.messages import RpcResponseMessage
from omcore.rpc.messages import RpcResultMessage
from omcore.rpc.messages import RpcSessionMessages
from omcore.rpc.runtime import RpcRuntime

from .pipelines.codecs import encode_rpc_wire_message_payload
from .pipelines.codecs import rpc_hello_instance_id
from .pipelines.codecs import rpc_message_of_request
from .pipelines.codecs import rpc_request_of_message
from .pipelines.messages import RpcWireError
from .pipelines.messages import RpcWireRequest
from .pipelines.messages import RpcWireResponse
from .pipelines.messages import RpcWireResult
from .protocol import RpcCallIndeterminateError
from .protocol import RpcProtocolError
from .protocol import RpcRemoteError
from .protocol import RpcRequest
from .protocol import RpcUnavailableError


##


def rpc_unavailable_response(request: RpcRequest) -> RpcWireError:
    return RpcWireError(
        client_id=request.client_id,
        request_id=request.request_id,
        code='unavailable',
        remote_type='omxtra.daemons.rpc.RpcServerActivityRejectedError',
        message='RPC server is shutting down',
    )


def rpc_answer(response: RpcWireResponse) -> ta.Any:
    """A dispatcher's response as a handler's outcome: its result, or its error raised to be sent exactly as it is."""

    if isinstance(response, RpcWireResult):
        return response.result
    if isinstance(response, RpcWireError):
        raise RpcHandlerError(RpcRemoteErrorData(
            code=response.code,
            remote_type=response.remote_type,
            message=response.message,
        ))
    raise TypeError(response)


def rpc_client_result(
        request: RpcRequest,
        response: RpcResponseMessage,
        *,
        instance_id: uuid.UUID,
) -> ta.Any:
    """A response as the client reports it: its result, or the error its code calls for."""

    if isinstance(response, RpcResultMessage):
        return response.result

    if isinstance(response, RpcErrorMessage):
        code = response.error.code
        if code == 'unavailable':
            # Refused before it ran: safe to retry.
            raise RpcUnavailableError(response.error.message)
        if code == 'remote':
            raise RpcRemoteError(
                remote_type=response.error.remote_type,
                message=response.error.message,
            )
        if code == 'protocol':
            raise RpcProtocolError(response.error.message)

    raise RpcCallIndeterminateError(request, instance_id=instance_id)


def rpc_handshake_failure(conn: RpcConnection, exc: BaseException) -> BaseException:
    """
    What a failed handshake is reported as: the protocol error which refused it, if one did, else unavailability - the
    request was never sent, so it never ran.
    """

    seen: set[int] = set()
    cur: BaseException | None = conn.close_exception or exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, RpcProtocolError):
            return cur
        cur = cur.__cause__

    err = RpcUnavailableError(str(conn.close_exception or exc))
    err.__cause__ = exc
    return err


##


class RpcClientRpcConnection(RpcConnection):
    """
    The client end of one conversation, async-colored and shared by the sync and asyncio clients: waits for the
    service's greeting, sends one identified request, and reads its answer, classifying every failure by whether the
    request may have run.
    """

    _HANDSHAKE_KEY: ta.ClassVar[ta.Any] = ('handshake',)

    def __init__(
            self,
            runtime: RpcRuntime,
            config: RpcConfig,
            *,
            max_frame_bytes: int,
            io_timeout_s: float | None,
    ) -> None:
        super().__init__(runtime, config)

        self._max_frame_bytes = max_frame_bytes
        self._io_timeout_s = io_timeout_s

        self._handshake_waiter: AsynclitePromise | None = None
        self._instance_id: uuid.UUID | None = None

        self._rpc_request: RpcRequest | None = None
        self._rpc_waiter: AsynclitePromise | None = None
        self._rpc_received = False

    @property
    def instance_id(self) -> uuid.UUID:
        return check.not_none(self._instance_id)

    async def start(self) -> None:
        # Registered first, so the greeting has somewhere to land however soon it arrives.
        self._handshake_waiter = self._add_waiter(self._HANDSHAKE_KEY)

        await super().start()

    async def _on_other_event(self, event: ta.Any) -> None:
        if isinstance(event, RpcHandshakeCompletedEvent):
            self._resolve_waiter(self._HANDSHAKE_KEY, event.peer_hello)
            return

        await super()._on_other_event(event)

    #

    async def handshake(self) -> uuid.UUID:
        """Waits for the greetings to cross, returning the service's instance id."""

        waiter = check.not_none(self._handshake_waiter)
        try:
            hello = await waiter.wait(timeout=self._io_timeout_s)
        except Exception as exc:  # noqa
            raise rpc_handshake_failure(self, exc) from None
        finally:
            self._discard_waiter(self._HANDSHAKE_KEY, waiter)

        self._instance_id = rpc_hello_instance_id(hello)
        return self._instance_id

    def _indeterminate(self, request: RpcRequest) -> RpcCallIndeterminateError:
        return RpcCallIndeterminateError(request, instance_id=self.instance_id)

    async def send_rpc(self, request: RpcRequest) -> None:
        """Sends the request, returning once its bytes are in the transport."""

        if self._rpc_request is not None:
            raise RuntimeError('RPC client connection already has a request')

        # Refused here, unsent, it certainly never ran.
        payload = encode_rpc_wire_message_payload(RpcWireRequest(request=request))
        if len(payload) > self._max_frame_bytes:
            raise RpcProtocolError(f'RPC frame is {len(payload)} bytes, exceeding limit {self._max_frame_bytes}')

        msg = rpc_message_of_request(request)
        key = ('request', msg.id)

        self._rpc_request = request
        self._rpc_waiter = self._add_waiter(key)
        try:
            await self._send(RpcSessionMessages.SendRequest(msg), key)
        except Exception as exc:  # noqa
            raise self._indeterminate(request) from exc

    async def receive_rpc(self) -> ta.Any:
        """Waits for the request's answer: its result, or the error it calls for."""

        request = check.not_none(self._rpc_request)
        if self._rpc_received:
            raise RuntimeError('RPC client connection already received its response')

        waiter = check.not_none(self._rpc_waiter)
        try:
            response = await waiter.wait()
        except Exception as exc:  # noqa
            raise self._indeterminate(request) from exc

        self._rpc_received = True
        return rpc_client_result(request, response, instance_id=self.instance_id)


##


class RpcServerHandler(RpcHandler):
    """
    Answers a connection's request through the replay-aware dispatcher, under an activity lease from the server's
    runtime held until the connection closes - until its answer is out - so a draining service waits for it. With no
    lease to be had the service is shutting down, and the request is refused unrun.

    One per connection: register `release_activity` as one of its close callbacks.
    """

    def __init__(
            self,
            dispatch: ta.Callable[[RpcRequest], ta.Awaitable[RpcWireResponse]],
            acquire_activity: ta.Callable[[], ta.ContextManager[ta.Any] | None],
    ) -> None:
        super().__init__()

        self._dispatch = dispatch
        self._acquire_activity = acquire_activity

        self._activity: ta.ContextManager[ta.Any] | None = None

    def release_activity(self, *_: ta.Any) -> None:
        if (activity := self._activity) is None:
            return
        self._activity = None
        activity.__exit__(None, None, None)

    async def handle_request(self, method: str, params: ta.Any) -> ta.Any:
        raise TypeError('daemons rpc requests are handled whole')

    async def handle_request_message(self, request: RpcRequestMessage) -> ta.Any:
        rpc_request = rpc_request_of_message(request)

        check.none(self._activity)
        if (activity := self._acquire_activity()) is None:
            return rpc_answer(rpc_unavailable_response(rpc_request))
        activity.__enter__()
        self._activity = activity

        return rpc_answer(await self._dispatch(rpc_request))
