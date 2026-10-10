# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""
An SSH-shaped toy protocol: explicit open with confirm or refuse, a channel number chosen by each side, per-stream
credit only, a maximum packet size, typed in-band messages (requests and flow-controlled extended data), EOF half-close
and a CLOSE handshake, and no reset.
"""
import dataclasses as dc
import typing as ta

from ....streambufs.segmented import SegmentedByteStreamBufferView
from ...core import IoPipeline
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ..adapters import MultiplexAdapter
from ..adapters import MultiplexConnection
from ..adapters import MultiplexStreamParams
from ..handlers import MultiplexConfig
from ..handlers import MultiplexIoPipelineHandler
from ..streams import MultiplexStream
from ..types import MultiplexStreamOpening
from ..types import MultiplexStreamSpecFactory
from .wire import FrameCodec
from .wire import FrameCodecIoPipelineHandler


##
# Wire frames, addressed by the recipient's channel number.


@dc.dataclass(frozen=True)
class SshOpen:
    kind: str
    sender: int
    window: int
    max_packet: int
    info: bytes


@dc.dataclass(frozen=True)
class SshOpenConfirm:
    recipient: int
    sender: int
    window: int
    max_packet: int


@dc.dataclass(frozen=True)
class SshOpenFailure:
    recipient: int
    reason: str


@dc.dataclass(frozen=True)
class SshWindowAdjust:
    recipient: int
    n: int


@dc.dataclass(frozen=True)
class SshData:
    recipient: int
    data: bytes


@dc.dataclass(frozen=True)
class SshExtData:
    recipient: int
    code: int
    data: bytes


@dc.dataclass(frozen=True)
class SshRequest:
    recipient: int
    name: str
    want_reply: bool
    payload: bytes


@dc.dataclass(frozen=True)
class SshEof:
    recipient: int


@dc.dataclass(frozen=True)
class SshClose:
    recipient: int


SSH_CODEC = FrameCodec([
    SshOpen,
    SshOpenConfirm,
    SshOpenFailure,
    SshWindowAdjust,
    SshData,
    SshExtData,
    SshRequest,
    SshEof,
    SshClose,
])


##
# Typed messages exchanged with a channel's pipeline. Requests may follow EOF in either direction, so they are marked
# deliverable after both kinds of half-close.


@dc.dataclass(frozen=True)
class ChannelRequest(IoPipelineMessages.AfterFinalInput, IoPipelineMessages.AfterShutdownOutput):
    name: str
    want_reply: bool = False
    payload: bytes = b''


@dc.dataclass(frozen=True)
class ChannelExtData:
    """Error-stream data: flow-controlled like data, but typed."""

    code: int
    data: bytes


##


@dc.dataclass()
class SshChannelState:
    peer_id: ta.Optional[int] = None
    peer_max_packet: int = 0
    close_sent: bool = False
    close_received: bool = False


@dc.dataclass(frozen=True)
class SshOpenInfo:
    kind: str
    info: bytes
    peer_id: ta.Optional[int] = None  # for a peer-opened channel


class SshLikeAdapter(MultiplexAdapter):
    def __init__(
            self,
            *,
            window: int = 64 * 1024,
            max_packet: int = 8 * 1024,
    ) -> None:
        super().__init__()

        self._window = window
        self._max_packet = max_packet
        self._next_id = 100
        self.recently_closed: ta.Set[int] = set()
        self.late_frames = 0

    def _alloc(self) -> int:
        k = self._next_id
        self._next_id += 1
        return k

    def _st(self, stream: MultiplexStream) -> SshChannelState:
        return stream.protocol

    #

    def inbound(self, conn: MultiplexConnection, msg: ta.Any) -> bool:
        if isinstance(msg, SshOpen):
            key = self._alloc()
            stream = conn.open_remote(
                key,
                SshOpenInfo(msg.kind, msg.info, msg.sender),
                recv_window=self._window,
                send_credit=msg.window,
            )
            if stream is not None:
                stream.protocol = SshChannelState(peer_id=msg.sender, peer_max_packet=msg.max_packet)
            return True

        recipient = getattr(msg, 'recipient', None)
        if recipient is None:
            return False

        stream = conn.get(recipient)
        if stream is None:
            if recipient in self.recently_closed:
                # A frame crossing our close on the wire: absorbed.
                self.late_frames += 1
                return True
            raise KeyError(f'unknown channel {recipient}')

        st = self._st(stream)

        if isinstance(msg, SshOpenConfirm):
            st.peer_id = msg.sender
            st.peer_max_packet = msg.max_packet
            conn.confirm(recipient, send_credit=msg.window)

        elif isinstance(msg, SshOpenFailure):
            conn.refuse(recipient, msg.reason)

        elif isinstance(msg, SshWindowAdjust):
            conn.grant(recipient, msg.n)

        elif isinstance(msg, SshData):
            if not st.close_sent:  # data after our CLOSE is discarded, per the protocol
                conn.data(recipient, msg.data)

        elif isinstance(msg, SshExtData):
            if not st.close_sent:
                conn.message(recipient, ChannelExtData(msg.code, msg.data), cost=len(msg.data))

        elif isinstance(msg, SshRequest):
            conn.message(recipient, ChannelRequest(msg.name, msg.want_reply, msg.payload))

        elif isinstance(msg, SshEof):
            conn.end(recipient)

        elif isinstance(msg, SshClose):
            st.close_received = True
            if not st.close_sent:
                st.close_sent = True
                conn.send(SshClose(st.peer_id))  # type: ignore[arg-type]
            conn.close(recipient)

        else:
            return False

        return True

    def open_local(self, conn: MultiplexConnection, info: ta.Any) -> MultiplexStreamParams:
        return MultiplexStreamParams(self._alloc(), recv_window=self._window, explicit=True)

    #

    def encode_open(self, stream: MultiplexStream) -> ta.Sequence[ta.Any]:
        stream.protocol = SshChannelState()
        info: SshOpenInfo = stream.info
        return [SshOpen(info.kind, stream.key, self._window, self._max_packet, info.info)]  # type: ignore[arg-type]

    def encode_accept(self, stream: MultiplexStream) -> ta.Sequence[ta.Any]:
        return [SshOpenConfirm(self._st(stream).peer_id, stream.key, self._window, self._max_packet)]  # type: ignore[arg-type]  # noqa

    def encode_refuse(self, opening: MultiplexStreamOpening, reason: ta.Any) -> ta.Sequence[ta.Any]:
        return [SshOpenFailure(opening.info.peer_id, str(reason))]

    def encode_reset(self, stream: MultiplexStream, reason: ta.Any) -> ta.Sequence[ta.Any]:
        # No reset in this protocol: a locally aborted channel is closed.
        st = self._st(stream)
        if st.close_sent or st.peer_id is None:
            return []
        st.close_sent = True
        return [SshClose(st.peer_id)]

    def encode_credit(self, stream: ta.Optional[MultiplexStream], amount: int) -> ta.Sequence[ta.Any]:
        assert stream is not None
        st = self._st(stream)
        if st.close_sent:
            return []  # Nothing may be sent on a channel after our CLOSE: the grant is declined.
        return [SshWindowAdjust(st.peer_id, amount)]  # type: ignore[arg-type]

    def encode_data(self, stream: MultiplexStream, data: SegmentedByteStreamBufferView) -> ta.Sequence[ta.Any]:
        return [SshData(self._st(stream).peer_id, data.tobytes())]  # type: ignore[arg-type]

    def encode_message(self, stream: MultiplexStream, msg: ta.Any) -> ta.Sequence[ta.Any]:
        peer_id: int = self._st(stream).peer_id  # type: ignore[assignment]
        if isinstance(msg, ChannelExtData):
            return [SshExtData(peer_id, msg.code, msg.data)]
        if isinstance(msg, ChannelRequest):
            return [SshRequest(peer_id, msg.name, msg.want_reply, msg.payload)]
        raise TypeError(msg)

    def encode_end(self, stream: MultiplexStream) -> ta.Sequence[ta.Any]:
        return [SshEof(self._st(stream).peer_id)]  # type: ignore[arg-type]

    def encode_finish(self, stream: MultiplexStream) -> ta.Sequence[ta.Any]:
        st = self._st(stream)
        if st.close_sent:
            return []
        st.close_sent = True
        return [SshClose(st.peer_id)]  # type: ignore[arg-type]

    #

    def max_data_unit(self, stream: MultiplexStream) -> int:
        return self._st(stream).peer_max_packet

    def claim_output(self, stream: MultiplexStream, msg: ta.Any) -> bool:
        return isinstance(msg, (ChannelRequest, ChannelExtData))

    def message_cost(self, stream: MultiplexStream, msg: ta.Any) -> int:
        if isinstance(msg, ChannelExtData):
            return len(msg.data)
        return 0

    def split_message(
            self,
            stream: MultiplexStream,
            msg: ta.Any,
            max_cost: int,
    ) -> ta.Optional[ta.Tuple[ta.Any, ta.Any]]:
        if not isinstance(msg, ChannelExtData) or max_cost < 1 or len(msg.data) <= max_cost:
            return None
        return (ChannelExtData(msg.code, msg.data[:max_cost]), ChannelExtData(msg.code, msg.data[max_cost:]))

    def on_stream_finished(self, conn: MultiplexConnection, stream: MultiplexStream) -> None:
        # The channel number is free once CLOSE has gone both ways.
        if self._st(stream).close_received:
            conn.close(stream.key)

    def on_stream_released(self, stream: MultiplexStream) -> None:
        self.recently_closed.add(ta.cast(int, stream.key))


def ssh_like_spec(
        spec_factory: MultiplexStreamSpecFactory,
        *,
        adapter: ta.Optional[SshLikeAdapter] = None,
        config: ta.Optional[MultiplexConfig] = None,
        auto_read: bool = False,
) -> ta.Tuple[IoPipeline.Spec, MultiplexIoPipelineHandler]:
    if adapter is None:
        adapter = SshLikeAdapter()
    mux = MultiplexIoPipelineHandler(adapter, spec_factory, config=config)
    return (
        IoPipeline.Spec(
            [FrameCodecIoPipelineHandler(SSH_CODEC), mux],
            services=[StubIoPipelineFlowService(auto_read=auto_read)],
        ),
        mux,
    )
