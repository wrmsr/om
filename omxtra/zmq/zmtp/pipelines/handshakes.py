"""
The ZMTP 3.0 NULL handshake. On activation the local greeting is sent at once; once the peer's greeting has been
validated the local READY follows, without waiting for the peer's. A valid peer READY ends the handshake: it is
announced inbound as a ZmtpPeerReady, after which messages pass through.

The handshake has one absolute deadline from activation, so a peer trickling bytes cannot extend it.
"""
import typing as ta

from omcore import check
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.flow.types import IoPipelineFlow
from omcore.io.pipelines.flow.types import IoPipelineFlowMessages
from omcore.io.pipelines.sched.types import IoPipelineScheduling

from ...core.sockettypes import IDENTITY_SOCKET_TYPES
from ...core.sockettypes import SocketType
from ...core.sockettypes import is_supported_peer
from ..commands import ERROR
from ..commands import READY
from ..commands import ZmtpCommand
from ..commands import decode_error
from ..commands import decode_ready
from ..commands import encode_ready
from ..errors import ZmtpHandshakeError
from ..errors import ZmtpHandshakeTimeoutError
from ..errors import ZmtpPeerError
from ..errors import ZmtpProtocolError
from ..greetings import LOCAL_GREETING
from ..greetings import NULL_MECHANISM
from ..greetings import ZmtpGreeting
from .messages import ZmtpMessage
from .messages import ZmtpPeerReady


##


class ZmtpHandshakeIoPipelineHandler(IoPipelineHandler):
    def __init__(
            self,
            socket_type: SocketType,
            *,
            identity: bytes = b'',
            timeout_s: float | None = None,
            max_properties: int = 64,
    ) -> None:
        super().__init__()

        if identity and socket_type not in IDENTITY_SOCKET_TYPES:
            raise ValueError(f'{socket_type} sockets carry no identity')
        if timeout_s is not None and not timeout_s > 0:
            raise ValueError(timeout_s)

        self._socket_type = socket_type
        self._identity = identity
        self._timeout_s = timeout_s
        self._max_properties = max_properties

        self._state: ta.Literal['new', 'greeting', 'ready_wait', 'ready', 'failed'] = 'new'
        self._consumed_since_flush = False
        self._timer: IoPipelineScheduling.Handle | None = None

    @property
    def is_ready(self) -> bool:
        return self._state == 'ready'

    #

    def _request_read(self, ctx: IoPipelineHandlerContext) -> None:
        if (flow := ctx.services.find(IoPipelineFlow)) is not None and not flow.is_auto_read():
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

    def _cancel_timer(self) -> None:
        if (timer := self._timer) is not None:
            self._timer = None
            timer.cancel()

    @staticmethod
    def _on_timeout(ctx: IoPipelineHandlerContext) -> None:
        h = check.isinstance(ctx.handler, ZmtpHandshakeIoPipelineHandler)
        h._timer = None  # noqa
        if h._state in ('ready', 'failed'):  # noqa
            return
        h._state = 'failed'  # noqa
        ctx.feed_in(IoPipelineMessages.Error(
            ZmtpHandshakeTimeoutError(f'handshake did not complete within {h._timeout_s:g} seconds'),  # noqa
            direction='inbound',
            handler=ctx.ref,
        ))

    def _start(self, ctx: IoPipelineHandlerContext) -> None:
        self._state = 'greeting'
        if self._timeout_s is not None and (sched := ctx.services.find(IoPipelineScheduling)) is not None:
            self._timer = sched.schedule_context(ctx.ref, self._timeout_s, ZmtpHandshakeIoPipelineHandler._on_timeout)

        ctx.feed_out(LOCAL_GREETING)
        self._request_read(ctx)

    def _on_greeting(self, ctx: IoPipelineHandlerContext, g: ZmtpGreeting) -> None:
        if self._state != 'greeting':
            raise ZmtpProtocolError('unexpected greeting')
        if g.mechanism != NULL_MECHANISM:
            raise ZmtpHandshakeError(f'unsupported security mechanism {g.mechanism!r}')
        if g.as_server:
            raise ZmtpHandshakeError('NULL mechanism peer claims the server role')

        # A peer advertising a later 3.x version follows the lower version, so this side keeps its 3.0 profile.
        self._state = 'ready_wait'
        ctx.feed_out(encode_ready(self._socket_type, identity=self._identity))

    def _on_command(self, ctx: IoPipelineHandlerContext, cmd: ZmtpCommand) -> None:
        if cmd.name == ERROR:
            raise ZmtpPeerError(decode_error(cmd.data))

        if self._state == 'ready_wait':
            if cmd.name != READY:
                raise ZmtpHandshakeError(f'expected READY, got {cmd.name!r}')
            ready = decode_ready(cmd.data, max_properties=self._max_properties)
            if not is_supported_peer(self._socket_type, ready.socket_type):
                raise ZmtpHandshakeError(f'{self._socket_type.value} cannot connect to {ready.socket_type.value}')

            self._state = 'ready'
            self._cancel_timer()
            ctx.feed_in(ZmtpPeerReady(ready.socket_type, ready.identity, ready.properties))

        elif self._state == 'ready':
            if cmd.name == READY:
                raise ZmtpProtocolError('duplicate READY')
            # Other commands - such as later protocol versions', a native peer's heartbeat - are never application
            # traffic. They go inward all the same: a read batch holding only a command must still lead to the next
            # read, which inside the handshake only the session decides.
            ctx.feed_in(cmd)

        else:
            raise ZmtpProtocolError(f'unexpected command {cmd.name!r}')

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, ZmtpMessage):
            if self._state != 'ready':
                raise ZmtpProtocolError('message before handshake completion')
            ctx.feed_in(msg)

        elif isinstance(msg, ZmtpCommand):
            self._consumed_since_flush = True
            self._on_command(ctx, msg)

        elif isinstance(msg, ZmtpGreeting):
            self._consumed_since_flush = True
            self._on_greeting(ctx, msg)

        elif isinstance(msg, IoPipelineFlowMessages.FlushInput):
            # Until ready, this stage asks for more input after consuming any, as nothing inside it saw the input.
            if self._consumed_since_flush and self._state in ('greeting', 'ready_wait'):
                self._request_read(ctx)
            self._consumed_since_flush = False
            ctx.feed_in(msg)

        elif isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            self._start(ctx)

        elif isinstance(msg, (IoPipelineMessages.FinalInput, IoPipelineMessages.Error)):
            if self._state != 'ready':
                self._state = 'failed'
            self._cancel_timer()
            ctx.feed_in(msg)

        else:
            ctx.feed_in(msg)
