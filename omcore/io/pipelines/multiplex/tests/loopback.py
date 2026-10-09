# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""
A loopback harness: one multiplexing handler in a pure-driven parent, with the test playing the peer by feeding plain
frame objects and reading frames back. No encoding, so every state can be reached precisely.
"""
import dataclasses as dc
import typing as ta

from ....streambufs.segmented import SegmentedByteStreamBufferView
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...drivers.pure import PureIoPipelineDriver
from ...drivers.types import IoPipelineDriverState
from ...flow.stub import StubIoPipelineFlowService
from ..adapters import MultiplexAdapter
from ..adapters import MultiplexConnection
from ..adapters import MultiplexStreamParams
from ..credit import MultiplexCreditStrategy
from ..handlers import MultiplexConfig
from ..handlers import MultiplexIoPipelineHandler
from ..schedulers import MultiplexOutputScheduler
from ..streams import MultiplexStream
from ..types import MultiplexMessages
from ..types import MultiplexStreamOpening
from ..types import MultiplexStreamSpecFactory


##
# Frames, in both directions unless noted.


@dc.dataclass(frozen=True)
class LOpen:
    key: ta.Any
    info: ta.Any = None
    credit: int = 1 << 30  # peer -> mux: initial send credit for the mux


@dc.dataclass(frozen=True)
class LConfirm:  # peer -> mux
    key: ta.Any
    credit: int = 1 << 30


@dc.dataclass(frozen=True)
class LAccept:  # mux -> peer
    key: ta.Any


@dc.dataclass(frozen=True)
class LRefuse:
    key: ta.Any
    reason: ta.Any = None


@dc.dataclass(frozen=True)
class LData:
    key: ta.Any
    data: bytes
    cost: ta.Optional[int] = None


@dc.dataclass(frozen=True)
class LMsg:
    key: ta.Any
    msg: ta.Any
    cost: int = 0


@dc.dataclass(frozen=True)
class LEnd:
    key: ta.Any


@dc.dataclass(frozen=True)
class LFinish:  # mux -> peer
    key: ta.Any
    ended: bool


@dc.dataclass(frozen=True)
class LClose:  # peer -> mux
    key: ta.Any


@dc.dataclass(frozen=True)
class LReset:
    key: ta.Any
    reason: ta.Any = None


@dc.dataclass(frozen=True)
class LGrant:
    key: ta.Any  # None for the connection
    n: int


@dc.dataclass(frozen=True)
class LAdjust:  # peer -> mux
    delta: int


@dc.dataclass(frozen=True)
class LGoodbye:  # mux -> peer
    exc: BaseException


@dc.dataclass(frozen=True)
class LBatch:  # peer -> mux
    """Several frames decoded from one transport read, delivered within one inbound call as a decoder would."""

    frames: ta.Sequence[ta.Any]


##


class Outcome:
    """Captures a completable's outcome, which is only observable from its listeners."""

    def __init__(self, msg: ta.Any) -> None:
        super().__init__()

        self.msg = msg
        self.result: ta.Any = None
        self.exc: ta.Optional[BaseException] = None
        self.done = False
        msg.add_listener(self._done)

    def _done(self, m: ta.Any) -> None:
        self.done = True
        if m.is_succeeded():
            self.result = m.get_result()
        else:
            self.exc = m.get_exception()


class LoopbackAdapter(MultiplexAdapter):
    def __init__(
            self,
            *,
            explicit_open: bool = True,
            recv_window: int = 1 << 30,
            local_send_credit: int = 0,
            max_unit: int = 1 << 20,
            overhead: int = 0,
            on_finish: ta.Literal['close', 'wait', 'reset'] = 'close',
            claim: ta.Callable[[ta.Any], bool] = lambda m: True,
            cost: ta.Callable[[ta.Any], int] = lambda m: 0,
            split: ta.Optional[ta.Callable[[ta.Any, int], ta.Optional[ta.Tuple[ta.Any, ta.Any]]]] = None,
    ) -> None:
        super().__init__()

        self._explicit_open = explicit_open
        self._recv_window = recv_window
        self._local_send_credit = local_send_credit
        self._max_unit = max_unit
        self._overhead = overhead
        self._on_finish = on_finish
        self._claim = claim
        self._cost = cost
        self._split = split

        self._next_key = 1000
        self.released: ta.List[ta.Any] = []
        self.input_ended = 0

    def inbound(self, conn: MultiplexConnection, msg: ta.Any) -> bool:
        if isinstance(msg, LBatch):
            for f in msg.frames:
                self.inbound(conn, f)
            return True

        if isinstance(msg, LOpen):
            conn.open_remote(msg.key, msg.info, recv_window=self._recv_window, send_credit=msg.credit)
        elif isinstance(msg, LConfirm):
            conn.confirm(msg.key, send_credit=msg.credit)
        elif isinstance(msg, LRefuse):
            conn.refuse(msg.key, msg.reason)
        elif isinstance(msg, LData):
            conn.data(msg.key, msg.data, cost=msg.cost)
        elif isinstance(msg, LMsg):
            conn.message(msg.key, msg.msg, cost=msg.cost)
        elif isinstance(msg, LEnd):
            conn.end(msg.key)
        elif isinstance(msg, LClose):
            conn.close(msg.key)
        elif isinstance(msg, LReset):
            conn.reset(msg.key, msg.reason)
        elif isinstance(msg, LGrant):
            conn.grant(msg.key, msg.n)
        elif isinstance(msg, LAdjust):
            conn.adjust_all(msg.delta)
        else:
            return False
        return True

    def open_local(self, conn: MultiplexConnection, info: ta.Any) -> MultiplexStreamParams:
        key = self._next_key
        self._next_key += 1
        return MultiplexStreamParams(
            key,
            recv_window=self._recv_window,
            send_credit=self._local_send_credit,
            explicit=self._explicit_open,
        )

    def encode_open(self, stream: MultiplexStream) -> ta.Sequence[ta.Any]:
        return [LOpen(stream.key, stream.info)]

    def encode_accept(self, stream: MultiplexStream) -> ta.Sequence[ta.Any]:
        return [LAccept(stream.key)]

    def encode_refuse(self, opening: MultiplexStreamOpening, reason: ta.Any) -> ta.Sequence[ta.Any]:
        return [LRefuse(opening.key, reason)]

    def encode_reset(self, stream: MultiplexStream, reason: ta.Any) -> ta.Sequence[ta.Any]:
        return [LReset(stream.key, reason)]

    def encode_credit(self, stream: ta.Optional[MultiplexStream], amount: int) -> ta.Sequence[ta.Any]:
        return [LGrant(stream.key if stream is not None else None, amount)]

    def encode_data(self, stream: MultiplexStream, data: SegmentedByteStreamBufferView) -> ta.Sequence[ta.Any]:
        return [LData(stream.key, bytes(data.tobytes()))]

    def encode_message(self, stream: MultiplexStream, msg: ta.Any) -> ta.Sequence[ta.Any]:
        return [LMsg(stream.key, msg)]

    def encode_end(self, stream: MultiplexStream) -> ta.Sequence[ta.Any]:
        return [LEnd(stream.key)]

    def encode_finish(self, stream: MultiplexStream) -> ta.Sequence[ta.Any]:
        return [LFinish(stream.key, stream.local_ended)]

    def encode_connection_error(self, exc: BaseException) -> ta.Sequence[ta.Any]:
        return [LGoodbye(exc)]

    def max_data_unit(self, stream: MultiplexStream) -> int:
        return self._max_unit

    def data_unit_overhead(self, stream: MultiplexStream) -> int:
        return self._overhead

    def claim_output(self, stream: MultiplexStream, msg: ta.Any) -> bool:
        return self._claim(msg)

    def message_cost(self, stream: MultiplexStream, msg: ta.Any) -> int:
        return self._cost(msg)

    def split_message(
            self,
            stream: MultiplexStream,
            msg: ta.Any,
            max_cost: int,
    ) -> ta.Optional[ta.Tuple[ta.Any, ta.Any]]:
        if self._split is None:
            return None
        return self._split(msg, max_cost)

    def on_stream_finished(self, conn: MultiplexConnection, stream: MultiplexStream) -> None:
        if self._on_finish == 'close':
            conn.close(stream.key)
        elif self._on_finish == 'reset' and not stream.remote_ended:
            conn.reset_local(stream.key, 'finished early')

    def on_stream_released(self, stream: MultiplexStream) -> None:
        self.released.append(stream.key)

    def on_input_ended(self, conn: MultiplexConnection) -> None:
        self.input_ended += 1
        super().on_input_ended(conn)


class OutboundRecorder(IoPipelineHandler):
    """Placed outside the multiplexing handler: records everything it emits, in order, including Defers."""

    def __init__(self) -> None:
        super().__init__()

        self.out: ta.List[ta.Any] = []

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        self.out.append(msg)
        ctx.feed_out(msg)


class LoopbackHarness:
    def __init__(
            self,
            spec_factory: MultiplexStreamSpecFactory,
            *,
            adapter: ta.Optional[LoopbackAdapter] = None,
            config: ta.Optional[MultiplexConfig] = None,
            credit: ta.Optional[MultiplexCreditStrategy] = None,
            scheduler: ta.Optional[MultiplexOutputScheduler] = None,
            parent_auto_read: bool = True,
            parent_flow: bool = True,
            extra_outer: ta.Sequence[IoPipelineHandler] = (),
    ) -> None:
        super().__init__()

        if adapter is None:
            adapter = LoopbackAdapter()
        self.adapter = adapter
        self.mux = MultiplexIoPipelineHandler(
            adapter,
            spec_factory,
            config=config,
            credit=credit,
            scheduler=scheduler,
        )
        self.recorder = OutboundRecorder()
        self.driver = PureIoPipelineDriver(IoPipeline.Spec(
            [*extra_outer, self.recorder, self.mux],
            services=[StubIoPipelineFlowService(auto_read=parent_auto_read)] if parent_flow else [],
        ))

        self.frames: ta.List[ta.Any] = []  # everything the peer has received, in order
        self.hold_drain = False

    @property
    def pipeline(self) -> IoPipeline:
        return self.driver.pipeline

    def step(self) -> ta.List[ta.Any]:
        """Advances the parent, returning the frames emitted since the last step."""

        out: ta.List[ta.Any] = []
        while True:
            while self.driver.is_running or self.driver.state is IoPipelineDriverState.NEW:
                msg = self.driver.next(read=True, raise_on_stall=False)
                if msg is None:
                    break
                out.append(msg)
            if (
                    self.hold_drain or
                    not self.driver.has_pending_output or
                    self.driver.state not in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING)
            ):
                break
            self.driver.drain_output()
        self.frames.extend(out)
        return out

    def feed(self, *frames: ta.Any) -> ta.List[ta.Any]:
        self.driver.feed_input(*frames)
        return self.step()

    def enqueue(self, *msgs: ta.Any) -> ta.List[ta.Any]:
        self.driver.enqueue(*msgs)
        return self.step()

    def open(self, spec: IoPipeline.Spec, info: ta.Any = None) -> Outcome:
        msg = MultiplexMessages.OpenStream(spec, info)
        out = Outcome(msg)
        self.enqueue(msg)
        return out

    def feed_stream(self, key: ta.Any, *msgs: ta.Any) -> ta.List[ta.Any]:
        return self.enqueue(MultiplexMessages.FeedStream(key, msgs))

    def app(self, key: ta.Any) -> ta.Any:
        """The (first) handler of a stream's pipeline."""

        pipeline = ta.cast(IoPipeline, self.mux.child_pipeline(key))
        return pipeline.handlers()[0].handler

    def eof(self) -> ta.List[ta.Any]:
        self.driver.feed_eof()
        return self.step()

    def close(self) -> None:
        self.driver.close()


def of_type(frames: ta.Iterable[ta.Any], ty: type, key: ta.Any = ...) -> ta.List[ta.Any]:
    return [f for f in frames if isinstance(f, ty) and (key is ... or getattr(f, 'key', None) == key)]


def data_of(frames: ta.Iterable[ta.Any], key: ta.Any) -> bytes:
    return b''.join(f.data for f in frames if isinstance(f, LData) and f.key == key)


def is_lifecycle(msg: ta.Any) -> bool:
    return isinstance(msg, (IoPipelineMessages.InitialInput, IoPipelineMessages.FinalInput))
