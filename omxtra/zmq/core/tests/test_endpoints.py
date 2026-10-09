import pytest

from ...api.errors import UnroutableError
from ...api.errors import WouldBlockError
from ...api.messages import MessageLimits
from ...api.messages import RoutedMessage
from ..dealers import DealerEndpoint
from ..endpoints import EndpointConfig
from ..errors import PeerRejectedError
from ..errors import PeerViolationError
from ..publishers import PubEndpoint
from ..routers import RouterEndpoint
from ..sockettypes import SocketType
from ..subscribers import SubEndpoint
from .sinks import RecordingListener
from .sinks import RecordingSink
from .sinks import drain


def _attach(ep, socket_type, identity=b''):
    sink = RecordingSink()
    return ep.attach(socket_type=socket_type, identity=identity, sink=sink), sink


##


def test_incompatible_and_excess_peers_are_rejected():
    ep = DealerEndpoint(EndpointConfig(max_peers=1))
    for t in (SocketType.PUB, SocketType.SUB, SocketType.REP, SocketType.PUSH):
        with pytest.raises(PeerRejectedError):
            _attach(ep, t)
    _attach(ep, SocketType.ROUTER)
    with pytest.raises(PeerRejectedError):
        _attach(ep, SocketType.DEALER)


def test_dealer_round_robin_skips_blocked_peers():
    lst = RecordingListener()
    ep = DealerEndpoint(EndpointConfig(send_queue_size=2), listener=lst)
    assert not ep.try_send((b'nobody',))

    a, sa = _attach(ep, SocketType.ROUTER)
    b, sb = _attach(ep, SocketType.ROUTER)
    c, sc = _attach(ep, SocketType.DEALER)
    assert lst.take() == ['writable'] * 3

    for i in range(6):
        assert ep.try_send((b'%d' % i,))
    assert [drain(ep, p) for p in (a, b, c)] == [[(b'0',), (b'3',)], [(b'1',), (b'4',)], [(b'2',), (b'5',)]]
    # A peer is woken only when its queue becomes nonempty.
    assert (sa.take(), sb.take(), sc.take()) == (['send'], ['send'], ['send'])

    # Fill every peer, then make room on a and c only: sends skip the blocked b rather than wait behind it.
    for i in range(6):
        assert ep.try_send((b'f%d' % i,))
    assert not ep.try_send((b'none left',))
    drain(ep, a)
    drain(ep, c)
    for i in range(4):
        assert ep.try_send((b's%d' % i,))
    assert drain(ep, a) == [(b's0',), (b's2',)]
    assert drain(ep, c) == [(b's1',), (b's3',)]
    assert len(b.outbound) == 2

    # Room returning wakes waiting senders.
    for i in range(4):
        assert ep.try_send((b't%d' % i,))
    assert not ep.try_send((b'none left',))
    lst.take()
    assert ep.take_output(b) is not None
    assert lst.take() == ['writable']
    assert ep.try_send((b'b again',))
    assert drain(ep, b)[-1] == (b'b again',)


def test_fair_receive_and_read_backpressure():
    lst = RecordingListener()
    ep = DealerEndpoint(EndpointConfig(recv_queue_size=2), listener=lst)
    a, sa = _attach(ep, SocketType.ROUTER)
    b, sb = _attach(ep, SocketType.ROUTER)
    lst.take()

    for i in range(3):
        ep.deliver(a, (b'a%d' % i,))
    ep.deliver(b, (b'b0',))
    assert lst.take() == ['readable'] * 4

    # The session stops reading a peer over its bound, and is woken once room returns.
    assert not ep.can_receive(a)
    assert ep.can_receive(b)
    assert [ep.recv() for _ in range(4)] == [(b'a0',), (b'b0',), (b'a1',), (b'a2',)]
    assert ep.recv() is None
    assert sa.take() == ['recv'] and sb.take() == []


def test_detach_discards_output_keeps_received_and_ignores_stale_peers():
    ep = DealerEndpoint(EndpointConfig(recv_queue_size=1))
    a, sa = _attach(ep, SocketType.ROUTER)
    ep.deliver(a, (b'in',))
    assert not ep.can_receive(a)
    ep.try_send((b'out',))
    ep.detach(a)

    # Unsent output is discarded with the connection; what was received whole stays receivable, as natively.
    assert ep.take_output(a) is None
    assert ep.has_received()
    assert ep.recv() == (b'in',)
    assert sa.take() == ['send']  # no wake for a peer which is gone
    assert not ep.has_received()

    assert not ep.can_receive(a)
    ep.deliver(a, (b'late',))
    assert ep.recv() is None
    ep.detach(a)
    assert not ep.try_send((b'x',))


def test_close_discards_received_messages_of_detached_peers():
    ep = DealerEndpoint()
    a, _ = _attach(ep, SocketType.ROUTER)
    ep.deliver(a, (b'in',))
    ep.detach(a)
    ep.close()
    assert ep.recv() is None and not ep.has_received()


def test_router_identities():
    ep = RouterEndpoint()
    a, _ = _attach(ep, SocketType.DEALER, b'alpha')
    with pytest.raises(PeerRejectedError):
        _attach(ep, SocketType.DEALER, b'alpha')

    anon1, _ = _attach(ep, SocketType.DEALER)
    anon2, _ = _attach(ep, SocketType.ROUTER)
    assert anon1.route[0] == 0 and anon2.route[0] == 0 and anon1.route != anon2.route
    assert set(ep.routes()) == {b'alpha', anon1.route, anon2.route}

    ep.deliver(a, (b'hi',))
    ep.deliver(anon1, (b'yo',))
    assert ep.recv() == RoutedMessage(b'alpha', (b'hi',))
    assert ep.recv() == RoutedMessage(anon1.route, (b'yo',))

    ep.send(b'alpha', (b'reply',))
    assert drain(ep, a) == [(b'reply',)]
    with pytest.raises(UnroutableError):
        ep.send(b'nobody', (b'x',))

    # The identity is released only by the peer holding it.
    ep.detach(a)
    with pytest.raises(UnroutableError):
        ep.send(b'alpha', (b'x',))
    a2, _ = _attach(ep, SocketType.DEALER, b'alpha')
    ep.detach(a)
    ep.send(b'alpha', (b'new',))
    assert drain(ep, a2) == [(b'new',)]


def test_router_fails_fast_when_full():
    ep = RouterEndpoint(EndpointConfig(send_queue_size=1))
    a, _ = _attach(ep, SocketType.DEALER, b'a')
    ep.send(b'a', (b'1',))
    with pytest.raises(WouldBlockError):
        ep.send(b'a', (b'2',))
    assert drain(ep, a) == [(b'1',)]


def test_publisher_fan_out():
    ep = PubEndpoint(EndpointConfig(send_queue_size=2))
    a, sa = _attach(ep, SocketType.SUB)
    b, sb = _attach(ep, SocketType.XSUB)

    # Nothing is subscribed yet.
    ep.publish((b'news', b'x'))
    assert drain(ep, a) == [] and drain(ep, b) == []

    # Raw peers may repeat subscriptions; they are counted. Overlapping prefixes deliver once.
    for m in [(b'\x01news',), (b'\x01news',), (b'\x01n',)]:
        ep.deliver(a, m)
    ep.deliver(b, (b'\x01',))
    ep.deliver(b, (b'arbitrary xsub message',))
    ep.deliver(b, (b'\x01multi', b'part'))
    ep.publish((b'news', b'1'))
    ep.publish((b'other',))
    assert drain(ep, a) == [(b'news', b'1')]
    assert drain(ep, b) == [(b'news', b'1'), (b'other',)]

    ep.deliver(a, (b'\x00news',))
    ep.deliver(a, (b'\x00n',))
    ep.publish((b'news', b'2'))
    assert drain(ep, a) == [(b'news', b'2')]
    ep.deliver(a, (b'\x00news',))
    ep.deliver(a, (b'\x00absent',))
    ep.publish((b'news', b'3'))
    assert drain(ep, a) == []
    assert drain(ep, b) == [(b'news', b'2'), (b'news', b'3')]

    # A full peer misses publications; the others still get them.
    for i in range(4):
        ep.publish((b'n%d' % i,))
    assert drain(ep, b) == [(b'n0',), (b'n1',)]
    assert not ep.has_received()


def test_publisher_bounds_peer_subscriptions():
    ep = PubEndpoint(EndpointConfig(max_peer_subscriptions=2, limits=MessageLimits(max_subscription_size=3)))
    a, _ = _attach(ep, SocketType.SUB)
    ep.deliver(a, (b'\x01abc',))
    with pytest.raises(PeerViolationError):
        ep.deliver(a, (b'\x01abcd',))
    ep.deliver(a, (b'\x01x',))
    with pytest.raises(PeerViolationError):
        ep.deliver(a, (b'\x01y',))


def test_subscriber_counts_replays_and_coalesces():
    ep = SubEndpoint()
    ep.subscribe(b'a')
    ep.subscribe(b'a')
    ep.subscribe(b'b')
    ep.unsubscribe(b'zzz')

    p, sink = _attach(ep, SocketType.PUB)
    assert sink.take() == ['send']
    assert sorted(drain(ep, p)) == [(b'\x01a',), (b'\x01b',)]

    # Only effective changes are sent; a change and its reversal before sending cancel out.
    ep.unsubscribe(b'a')
    assert drain(ep, p) == []
    ep.unsubscribe(b'b')
    ep.subscribe(b'b')
    ep.subscribe(b'c')
    assert sink.take() == ['send', 'send']
    ep.unsubscribe(b'a')
    assert drain(ep, p) == [(b'\x01c',), (b'\x00a',)]
    assert sorted(ep.subscriptions()) == [b'b', b'c']

    # A second peer gets the current set.
    q, _ = _attach(ep, SocketType.XPUB)
    assert sorted(drain(ep, q)) == [(b'\x01b',), (b'\x01c',)]


def test_subscriber_filters():
    ep = SubEndpoint()
    p, _ = _attach(ep, SocketType.PUB)
    ep.subscribe(b'keep')
    ep.deliver(p, (b'keep', b'1'))
    ep.deliver(p, (b'drop', b'2'))
    ep.deliver(p, (b'keeper',))
    assert [ep.recv(), ep.recv(), ep.recv()] == [(b'keep', b'1'), (b'keeper',), None]


def test_close():
    lst = RecordingListener()
    ep = RouterEndpoint(listener=lst)
    a, sa = _attach(ep, SocketType.DEALER, b'a')
    b, sb = _attach(ep, SocketType.DEALER, b'b')
    ep.deliver(a, (b'x',))
    lst.take()

    ep.close()
    assert sa.take() == ['close'] and sb.take() == ['close']
    assert lst.take() == ['readable', 'writable']
    assert ep.recv() is None and ep.closed and not ep.peers()
    with pytest.raises(PeerRejectedError):
        _attach(ep, SocketType.DEALER, b'c')
    ep.close()
    assert sa.take() == []
