# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
An optional hello handshake, installed between the envelope codec and the session.

Each side greets the other with an `RpcHelloMessage` of opaque fields - a protocol name and version, an instance id -
before anything else crosses. The initiating side greets as soon as the connection starts; the responding side greets
once it has the initiator's. A `validate` callback inspects the peer's greeting and raises to refuse it, which fails
the connection with a protocol error; the responder still sends its own greeting first, so a refused initiator learns
why from what it receives.

Until both greetings have crossed, envelopes the session sends are held back, along with the flush fences following
them, so requests may be made at once and simply go out when the connection is ready. Anything other than a greeting
arriving first is a protocol violation, as is a second greeting. On completion the handler emits
`RpcHandshakeCompletedEvent` toward the host, carrying the peer's greeting; `RpcConnection` hands such events to its
`_on_other_event`, where a subclass picks it up.
"""
import collections
import dataclasses as dc
import functools
import typing as ta
import weakref

from ..io.pipelines.core import IoPipelineHandler
from ..io.pipelines.core import IoPipelineHandlerContext
from ..io.pipelines.core import IoPipelineMessages
from ..io.pipelines.flow.types import IoPipelineFlow
from ..io.pipelines.flow.types import IoPipelineFlowMessages
from .errors import RpcProtocolError
from .messages import RpcEnvelope
from .messages import RpcHelloMessage
from .messages import RpcInfoEvent


RpcHelloValidator = ta.Callable[[ta.Mapping[str, ta.Any]], None]  # ta.TypeAlias


##


@dc.dataclass(frozen=True)
class RpcHandshakeCompletedEvent(
    RpcInfoEvent,
    IoPipelineMessages.NeverInbound,
    IoPipelineMessages.AfterShutdownOutput,
):
    """Both greetings have crossed. Fed outbound to the host."""

    peer_hello: ta.Mapping[str, ta.Any]


class RpcHandshakeIoPipelineHandler(IoPipelineHandler):
    def __init__(
            self,
            hello: ta.Mapping[str, ta.Any],
            *,
            initiate: bool,
            validate: ta.Optional[RpcHelloValidator] = None,
    ) -> None:
        super().__init__()

        self._hello = dict(hello)
        self._initiate = initiate
        self._validate = validate

        self._sent_hello = False
        self._peer_hello: ta.Optional[ta.Mapping[str, ta.Any]] = None
        self._completed = False
        self._failed = False
        self._held: ta.Deque[ta.Any] = collections.deque()

    @property
    def completed(self) -> bool:
        return self._completed

    @property
    def peer_hello(self) -> ta.Optional[ta.Mapping[str, ta.Any]]:
        return self._peer_hello

    #

    def _fail(self, ctx: IoPipelineHandlerContext, exc: BaseException) -> None:
        if self._failed:
            return
        self._failed = True
        self._held.clear()
        ctx.feed_in(IoPipelineMessages.Error(exc, direction='inbound', handler=ctx.ref))

    def _send_hello(self, ctx: IoPipelineHandlerContext) -> ta.Optional[IoPipelineFlowMessages.FlushOutput]:
        """Sends this side's greeting, returning the fence following it, if any."""

        self._sent_hello = True
        ctx.feed_out(RpcHelloMessage(self._hello))
        if ctx.invalidated or ctx.services.find(IoPipelineFlow) is None:
            return None
        fence = IoPipelineFlowMessages.FlushOutput()
        ctx.feed_out(fence)
        return fence

    @staticmethod
    def _fail_after_fence(
            ctx_ref: ta.Callable[[], ta.Optional[IoPipelineHandlerContext]],
            exc: BaseException,
            _fence: IoPipelineMessages.Completable[None],
    ) -> None:
        if (ctx := ctx_ref()) is None or ctx.invalidated:
            return
        ta.cast(RpcHandshakeIoPipelineHandler, ctx.handler)._fail(ctx, exc)  # noqa

    def _complete(self, ctx: IoPipelineHandlerContext) -> None:
        self._completed = True

        held, self._held = self._held, collections.deque()
        while held and not ctx.invalidated:
            ctx.feed_out(held.popleft())

        if not ctx.invalidated:
            ctx.feed_out(RpcHandshakeCompletedEvent(dict(ta.cast(ta.Mapping[str, ta.Any], self._peer_hello))))

    def _on_peer_hello(self, ctx: IoPipelineHandlerContext, msg: RpcHelloMessage) -> None:
        if self._peer_hello is not None:
            self._fail(ctx, RpcProtocolError('duplicate hello'))
            return
        self._peer_hello = msg.fields

        fence: ta.Optional[IoPipelineFlowMessages.FlushOutput] = None
        if not self._initiate:
            # Greet back before judging the peer's greeting, so a refused peer still learns who it reached.
            fence = self._send_hello(ctx)
            if ctx.invalidated:
                return

        if (v := self._validate) is not None:
            try:
                v(msg.fields)
            except Exception as e:  # noqa
                err: BaseException
                if isinstance(e, RpcProtocolError):
                    err = e
                else:
                    err = RpcProtocolError(f'hello refused: {e}')
                    err.__cause__ = e

                if fence is not None and not fence.is_done():
                    # Failing aborts the transport, which would discard the greeting just sent: fail once it is out.
                    fence.add_listener(functools.partial(self._fail_after_fence, weakref.ref(ctx), err))
                else:
                    self._fail(ctx, err)
                return

        self._complete(ctx)

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            if self._initiate and not self._sent_hello and not ctx.invalidated:
                self._send_hello(ctx)
            return

        if isinstance(msg, RpcHelloMessage):
            if self._failed:
                return
            if self._completed:
                self._fail(ctx, RpcProtocolError('hello after handshake'))
                return
            self._on_peer_hello(ctx, msg)
            return

        if isinstance(msg, RpcEnvelope) and not self._completed:
            if not self._failed:
                self._fail(ctx, RpcProtocolError(f'{type(msg).__name__} before handshake'))
            return

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if not self._completed and isinstance(msg, (RpcEnvelope, IoPipelineFlowMessages.FlushOutput)):
            if isinstance(msg, RpcHelloMessage):
                ctx.feed_out(msg)
            elif not self._failed:
                # Fences are held with what they follow, so whoever waits on one is not told of a send yet to happen.
                self._held.append(msg)
            elif isinstance(msg, IoPipelineFlowMessages.FlushOutput):
                ctx.feed_out(msg)
            return

        if isinstance(msg, IoPipelineMessages.FinalOutput):
            self._held.clear()

        ctx.feed_out(msg)
