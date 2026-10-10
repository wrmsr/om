# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
"""
The driver conformance scenarios, run against a stream's child pipeline: the multiplexing handler is the child's driver,
and the stream's peer stands in for the transport.

The harness hosts one peer-opened stream behind the real multiplexing handler in a pure-driven parent pipeline, with a
loopback adapter whose frames are plain objects. Transport input is stream data (delivered in transport-sized chunks,
as a socket would deliver it), transport EOF is the peer ending its output, and the transport boundary is the parent's:
output has crossed it once it was emitted into the parent and the parent driver accepted it. Blocking output withholds
send credit, so output queues in the stream and drives the child's writability as a socket's buffer would.
"""
import dataclasses as dc
import typing as ta

from ....streambufs.segmented import SegmentedByteStreamBufferView
from ...core import IoPipeline
from ...drivers.pure import PureIoPipelineDriver
from ...drivers.tests import test_conformance as tc
from ...drivers.types import IoPipelineDriverState
from ...flow.stub import StubIoPipelineFlowService
from ..adapters import IoPipelineMultiplexAdapter
from ..adapters import IoPipelineMultiplexConnection
from ..adapters import IoPipelineMultiplexStreamParams
from ..children import IoPipelineMultiplexChildConfig
from ..handlers import IoPipelineMultiplexConfig
from ..handlers import MultiplexIoPipelineHandler
from ..streams import IoPipelineMultiplexStream
from ..types import IoPipelineMultiplexMessages
from ..types import IoPipelineMultiplexRefusal
from ..types import IoPipelineMultiplexStreamOpening


##


_KEY = 1
_BIG = 1 << 40


@dc.dataclass(frozen=True)
class _Open:
    key: int


@dc.dataclass(frozen=True)
class _Data:
    key: int
    data: bytes


@dc.dataclass(frozen=True)
class _Msg:
    key: int
    msg: ta.Any


@dc.dataclass(frozen=True)
class _End:
    key: int


@dc.dataclass(frozen=True)
class _Grant:
    key: int
    n: int


@dc.dataclass(frozen=True)
class _Reset:
    key: int


@dc.dataclass(frozen=True)
class _Batch:
    """The frames decoded from one transport read, delivered within one inbound call as a decoder would."""

    frames: ta.Sequence[ta.Any]


class _LoopbackAdapter(IoPipelineMultiplexAdapter):
    def inbound(self, conn: IoPipelineMultiplexConnection, msg: ta.Any) -> bool:
        if isinstance(msg, _Batch):
            for f in msg.frames:
                self.inbound(conn, f)
            return True

        if isinstance(msg, _Open):
            conn.open_remote(msg.key, recv_window=_BIG, send_credit=_BIG)
        elif isinstance(msg, _Data):
            conn.data(msg.key, msg.data)
        elif isinstance(msg, _End):
            conn.end(msg.key)
        elif isinstance(msg, _Grant):
            conn.grant(msg.key, msg.n)
        elif isinstance(msg, _Reset):
            conn.reset(msg.key, 'closed by harness')
        else:
            return False
        return True

    def open_local(self, conn: IoPipelineMultiplexConnection, info: ta.Any) -> IoPipelineMultiplexStreamParams:
        raise TypeError

    def encode_credit(self, stream: ta.Optional[IoPipelineMultiplexStream], amount: int) -> ta.Sequence[ta.Any]:
        return []

    def encode_data(
            self,
            stream: IoPipelineMultiplexStream,
            data: SegmentedByteStreamBufferView,
    ) -> ta.Sequence[ta.Any]:
        return [_Data(ta.cast(int, stream.key), bytes(data.tobytes()))]

    def encode_message(self, stream: IoPipelineMultiplexStream, msg: ta.Any) -> ta.Sequence[ta.Any]:
        return [_Msg(ta.cast(int, stream.key), msg)]

    def encode_end(self, stream: IoPipelineMultiplexStream) -> ta.Sequence[ta.Any]:
        return [_End(ta.cast(int, stream.key))]

    def claim_output(self, stream: IoPipelineMultiplexStream, msg: ta.Any) -> bool:
        # Whatever the child returns to its 'driver' reaches the harness, as unhandled driver output would.
        return True

    def max_data_unit(self, stream: IoPipelineMultiplexStream) -> int:
        return 1 << 30

    def on_stream_finished(self, conn: IoPipelineMultiplexConnection, stream: IoPipelineMultiplexStream) -> None:
        conn.close(stream.key)


class _MultiplexChildConformanceDriverAdapter(tc._ConformanceDriverAdapter):
    NAME = 'multiplex-child'

    def __init__(self, handler: tc._ConformanceIoPipelineHandler, **kwargs: ta.Any) -> None:
        super().__init__(handler, **kwargs)

        self._child_spec = tc._make_spec(
            handler,
            manual_input=self._manual_input,
            explicit_auto_input=self._explicit_auto_input,
        )

        self._mux = MultiplexIoPipelineHandler(
            _LoopbackAdapter(),
            self._spec_factory,
            config=IoPipelineMultiplexConfig(child=IoPipelineMultiplexChildConfig(
                read_batch_max_bytes=self._read_batch_max_bytes,
                write_high_watermark=self._write_high_watermark,
                write_low_watermark=self._write_low_watermark,
            )),
        )
        self._driver = PureIoPipelineDriver(IoPipeline.Spec(
            [self._mux],
            services=[StubIoPipelineFlowService(auto_read=True)],
        ))

        self._output = bytearray()
        self.observed_on_release: ta.List[ta.Any] = []
        self._eof = False
        self._blocked = False
        self._closed_by_harness = False
        self._started = False

    def _spec_factory(
            self,
            opening: IoPipelineMultiplexStreamOpening,
    ) -> ta.Union[IoPipeline.Spec, IoPipelineMultiplexRefusal]:
        return self._child_spec

    #

    @property
    def _stream(self) -> ta.Optional[IoPipelineMultiplexStream]:
        return self._mux.streams.get(_KEY)

    @property
    def state(self) -> IoPipelineDriverState:
        if not self._started:
            return IoPipelineDriverState.NEW
        if self._closed_by_harness:
            return IoPipelineDriverState.CLOSED
        child = self._mux._children.get(_KEY)
        stream = self._stream
        if child is None or stream is None:
            pipeline = self.pipeline
            return IoPipelineDriverState.CLOSED if pipeline.saw_final_output else IoPipelineDriverState.FAILED
        if child.failure is not None:
            return IoPipelineDriverState.FAILED
        if stream.local_finished or any(
                getattr(item, 'kind', None) == 'final' for item in list(stream._out_q)
        ):
            return IoPipelineDriverState.DRAINING
        return IoPipelineDriverState.RUNNING

    _child_pipeline: ta.Optional[IoPipeline] = None

    @property
    def pipeline(self) -> IoPipeline:
        if (p := self._mux.child_pipeline(_KEY)) is not None:
            self._child_pipeline = p
        assert self._child_pipeline is not None
        return self._child_pipeline

    @property
    def output_shutdown(self) -> bool:
        stream = self._stream
        if stream is None:
            return self._eof
        return stream.local_ended

    #

    def _step(self, *, read: bool) -> ta.Optional[ta.Any]:
        """Advances the parent, collecting stream output; returns the first typed message the child produced."""

        while self._driver.is_running or self._driver.state is IoPipelineDriverState.NEW:
            out = self._driver.next(read=read, raise_on_stall=False)
            if out is None:
                break
            if isinstance(out, _Data):
                self._output.extend(out.data)
            elif isinstance(out, _End):
                self._eof = True
            elif isinstance(out, _Msg):
                return out.msg
            else:
                raise TypeError(out)

        if not self._blocked and self._driver.has_pending_output:
            self._driver.drain_output()
            return self._step(read=read)

        return None

    async def start(self) -> None:
        self._driver.feed_input(_Open(_KEY))
        self._started = True
        assert self._step(read=True) is None
        self._child_pipeline = self._mux.child_pipeline(_KEY)

    async def enqueue(self, *msgs: ta.Any) -> ta.Optional[ta.Any]:
        self._driver.enqueue(IoPipelineMultiplexMessages.FeedStream(_KEY, msgs))
        return self._step(read=False)

    async def feed_input(self, data: bytes) -> ta.Any:
        mv = memoryview(data)
        self._driver.feed_input(_Batch([
            _Data(_KEY, bytes(mv[pos:pos + self._read_chunk_size]))
            for pos in range(0, len(mv), self._read_chunk_size)
        ]))
        return self._step(read=True)

    async def feed_eof(self) -> ta.Any:
        self._driver.feed_input(_End(_KEY))
        return self._step(read=True)

    async def step_nonblocking(self) -> ta.Optional[ta.Any]:
        return self._step(read=False)

    async def block_output(self) -> None:
        self._blocked = True
        self._driver.feed_input(_Grant(_KEY, -_BIG))
        assert self._step(read=True) is None

    async def release_output(self) -> None:
        if self._blocked:
            self._blocked = False
            if self._stream is not None:
                self._driver.feed_input(_Grant(_KEY, _BIG))
        if self._driver.is_running:
            while (out := self._step(read=True)) is not None:
                self.observed_on_release.append(out)

    def take_output(self) -> bytes:
        out = bytes(self._output)
        self._output.clear()
        return out

    def peer_saw_eof(self) -> bool:
        return self._eof

    async def close(self) -> None:
        if self._driver.is_running and self._stream is not None and not self._stream.is_terminal:
            self._driver.feed_input(_Reset(_KEY))
            self._step(read=True)
            self._closed_by_harness = True
        self._driver.close()


class TestMultiplexChildConformance(tc.TestIoPipelineDriverConformance):
    ADAPTER_TYPES = (_MultiplexChildConformanceDriverAdapter,)

    async def test_manual_input_is_honored_while_output_is_blocked(self) -> None:
        # The shared scenario observes input through output, which for a stream is ordered behind the blocked output -
        # unlike a driver's output for its caller. The property itself is checked directly: input is delivered while
        # output is blocked, and the observation follows once output is released.

        async def run(adapter: tc._ConformanceDriverAdapter) -> None:
            await adapter.start()
            await adapter.block_output()
            flush_output = tc.IoPipelineFlowMessages.FlushOutput()

            self.assertIsNone(await adapter.enqueue(tc._Emit([b'payload', flush_output]), tc._RequestInput()))
            self.assertIsNone(await adapter.feed_input(b'input'))
            self.assertEqual(
                [tc.ByteStreamBuffers.to_bytes(m, strict=True)
                 for m in adapter.handler.inputs if tc.ByteStreamBuffers.can_bytes(m)],
                [b'input'],
            )
            self.assertFalse(flush_output.is_done())

            await adapter.release_output()
            self.assertTrue(flush_output.is_succeeded())
            self.assertEqual(adapter.take_output(), b'payload')
            self.assertEqual(adapter.observed_on_release, [tc._ObservedInput(b'input')])  # type: ignore[attr-defined]

        await self._with_adapters(run, manual_input=True)
