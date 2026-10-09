import typing as ta

from omcore import dataclasses as dc
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.drivers.pure import PureIoPipelineDriver
from omcore.io.pipelines.drivers.types import IoPipelineDriverState
from omcore.io.pipelines.flow.stub import StubIoPipelineFlowService
from omcore.io.pipelines.flow.types import IoPipelineFlow
from omcore.io.pipelines.flow.types import IoPipelineFlowMessages

from ....core.sockettypes import SocketType
from ..codecs import ZmtpCodecConfig
from ..codecs import ZmtpCodecIoPipelineHandler
from ..handshakes import ZmtpHandshakeIoPipelineHandler


##


@dc.dataclass(frozen=True)
class Send:
    """Fed inbound from outside the pipeline, the collector emits these messages outbound."""

    msgs: ta.Sequence[ta.Any]


class Collector(IoPipelineHandler):
    """An innermost handler recording what reaches it, asking for more input after each batch it received from."""

    def __init__(self, *, on_change: ta.Callable[[], None] | None = None) -> None:
        super().__init__()

        self._on_change = on_change

        self.items: list[ta.Any] = []
        self.errors: list[BaseException] = []
        self.final_input = False
        self._received = False

    def of_type[T](self, cls: type[T]) -> list[T]:
        return [i for i in self.items if isinstance(i, cls)]

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, Send):
            for m in msg.msgs:
                ctx.feed_out(m)

        elif isinstance(msg, IoPipelineFlowMessages.FlushInput):
            if self._received and not ctx.services[IoPipelineFlow].is_auto_read():
                ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())
            self._received = False
            ctx.feed_in(msg)

        elif isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            self.final_input = True
            self._changed()
            ctx.feed_in(msg)

        elif isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            self._changed()

        elif isinstance(msg, (IoPipelineFlowMessages.ReadyForOutput, IoPipelineFlowMessages.PauseOutput)):
            pass

        else:
            self._received = True
            self.items.append(msg)
            self._changed()

    def _changed(self) -> None:
        if (cb := self._on_change) is not None:
            cb()


def codec_spec(
        collector: Collector,
        *,
        config: ZmtpCodecConfig | None = None,
        auto_read: bool = True,
) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        [ZmtpCodecIoPipelineHandler(config), collector],
        services=[StubIoPipelineFlowService(auto_read=auto_read)],
    )


def zmtp_spec(
        collector: Collector,
        socket_type: SocketType,
        *,
        identity: bytes = b'',
        config: ZmtpCodecConfig | None = None,
        timeout_s: float | None = None,
        auto_read: bool = False,
) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        [
            ZmtpCodecIoPipelineHandler(config),
            ZmtpHandshakeIoPipelineHandler(socket_type, identity=identity, timeout_s=timeout_s),
            collector,
        ],
        services=[StubIoPipelineFlowService(auto_read=auto_read)],
    )


def step(d: PureIoPipelineDriver) -> list[ta.Any]:
    out = []
    while d.is_running or d.state is IoPipelineDriverState.NEW:
        if (o := d.next(read=True, raise_on_stall=False)) is None:
            break
        out.append(o)
    return out


class Link:
    """
    Two pure drivers back to back. Bytes move between them in chunks of at most `chunk` bytes per step, and at most
    `capacity` bytes wait unread in a receiving driver - beyond that, output stays queued in the sending driver.
    """

    def __init__(
            self,
            a: PureIoPipelineDriver,
            b: PureIoPipelineDriver,
            *,
            chunk: int | None = None,
            capacity: int | None = None,
    ) -> None:
        super().__init__()

        self.a = a
        self.b = b
        self._chunk = chunk
        self._capacity = capacity
        self._eof_sent: set[int] = set()
        self.unhandled: list[ta.Any] = []

    def _move(self, src: PureIoPipelineDriver, dst: PureIoPipelineDriver) -> bool:
        moved = False
        if src.has_pending_output and src.state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING):
            n = self._chunk
            if self._capacity is not None and dst.is_running:
                room = self._capacity - dst.pending_input_bytes
                n = room if n is None else min(n, room)
            if n is None or n > 0:
                data = src.drain_output(n)
                if data and dst.is_running:
                    dst.feed_input(data)
                    moved = True

        ended = src.output_shutdown or src.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)
        if ended and not src.has_pending_output and id(src) not in self._eof_sent:
            self._eof_sent.add(id(src))
            if dst.is_running:
                dst.feed_eof()
            moved = True

        return moved

    def pump(self, max_rounds: int = 1_000_000) -> None:
        for _ in range(max_rounds):
            outs = [*step(self.a), *step(self.b)]
            self.unhandled.extend(outs)
            progressed = bool(outs)
            progressed |= self._move(self.a, self.b)
            progressed |= self._move(self.b, self.a)
            if not progressed:
                return
        raise RuntimeError('link did not quiesce')
