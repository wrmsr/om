"""Read flow at the session level after the handshake, stepped deterministically with a pure driver."""
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.drivers.pure import PureIoPipelineDriver
from omcore.io.pipelines.flow.stub import StubIoPipelineFlowService

from ....api.messages import RoutedMessage
from ....core.routers import RouterEndpoint
from ....core.sockettypes import SocketType
from ...commands import encode_ready
from ...frames import encode_command_frame
from ...frames import encode_frame_header
from ...greetings import ZmtpGreeting
from ...greetings import encode_greeting
from ..codecs import ZmtpCodecIoPipelineHandler
from ..handshakes import ZmtpHandshakeIoPipelineHandler
from ..sessions import ZmtpSessionIoPipelineHandler
from .harness import step
from .test_sessions import _PureSink


def _msg(*frames: bytes) -> bytes:
    return b''.join(encode_frame_header(len(f), more=i < len(frames) - 1) + f for i, f in enumerate(frames))


def test_command_only_batch_after_handshake_keeps_reading():
    router = RouterEndpoint()
    sink = _PureSink()
    session = ZmtpSessionIoPipelineHandler(router, sink)
    d = PureIoPipelineDriver(IoPipeline.Spec(
        [
            ZmtpCodecIoPipelineHandler(),
            ZmtpHandshakeIoPipelineHandler(SocketType.ROUTER),
            session,
        ],
        services=[StubIoPipelineFlowService(auto_read=False)],
    ))
    sink.driver = d
    step(d)

    ready = encode_ready(SocketType.DEALER, identity=b'peer')
    d.feed_input(encode_greeting(ZmtpGreeting()) + encode_command_frame(ready.name, ready.data) + _msg(b'one'))
    step(d)
    assert router.recv() == RoutedMessage(b'peer', (b'one',))

    # A read batch holding nothing but a command, as a native heartbeat PING arrives.
    d.feed_input(encode_command_frame(b'PING', b'\x00\x00'))
    step(d)

    d.feed_input(_msg(b'two'))
    step(d)
    assert d.pending_input_bytes == 0, 'the connection stopped reading: no read was requested after the PING batch'
    assert router.recv() == RoutedMessage(b'peer', (b'two',))
