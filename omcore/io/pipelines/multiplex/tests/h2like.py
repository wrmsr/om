# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""
An HTTP/2-shaped toy protocol: implicit open, one shared stream id space with parity, two-level signed credit with an
all-streams adjustment from SETTINGS, padding counted against credit, headers and trailers as uncontrolled typed items
ordered with data, RST_STREAM, and a GOAWAY graceful-shutdown marker.

Header compression is deliberately absent; in the real protocol it would be done here, at the connection, in wire
order, never inside a stream's pipeline.
"""
import dataclasses as dc
import typing as ta

from ....streambufs.segmented import SegmentedByteStreamBufferView
from ...core import IoPipeline
from ...flow.stub import StubIoPipelineFlowService
from ..adapters import IoPipelineMultiplexAdapter
from ..adapters import IoPipelineMultiplexConnection
from ..adapters import IoPipelineMultiplexStreamParams
from ..credit import ConnectionMultiplexCreditStrategy
from ..handlers import IoPipelineMultiplexConfig
from ..handlers import MultiplexIoPipelineHandler
from ..streams import IoPipelineMultiplexStream
from ..types import FlowControlMultiplexIoPipelineError
from ..types import IoPipelineMultiplexStreamOpening
from ..types import MultiplexStreamSpecFactory
from .wire import FrameCodec
from .wire import FrameCodecIoPipelineHandler


##
# Wire frames


@dc.dataclass(frozen=True)
class H2Headers:
    stream_id: int
    fields: str
    end_stream: bool


@dc.dataclass(frozen=True)
class H2Data:
    stream_id: int
    data: bytes
    end_stream: bool
    pad: int


@dc.dataclass(frozen=True)
class H2WindowUpdate:
    stream_id: int  # 0 for the connection
    n: int


@dc.dataclass(frozen=True)
class H2RstStream:
    stream_id: int
    code: str


@dc.dataclass(frozen=True)
class H2Settings:
    initial_window: int


@dc.dataclass(frozen=True)
class H2GoAway:
    last_stream_id: int
    code: str


H2_CODEC = FrameCodec([
    H2Headers,
    H2Data,
    H2WindowUpdate,
    H2RstStream,
    H2Settings,
    H2GoAway,
])


##
# Typed messages exchanged with a stream's pipeline, and local commands fed to the connection.


@dc.dataclass(frozen=True)
class Headers:
    fields: str


@dc.dataclass(frozen=True)
class SendSettings:
    initial_window: int


@dc.dataclass(frozen=True)
class SendRaw:
    """Test hook: a raw frame to send as control output, bypassing every check - for misbehaving peers."""

    frame: ta.Any


##


class H2LikeAdapter(IoPipelineMultiplexAdapter):
    def __init__(
            self,
            role: ta.Literal['client', 'server'],
            *,
            initial_window: int = 16 * 1024,
            peer_initial_window: int = 16 * 1024,
            max_frame: int = 4 * 1024,
            pad: int = 0,
    ) -> None:
        super().__init__()

        self._role = role
        self._initial_window = initial_window
        self._peer_initial_window = peer_initial_window
        self._max_frame = max_frame
        self._pad = pad

        self._next_local = 1 if role == 'client' else 2
        self._last_peer_id = 0
        self.goaway_received: ta.Optional[int] = None
        self.goaway_sent: ta.Optional[int] = None
        self.ignored_frames = 0

    def _is_peer_id(self, sid: int) -> bool:
        return bool(sid % 2) == (self._role == 'server')

    def _maybe_close(self, conn: IoPipelineMultiplexConnection, stream: ta.Optional[IoPipelineMultiplexStream]) -> None:
        if stream is not None and not stream.is_terminal and stream.local_finished and stream.remote_ended:
            conn.close(stream.key)

    #

    def inbound(self, conn: IoPipelineMultiplexConnection, msg: ta.Any) -> bool:
        if isinstance(msg, SendSettings):
            conn.send(H2Settings(msg.initial_window))
            return True

        if isinstance(msg, SendRaw):
            conn.send(msg.frame)
            return True

        if isinstance(msg, H2Settings):
            delta = msg.initial_window - self._peer_initial_window
            self._peer_initial_window = msg.initial_window
            conn.adjust_all(delta)
            return True

        if isinstance(msg, H2WindowUpdate):
            if msg.stream_id == 0:
                conn.grant(None, msg.n)
            elif conn.get(msg.stream_id) is not None:
                conn.grant(msg.stream_id, msg.n)
            return True

        if isinstance(msg, H2GoAway):
            self.goaway_received = msg.last_stream_id
            for s in conn.streams():
                if s.origin == 'local' and ta.cast(int, s.key) > msg.last_stream_id and not s.is_terminal:
                    # Never processed by the peer: safe to retry elsewhere.
                    conn.reset(s.key, 'REFUSED_STREAM')
            conn.begin_shutdown()
            return True

        if isinstance(msg, H2Headers):
            stream = conn.get(msg.stream_id)
            if stream is None:
                if not self._is_peer_id(msg.stream_id) or msg.stream_id <= self._last_peer_id:
                    self.ignored_frames += 1
                    return True
                self._last_peer_id = msg.stream_id
                stream = conn.open_remote(
                    msg.stream_id,
                    msg.fields,
                    recv_window=self._initial_window,
                    send_credit=self._peer_initial_window,
                )
                if stream is None:
                    return True
            conn.message(msg.stream_id, Headers(msg.fields))
            if msg.end_stream:
                conn.end(msg.stream_id)
                self._maybe_close(conn, stream)
            return True

        if isinstance(msg, H2Data):
            if (stream := conn.get(msg.stream_id)) is None:
                # A released stream's frames still count against the connection window (RFC 7540 6.9).
                self.ignored_frames += 1
                conn.discard(len(msg.data) + msg.pad)
                return True
            try:
                conn.data(msg.stream_id, msg.data, cost=len(msg.data) + msg.pad)
            except FlowControlMultiplexIoPipelineError as e:
                if e.scope == 'stream':
                    conn.reset_local(msg.stream_id, 'FLOW_CONTROL_ERROR')
                    return True
                raise
            if msg.end_stream:
                conn.end(msg.stream_id)
                self._maybe_close(conn, stream)
            return True

        if isinstance(msg, H2RstStream):
            if conn.get(msg.stream_id) is not None:
                conn.reset(msg.stream_id, msg.code)
            return True

        return False

    def open_local(self, conn: IoPipelineMultiplexConnection, info: ta.Any) -> IoPipelineMultiplexStreamParams:
        sid = self._next_local
        self._next_local += 2
        return IoPipelineMultiplexStreamParams(
            sid,
            recv_window=self._initial_window,
            send_credit=self._peer_initial_window,
            explicit=False,
        )

    #

    def encode_refuse(self, opening: IoPipelineMultiplexStreamOpening, reason: ta.Any) -> ta.Sequence[ta.Any]:
        return [H2RstStream(ta.cast(int, opening.key), 'REFUSED_STREAM')]

    def encode_reset(self, stream: IoPipelineMultiplexStream, reason: ta.Any) -> ta.Sequence[ta.Any]:
        return [H2RstStream(ta.cast(int, stream.key), str(reason))]

    def encode_credit(self, stream: ta.Optional[IoPipelineMultiplexStream], amount: int) -> ta.Sequence[ta.Any]:
        return [H2WindowUpdate(ta.cast(int, stream.key) if stream is not None else 0, amount)]

    def encode_data(
            self,
            stream: IoPipelineMultiplexStream,
            data: SegmentedByteStreamBufferView,
    ) -> ta.Sequence[ta.Any]:
        return [H2Data(ta.cast(int, stream.key), bytes(data.tobytes()), False, self._pad)]

    def encode_message(self, stream: IoPipelineMultiplexStream, msg: ta.Any) -> ta.Sequence[ta.Any]:
        return [H2Headers(ta.cast(int, stream.key), msg.fields, False)]

    def encode_end(self, stream: IoPipelineMultiplexStream) -> ta.Sequence[ta.Any]:
        return [H2Data(ta.cast(int, stream.key), b'', True, 0)]

    def encode_finish(self, stream: IoPipelineMultiplexStream) -> ta.Sequence[ta.Any]:
        if stream.local_ended:
            return []
        return [H2Data(ta.cast(int, stream.key), b'', True, 0)]

    def encode_connection_error(self, exc: BaseException) -> ta.Sequence[ta.Any]:
        code = 'FLOW_CONTROL_ERROR' if isinstance(exc, FlowControlMultiplexIoPipelineError) else 'INTERNAL_ERROR'
        return [H2GoAway(self._last_peer_id, code)]

    #

    def max_data_unit(self, stream: IoPipelineMultiplexStream) -> int:
        return self._max_frame

    def data_unit_overhead(self, stream: IoPipelineMultiplexStream) -> int:
        return self._pad

    def claim_output(self, stream: IoPipelineMultiplexStream, msg: ta.Any) -> bool:
        return isinstance(msg, Headers)

    def on_stream_finished(self, conn: IoPipelineMultiplexConnection, stream: IoPipelineMultiplexStream) -> None:
        if stream.remote_ended:
            conn.close(stream.key)
        else:
            conn.reset_local(stream.key, 'CANCEL')

    def on_shutdown(self, conn: IoPipelineMultiplexConnection) -> None:
        self.goaway_sent = self._last_peer_id
        conn.send(H2GoAway(self._last_peer_id, 'NO_ERROR'))
        conn.begin_shutdown()


def h2_like_spec(
        role: ta.Literal['client', 'server'],
        spec_factory: MultiplexStreamSpecFactory,
        *,
        adapter: ta.Optional[H2LikeAdapter] = None,
        config: ta.Optional[IoPipelineMultiplexConfig] = None,
        connection_send_window: int = 64 * 1024,
        connection_recv_window: int = 64 * 1024,
        connection_replenish_on: ta.Literal['receive', 'consume'] = 'receive',
        auto_read: bool = False,
) -> ta.Tuple[IoPipeline.Spec, MultiplexIoPipelineHandler]:
    if adapter is None:
        adapter = H2LikeAdapter(role)
    mux = MultiplexIoPipelineHandler(
        adapter,
        spec_factory,
        config=config,
        credit=ConnectionMultiplexCreditStrategy(
            send_credit=connection_send_window,
            recv_window=connection_recv_window,
            connection_replenish_on=connection_replenish_on,
        ),
    )
    return (
        IoPipeline.Spec(
            [FrameCodecIoPipelineHandler(H2_CODEC), mux],
            services=[StubIoPipelineFlowService(auto_read=auto_read)],
        ),
        mux,
    )
