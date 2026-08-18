import typing as ta
import uuid

from ....io.pipelines.core import IoPipelineHandler
from ....io.pipelines.core import IoPipelineHandlerContext
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.flow.types import IoPipelineFlow
from ....io.pipelines.flow.types import IoPipelineFlowMessages
from ..protocol import RpcProtocolError
from .messages import RpcClientConnected
from .messages import RpcClientHello
from .messages import RpcClientRequestSent
from .messages import RpcClientResponse
from .messages import RpcClientSendRequest
from .messages import RpcPipelineFailure
from .messages import RpcServerDispatch
from .messages import RpcServerHello
from .messages import RpcServerSendResponse
from .messages import RpcWireError
from .messages import RpcWireRequest
from .messages import RpcWireResult


##


_RpcClientSessionState: ta.TypeAlias = ta.Literal['new', 'hello', 'ready', 'request', 'done']


class RpcClientSessionIoPipelineHandler(IoPipelineHandler):
    """Implement one handshaken, single-request client conversation."""

    def __init__(self, protocol_version: int) -> None:
        super().__init__()

        self._protocol_version = protocol_version
        self._state: _RpcClientSessionState = 'new'

    def _fail(self, ctx: IoPipelineHandlerContext, exc: BaseException) -> None:
        if self._state == 'done':
            return
        self._state = 'done'
        ctx.feed_out(RpcPipelineFailure(exc=exc))
        ctx.feed_final_output()

    def _state_is(self, state: str) -> bool:
        return self._state == state

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            if self._state != 'new':
                raise RpcProtocolError('RPC client received duplicate initial input')
            self._state = 'hello'
            ctx.mark_propagated('inbound', msg)
            ctx.feed_out(RpcClientHello(version=self._protocol_version))
            if not self._state_is('hello'):
                return
            IoPipelineFlow.maybe_flush_output(ctx)
            return

        if isinstance(msg, RpcServerHello):
            if self._state != 'hello':
                self._fail(ctx, RpcProtocolError('Unexpected RPC server hello'))
                return
            if msg.version != self._protocol_version:
                self._fail(ctx, RpcProtocolError(
                    f'RPC protocol version mismatch: '
                    f'client={self._protocol_version}, server={msg.version!r}',
                ))
                return
            self._state = 'ready'
            ctx.feed_out(RpcClientConnected(instance_id=msg.instance_id))
            return

        if isinstance(msg, RpcClientSendRequest):
            if self._state != 'ready':
                raise RuntimeError('RPC client connection is not ready for a request')
            self._state = 'request'
            ctx.feed_out(RpcWireRequest(request=msg.request))
            if not self._state_is('request'):
                return
            if ctx.services.find(IoPipelineFlow) is not None:
                flush = IoPipelineFlowMessages.FlushOutput()
                flush.add_listener(lambda _: ctx.feed_out(RpcClientRequestSent(request=msg.request)))
                ctx.feed_out(flush)
            else:
                ctx.feed_out(RpcClientRequestSent(request=msg.request))
            return

        if isinstance(msg, (RpcWireResult, RpcWireError)):
            if self._state != 'request':
                self._fail(ctx, RpcProtocolError('Unexpected RPC response'))
                return
            self._state = 'done'
            ctx.feed_out(RpcClientResponse(response=msg))
            ctx.feed_final_output()
            return

        if isinstance(msg, IoPipelineMessages.Error):
            self._fail(ctx, msg.exc)
            return

        if isinstance(msg, RpcPipelineFailure):
            self._fail(ctx, msg.exc)
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            if self._state != 'done':
                self._fail(ctx, EOFError('RPC connection closed'))
                ctx.mark_propagated('inbound', msg)
                return
            ctx.feed_in(msg)
            return

        ctx.feed_in(msg)


_RpcServerSessionState: ta.TypeAlias = ta.Literal['new', 'hello', 'ready', 'dispatch', 'response', 'done']


class RpcServerSessionIoPipelineHandler(IoPipelineHandler):
    """Implement one handshaken, single-request server conversation."""

    def __init__(
            self,
            *,
            protocol_version: int,
            instance_id: uuid.UUID,
    ) -> None:
        super().__init__()

        self._protocol_version = protocol_version
        self._instance_id = instance_id
        self._state: _RpcServerSessionState = 'new'

    def _state_is(self, state: str) -> bool:
        return self._state == state

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            if self._state != 'new':
                raise RpcProtocolError('RPC server received duplicate initial input')
            self._state = 'hello'
            ctx.mark_propagated('inbound', msg)
            return

        if isinstance(msg, RpcClientHello):
            if not self._state_is('hello'):
                raise RpcProtocolError('Unexpected RPC client hello')
            ctx.feed_out(RpcServerHello(
                version=self._protocol_version,
                instance_id=self._instance_id,
            ))
            if self._state != 'hello':
                return
            IoPipelineFlow.maybe_flush_output(ctx)
            if msg.version != self._protocol_version:
                self._state = 'done'
                ctx.feed_final_output()
            else:
                self._state = 'ready'
            return

        if isinstance(msg, RpcWireRequest):
            if self._state != 'ready':
                self._state = 'done'
                ctx.feed_out(RpcPipelineFailure(exc=RpcProtocolError('Unexpected RPC request')))
                ctx.feed_final_output()
                return
            self._state = 'dispatch'
            ctx.feed_out(RpcServerDispatch(request=msg.request))
            return

        if isinstance(msg, RpcServerSendResponse):
            if self._state != 'dispatch':
                raise RuntimeError('RPC server has no request awaiting a response')
            self._state = 'response'
            ctx.feed_out(msg.response)
            if not self._state_is('response'):
                return
            self._state = 'done'
            IoPipelineFlow.maybe_flush_output(ctx)
            ctx.feed_final_output()
            return

        if isinstance(msg, IoPipelineMessages.Error):
            if self._state == 'done':
                return
            self._state = 'done'
            ctx.feed_out(RpcPipelineFailure(exc=msg.exc))
            ctx.feed_final_output()
            return

        if isinstance(msg, RpcPipelineFailure):
            if self._state == 'done':
                return
            self._state = 'done'
            ctx.feed_out(msg)
            ctx.feed_final_output()
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            if self._state != 'done':
                self._state = 'done'
                ctx.feed_final_output()
            ctx.feed_in(msg)
            return

        ctx.feed_in(msg)
