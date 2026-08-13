from ... import check
from .pipelines.codecs import encode_rpc_wire_message_payload
from .pipelines.messages import RpcWireError
from .pipelines.messages import RpcWireResponse
from .pipelines.messages import RpcWireResult
from .protocol import RpcHandler
from .protocol import RpcProtocolError
from .protocol import RpcRequest
from .protocol import exception_type_name
from .registry import RpcResponseExecute
from .registry import RpcResponsePending
from .registry import RpcResponseRegistry
from .registry import RpcResponseRejected
from .registry import RpcResponseReplay


##


def rpc_remote_error_response(
        request: RpcRequest,
        exc: BaseException,
        *,
        message: str | None = None,
) -> RpcWireError:
    return RpcWireError(
        client_id=request.client_id,
        request_id=request.request_id,
        code='remote',
        remote_type=exception_type_name(exc),
        message=(str(exc) if message is None else message)[:1_000],
    )


def validate_rpc_response(
        request: RpcRequest,
        response: RpcWireResponse,
        *,
        max_frame_bytes: int,
) -> RpcWireResponse:
    try:
        payload = encode_rpc_wire_message_payload(response)
        if len(payload) > max_frame_bytes:
            raise RpcProtocolError(
                f'RPC frame is {len(payload)} bytes, exceeding limit {max_frame_bytes}',
            )
        return response
    except RpcProtocolError as exc:
        fallback = rpc_remote_error_response(request, exc)
        payload = encode_rpc_wire_message_payload(fallback)
        if len(payload) > max_frame_bytes:
            fallback = rpc_remote_error_response(
                request,
                exc,
                message='Failed to construct RPC response',
            )
        return fallback


class RpcRequestDispatcher:
    """Execute or replay requests while keeping waiting policy out of the registry."""

    def __init__(
            self,
            handler: RpcHandler,
            registry: RpcResponseRegistry,
            *,
            max_frame_bytes: int,
    ) -> None:
        super().__init__()

        check.arg(max_frame_bytes > 0)
        self._handler = handler
        self._registry = registry
        self._max_frame_bytes = max_frame_bytes

    def dispatch(self, request: RpcRequest) -> RpcWireResponse:
        claim = self._registry.claim(request)
        if isinstance(claim, (RpcResponseReplay, RpcResponseRejected)):
            return claim.response
        if isinstance(claim, RpcResponsePending):
            return claim.entry.wait()
        if not isinstance(claim, RpcResponseExecute):
            raise TypeError(claim)

        try:
            try:
                result = self._handler(request)
            except BaseException as exc:  # noqa
                response: RpcWireResponse = rpc_remote_error_response(request, exc)
            else:
                response = RpcWireResult(
                    client_id=request.client_id,
                    request_id=request.request_id,
                    result=result,
                )
            response = validate_rpc_response(
                request,
                response,
                max_frame_bytes=self._max_frame_bytes,
            )
        except BaseException as exc:  # noqa
            response = rpc_remote_error_response(
                request,
                exc,
                message='Failed to construct RPC response',
            )

        self._registry.complete(claim.entry, response)
        return response
