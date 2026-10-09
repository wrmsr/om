"""Endpoints joined end to end by pure drivers through the whole stage chain, stepped deterministically."""
import gc
import weakref

import pytest

from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.drivers.pure import PureIoPipelineDriver
from omcore.io.pipelines.flow.stub import StubIoPipelineFlowService

from ....api.messages import RoutedMessage
from ....core.dealers import DealerEndpoint
from ....core.endpoints import Endpoint
from ....core.endpoints import EndpointConfig
from ....core.errors import PeerRejectedError
from ....core.peers import PeerSink
from ....core.publishers import PubEndpoint
from ....core.routers import RouterEndpoint
from ....core.sockettypes import SocketType
from ....core.subscribers import SubEndpoint
from ...commands import encode_ready
from ...errors import ZmtpProtocolError
from ...frames import encode_command_frame
from ...greetings import ZmtpGreeting
from ...greetings import encode_greeting
from ..codecs import ZmtpCodecIoPipelineHandler
from ..handshakes import ZmtpHandshakeIoPipelineHandler
from ..sessions import ZmtpSessionEnded
from ..sessions import ZmtpSessionIoPipelineHandler
from ..sessions import ZmtpSessionWake
from .harness import Link
from .harness import step


class _PureSink(PeerSink):
    def __init__(self) -> None:
        super().__init__()

        self.driver: PureIoPipelineDriver | None = None
        self.closed = False

    def wake_send(self) -> None:
        if self.driver is not None and self.driver.is_running:
            self.driver.enqueue(ZmtpSessionWake('send'))

    def wake_recv(self) -> None:
        if self.driver is not None and self.driver.is_running:
            self.driver.enqueue(ZmtpSessionWake('recv'))

    def close(self) -> None:
        self.closed = True


class _Node:
    def __init__(
            self,
            endpoint: Endpoint,
            *,
            identity: bytes = b'',
            config: PureIoPipelineDriver.Config | None = None,
            budget: int = 64 * 1024,
    ) -> None:
        super().__init__()

        self.endpoint = endpoint
        self.sink = _PureSink()
        self.session = ZmtpSessionIoPipelineHandler(endpoint, self.sink, turn_output_budget=budget)
        self.driver = PureIoPipelineDriver(
            IoPipeline.Spec(
                [
                    ZmtpCodecIoPipelineHandler(),
                    ZmtpHandshakeIoPipelineHandler(endpoint.SOCKET_TYPE, identity=identity),
                    self.session,
                ],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            config,
        )
        self.sink.driver = self.driver


def _link(a: _Node, b: _Node, **kwargs) -> Link:
    link = Link(a.driver, b.driver, **kwargs)
    link.pump()
    return link


##


def test_dealer_router():
    dealer, router = DealerEndpoint(), RouterEndpoint()
    a, b = _Node(dealer, identity=b'dealer'), _Node(router)
    link = _link(a, b)
    assert a.session.was_ready and b.session.was_ready
    assert router.routes() == [b'dealer']

    msgs = [(b'%d' % i, b'', b'x' * i) for i in range(50)]
    for m in msgs:
        assert dealer.try_send(m)
    router.send(b'dealer', (b'early reply',))
    link.pump()
    assert [router.recv() for _ in range(50)] == [RoutedMessage(b'dealer', m) for m in msgs]
    assert router.recv() is None
    assert dealer.recv() == (b'early reply',)


@pytest.mark.parametrize(('chunk', 'size'), [(1, 3_000), (3, 20_000), (1000, 70_000)])
def test_large_messages_in_small_reads(chunk, size):
    dealer, router = DealerEndpoint(), RouterEndpoint()
    a, b = _Node(dealer, identity=b'd'), _Node(router)
    link = _link(a, b, chunk=chunk)
    big = (b'a' * size, b'', b'b' * 300)
    assert dealer.try_send(big)
    link.pump()
    assert router.recv() == RoutedMessage(b'd', big)


def test_backpressure_end_to_end():
    # The router's application does not receive: its queue fills, its session stops reading, the link fills, the
    # dealer's driver pauses its session, and the dealer's queue fills - so its sends stop being admitted.
    small = EndpointConfig(send_queue_size=4, recv_queue_size=4)
    dealer, router = DealerEndpoint(small), RouterEndpoint(small)
    cfg = PureIoPipelineDriver.Config(write_high_watermark=1024, write_low_watermark=256)
    a, b = _Node(dealer, identity=b'd', config=cfg, budget=512), _Node(router, config=cfg)
    link = _link(a, b, capacity=2048)

    chunk = b'x' * 500
    sent = 0
    while dealer.try_send((b'%d' % sent, chunk)):
        sent += 1
        link.pump()
        assert sent < 1000
    assert router.recv() is not None
    received = 1

    # Bounded: what the dealer accepted fits in its queue, both drivers' buffers, the link, and the router's queue.
    assert sent < 4 + 4 + (1024 + 2048 + 1024) // 500 + 4

    # Receiving restores flow all the way back.
    while True:
        link.pump()
        if (m := router.recv()) is None:
            break
        assert m.message[0] == b'%d' % received
        received += 1
    assert received == sent
    assert dealer.try_send((b'again',))
    link.pump()
    assert router.recv() == RoutedMessage(b'd', (b'again',))


def test_pub_sub_fan_out_and_subscription_replay():
    pub = PubEndpoint()
    sub1, sub2 = SubEndpoint(), SubEndpoint()
    sub1.subscribe(b'a')
    sub2.subscribe(b'')

    p1, s1 = _Node(pub), _Node(sub1)
    p2, s2 = _Node(pub), _Node(sub2)
    l1, l2 = _link(p1, s1), _link(p2, s2)

    pub.publish((b'apple',))
    pub.publish((b'banana',))
    l1.pump()
    l2.pump()
    assert [sub1.recv(), sub1.recv()] == [(b'apple',), None]
    assert [sub2.recv(), sub2.recv(), sub2.recv()] == [(b'apple',), (b'banana',), None]

    sub1.subscribe(b'b')
    sub1.unsubscribe(b'a')
    l1.pump()
    pub.publish((b'apple2',))
    pub.publish((b'banana2',))
    l1.pump()
    assert [sub1.recv(), sub1.recv()] == [(b'banana2',), None]


def test_peer_eof_ends_the_session():
    dealer, router = DealerEndpoint(), RouterEndpoint()
    a, b = _Node(dealer, identity=b'd'), _Node(router)
    link = _link(a, b)
    a.driver.close()
    link.pump()
    assert router.routes() == []
    assert b.session.peer is None and b.session.failure is None

    # The end is handed to the connection's owner - at once, not behind unwritten output - for it to close.
    (ended,) = link.unhandled
    assert isinstance(ended, ZmtpSessionEnded)


def test_protocol_violation_detaches_and_fails_the_connection():
    router = RouterEndpoint()
    b = _Node(router)
    step(b.driver)
    b.driver.feed_input(encode_greeting(ZmtpGreeting()))
    step(b.driver)
    ready = encode_ready(SocketType.DEALER, identity=b'raw')
    b.driver.feed_input(encode_command_frame(ready.name, ready.data))
    step(b.driver)
    assert router.routes() == [b'raw']

    b.driver.feed_input(bytes([0x80, 0]))
    with pytest.raises(Exception):  # noqa
        step(b.driver)
    assert isinstance(b.session.failure, ZmtpProtocolError)
    assert router.routes() == []
    assert not b.driver.is_running


def test_duplicate_identity_is_rejected_and_the_first_keeps_working():
    router = RouterEndpoint()
    d1, d2 = DealerEndpoint(), DealerEndpoint()
    a1, b1 = _Node(d1, identity=b'same'), _Node(router)
    a2, b2 = _Node(d2, identity=b'same'), _Node(router)
    l1 = _link(a1, b1)
    with pytest.raises(Exception):  # noqa
        _link(a2, b2)
    assert isinstance(b2.session.failure, PeerRejectedError)
    assert not b2.driver.is_running

    assert d1.try_send((b'still here',))
    l1.pump()
    assert router.recv() == RoutedMessage(b'same', (b'still here',))


def test_endpoint_close_tells_sinks():
    dealer, router = DealerEndpoint(), RouterEndpoint()
    a, b = _Node(dealer, identity=b'd'), _Node(router)
    _link(a, b)
    router.close()
    assert b.sink.closed and router.routes() == []


def test_message_bytes_are_never_split_across_two_messages():
    # Two messages queued while output is paused go out whole and in order once it resumes.
    dealer, router = DealerEndpoint(), RouterEndpoint()
    cfg = PureIoPipelineDriver.Config(write_high_watermark=10, write_low_watermark=5)
    a, b = _Node(dealer, identity=b'd', config=cfg, budget=1), _Node(router)
    link = _link(a, b, chunk=7)
    for i in range(20):
        assert dealer.try_send((b'm%d' % i, b'-' * i))
    link.pump()
    assert [router.recv() for _ in range(20)] == [RoutedMessage(b'd', (b'm%d' % i, b'-' * i)) for i in range(20)]


def test_released_without_cycle_collection():
    gc.collect()
    gc.disable()
    try:
        dealer, router = DealerEndpoint(), RouterEndpoint()
        a, b = _Node(dealer, identity=b'd'), _Node(router)
        link = _link(a, b)
        dealer.try_send((b'pending',))
        link.a.close()
        link.b.close()
        refs = [weakref.ref(x) for x in (a.driver.pipeline, b.driver.pipeline, a.session, b.session)]
        del a, b, link
        dealer.close()
        router.close()
        assert [r() for r in refs] == [None] * 4
    finally:
        gc.enable()
