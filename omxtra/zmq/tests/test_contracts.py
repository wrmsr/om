"""The shared application contract, run against every available backend over real TCP and IPC transports."""
import asyncio
import os
import socket

import pytest

from ..api.addresses import IpcAddress
from ..api.addresses import TcpAddress
from ..api.configs import SocketConfig
from ..api.errors import AddressInUseError
from ..api.errors import ConcurrentReceiveError
from ..api.errors import InvalidAddressError
from ..api.errors import InvalidMessageError
from ..api.errors import InvalidRoutingIdError
from ..api.errors import SocketClosedError
from ..api.errors import UnroutableError
from ..api.errors import WouldBlockError
from ..api.errors import ZmqTimeoutError
from ..api.messages import MessageLimits
from ..api.messages import RoutedMessage
from .support import TIMEOUT
from .support import await_subscribed
from .support import backend_names
from .support import new_backend
from .support import recv_skipping_probes
from .support import short_tmp_dir


BACKENDS = backend_names()

TRANSPORTS = ['tcp', 'ipc']


def _bind_address(transport: str, tmp: str, name: str = 'ep') -> str:
    if transport == 'tcp':
        return 'tcp://127.0.0.1:*'
    return f'ipc://{os.path.join(tmp, name)}'


##


@pytest.mark.parametrize('transport', TRANSPORTS)
@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.parametrize('router_binds', [True, False])
@pytest.mark.asyncs('asyncio')
async def test_dealer_router_round_trip(backend_name, transport, router_binds):
    with short_tmp_dir() as tmp:
        async with new_backend(backend_name) as be:
            router = be.create_router()
            dealer = be.create_dealer(routing_id=b'dealer-1')

            binder, connector = (router, dealer) if router_binds else (dealer, router)
            bound = await binder.bind(_bind_address(transport, tmp))
            if transport == 'tcp':
                assert isinstance(bound.address, TcpAddress)
                assert bound.address.port != 0
            else:
                assert isinstance(bound.address, IpcAddress)
            await connector.connect(bound.address)

            await dealer.send((b'hello', b'', b'world'))
            got = await router.recv(timeout=TIMEOUT)
            assert got == RoutedMessage(b'dealer-1', (b'hello', b'', b'world'))

            await router.send(got.route, (b'reply',))
            assert await dealer.recv(timeout=TIMEOUT) == (b'reply',)

            # Neither side alternates: both send several messages before receiving any.
            for i in range(10):
                await dealer.send((b'd%d' % i,))
                await router.send(b'dealer-1', (b'r%d' % i,))
            assert [await router.recv(timeout=TIMEOUT) for _ in range(10)] == [
                RoutedMessage(b'dealer-1', (b'd%d' % i,)) for i in range(10)
            ]
            assert [await dealer.recv(timeout=TIMEOUT) for _ in range(10)] == [(b'r%d' % i,) for i in range(10)]


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_frames_are_preserved(backend_name):
    async with new_backend(backend_name) as be:
        a = be.create_dealer()
        b = be.create_dealer()
        bound = await a.bind('tcp://127.0.0.1:*')
        await b.connect(bound.address)

        msgs = [
            (b'',),
            (b'', b'', b''),
            (b'\x00', b'\x01'),
            tuple(bytes([i % 256]) * n for i, n in enumerate([0, 1, 254, 255, 256, 65536])),
            (os.urandom(1024 * 1024),),
            tuple(b'%d' % i for i in range(1000)),
        ]
        for m in msgs:
            await b.send(m)
        for m in msgs:
            assert await a.recv(timeout=TIMEOUT) == m


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_router_routes(backend_name):
    async with new_backend(backend_name) as be:
        router = be.create_router()
        bound = await router.bind('tcp://127.0.0.1:*')

        dealers = {rid: be.create_dealer(routing_id=rid) for rid in (b'a', b'b', b'c')}
        anon = be.create_dealer()
        for d in [*dealers.values(), anon]:
            await d.connect(bound.address)

        for rid, d in dealers.items():
            await d.send((b'from ' + rid,))
        await anon.send((b'from anon',))

        got = {}
        for _ in range(4):
            rm = await router.recv(timeout=TIMEOUT)
            got[rm.message[0]] = rm.route
        for rid in dealers:
            assert got[b'from ' + rid] == rid
        anon_route = got[b'from anon']
        assert anon_route and anon_route not in dealers

        for rid in dealers:
            await router.send(rid, (b'to ' + rid,))
        await router.send(anon_route, (b'to anon',))
        for rid, d in dealers.items():
            assert await d.recv(timeout=TIMEOUT) == (b'to ' + rid,)
        assert await anon.recv(timeout=TIMEOUT) == (b'to anon',)

        with pytest.raises(UnroutableError):
            await router.send(b'nobody', (b'x',))


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_router_fails_fast_when_a_route_is_full(backend_name):
    async with new_backend(backend_name) as be:
        router = be.create_router(SocketConfig(send_queue_size=1))
        dealer = be.create_dealer(SocketConfig(recv_queue_size=1), routing_id=b'slow')
        bound = await router.bind('tcp://127.0.0.1:*')
        await dealer.connect(bound.address)

        await dealer.send((b'hi',))
        assert (await router.recv(timeout=TIMEOUT)).route == b'slow'

        # The dealer never reads, so local and transport buffers fill and the router refuses rather than waits.
        chunk = b'x' * (256 * 1024)

        async def fill() -> None:
            for _ in range(10_000):
                await router.send(b'slow', (chunk,))

        with pytest.raises(WouldBlockError):
            await fill()


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_dealer_round_robin_and_fair_receive(backend_name):
    async with new_backend(backend_name) as be:
        dealer = be.create_dealer()
        routers = [be.create_router() for _ in range(3)]
        for r in routers:
            await dealer.connect((await r.bind('tcp://127.0.0.1:*')).address)

        # Each router learns the dealer's route from a message, so wait until all three connections can carry one.
        async with asyncio.timeout(TIMEOUT):
            routes: dict[int, bytes] = {}
            while len(routes) < 3:
                await dealer.send((b'hello',))
                for i, r in enumerate(routers):
                    try:
                        routes[i] = (await r.recv(timeout=.01)).route
                    except ZmqTimeoutError:
                        pass

        # Drain stragglers, then send a round of 30: round robin spreads them evenly over the ready peers.
        for r in routers:
            while True:
                try:
                    await r.recv(timeout=.05)
                except ZmqTimeoutError:
                    break
        for i in range(30):
            await dealer.send((b'%d' % i,))
        counts = []
        for r in routers:
            n = 0
            while True:
                try:
                    await r.recv(timeout=.2)
                except ZmqTimeoutError:
                    break
                n += 1
            counts.append(n)
        assert counts == [10, 10, 10]

        # Every router replies; the dealer receives all of them.
        for i, r in enumerate(routers):
            for j in range(5):
                await r.send(routes[i], (b'%d-%d' % (i, j),))
        got = [await dealer.recv(timeout=TIMEOUT) for _ in range(15)]
        assert sorted(got) == sorted((b'%d-%d' % (i, j),) for i in range(3) for j in range(5))
        # Messages from one peer keep their order.
        for i in range(3):
            assert [m for m in got if m[0].startswith(b'%d-' % i)] == [(b'%d-%d' % (i, j),) for j in range(5)]


@pytest.mark.parametrize('transport', TRANSPORTS)
@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.parametrize('pub_binds', [True, False])
@pytest.mark.asyncs('asyncio')
async def test_pub_sub(backend_name, transport, pub_binds):
    with short_tmp_dir() as tmp:
        async with new_backend(backend_name) as be:
            pub = be.create_publisher()
            sub = be.create_subscriber()
            binder, connector = (pub, sub) if pub_binds else (sub, pub)
            bound = await binder.bind(_bind_address(transport, tmp))
            await connector.connect(bound.address)

            await sub.subscribe(b'news')
            await await_subscribed(pub, sub, b'news')

            await pub.send((b'sports', b'skipped'))
            await pub.send((b'news', b'one'))
            await pub.send((b'newsflash', b'two'))
            await pub.send((b'new', b'skipped'))
            await pub.send((b'news',))
            assert await recv_skipping_probes(sub) == (b'news', b'one')
            assert await recv_skipping_probes(sub) == (b'newsflash', b'two')
            assert await recv_skipping_probes(sub) == (b'news',)


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_subscriptions_are_counted_and_matched_once(backend_name):
    async with new_backend(backend_name) as be:
        pub = be.create_publisher()
        sub = be.create_subscriber()
        await sub.connect((await pub.bind('tcp://127.0.0.1:*')).address)

        await sub.subscribe(b'a')
        await sub.subscribe(b'a')
        await sub.subscribe(b'ab')
        await sub.unsubscribe(b'zzz')  # absent: no effect
        await sub.subscribe(b'm0')
        await await_subscribed(pub, sub, b'm0')

        # Overlapping prefixes deliver a message once.
        await pub.send((b'abc',))
        await pub.send((b'm0-end',))
        assert await recv_skipping_probes(sub) == (b'abc',)
        assert await recv_skipping_probes(sub) == (b'm0-end',)

        # One of two references removed: still subscribed.
        await sub.unsubscribe(b'a')
        await sub.unsubscribe(b'ab')
        await sub.subscribe(b'm1')
        await await_subscribed(pub, sub, b'm1')
        await pub.send((b'a-still',))
        await pub.send((b'm1-end',))
        assert await recv_skipping_probes(sub) == (b'a-still',)
        assert await recv_skipping_probes(sub) == (b'm1-end',)

        # Last reference removed: no longer subscribed.
        await sub.unsubscribe(b'a')
        await sub.subscribe(b'm2')
        await await_subscribed(pub, sub, b'm2')
        await pub.send((b'a-gone',))
        await pub.send((b'm2-end',))
        assert await recv_skipping_probes(sub) == (b'm2-end',)


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_publisher_never_waits(backend_name):
    async with new_backend(backend_name) as be:
        pub = be.create_publisher(SocketConfig(send_queue_size=1))
        # No subscribers at all: success.
        await pub.send((b'nobody',))

        slow = be.create_subscriber(SocketConfig(recv_queue_size=1))
        fast = be.create_subscriber()
        bound = await pub.bind('tcp://127.0.0.1:*')
        for s in (slow, fast):
            await s.connect(bound.address)
            await s.subscribe(b'')
        await await_subscribed(pub, slow, b'')
        await await_subscribed(pub, fast, b'')

        # The slow subscriber never reads; publishing still never blocks. Publication is lossy for every subscriber at
        # capacity, the fast one included, so the fast one is only shown to keep receiving after the burst.
        chunk = b'x' * (64 * 1024)
        async with asyncio.timeout(TIMEOUT):
            for _ in range(500):
                await pub.send((b't', chunk))

            while True:
                await pub.send((b'last',))
                try:
                    if (await recv_skipping_probes(fast, timeout=.05)) == (b'last',):
                        break
                except ZmqTimeoutError:
                    pass


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_dealer_send_waits_for_a_peer(backend_name):
    async with new_backend(backend_name) as be:
        dealer = be.create_dealer()
        with pytest.raises(ZmqTimeoutError):
            await dealer.send((b'x',), timeout=.05)

        # Connect before the binder exists: the send completes once it appears.
        with short_tmp_dir() as tmp:
            path = os.path.join(tmp, 'late')
            await dealer.connect(f'ipc://{path}')
            send = asyncio.ensure_future(dealer.send((b'waited',), timeout=TIMEOUT))
            await asyncio.sleep(0)
            assert not send.done()

            router = be.create_router()
            await router.bind(f'ipc://{path}')
            await send
            assert (await router.recv(timeout=TIMEOUT)).message == (b'waited',)


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_receive_ownership(backend_name):
    async with new_backend(backend_name) as be:
        a = be.create_dealer()
        b = be.create_dealer()
        await b.connect((await a.bind('tcp://127.0.0.1:*')).address)

        # Only one receive at a time.
        first = asyncio.ensure_future(a.recv(timeout=TIMEOUT))
        await asyncio.sleep(0)
        with pytest.raises(ConcurrentReceiveError):
            await a.recv(timeout=TIMEOUT)

        # A cancelled receive leaves later messages available.
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        await b.send((b'kept',))
        assert await a.recv(timeout=TIMEOUT) == (b'kept',)

        with pytest.raises(ZmqTimeoutError):
            await a.recv(timeout=.02)


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_close_fails_waiters_and_operations(backend_name):
    async with new_backend(backend_name) as be:
        a = be.create_dealer()
        await a.bind('tcp://127.0.0.1:*')

        recv = asyncio.ensure_future(a.recv(timeout=TIMEOUT))
        send = asyncio.ensure_future(a.send((b'x',), timeout=TIMEOUT))
        await asyncio.sleep(0)
        await a.aclose()
        with pytest.raises(SocketClosedError):
            await recv
        with pytest.raises(SocketClosedError):
            await send

        for op in (a.recv(), a.send((b'x',)), a.bind('tcp://127.0.0.1:*'), a.connect('tcp://127.0.0.1:1')):
            with pytest.raises(SocketClosedError):
                await op
        await a.aclose()

    # Closing the backend closes its sockets.
    be = new_backend(backend_name)
    s = be.create_subscriber()
    await be.aclose()
    with pytest.raises(SocketClosedError):
        await s.recv()
    with pytest.raises(SocketClosedError):
        be.create_dealer()


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_validation(backend_name):
    limits = MessageLimits(max_frame_size=10, max_message_size=15, max_frames=3, max_subscription_size=4)
    async with new_backend(backend_name) as be:
        d = be.create_dealer(SocketConfig(limits=limits))
        r = be.create_router(SocketConfig(limits=limits))
        p = be.create_publisher(SocketConfig(limits=limits))
        s = be.create_subscriber(SocketConfig(limits=limits))

        for bad in [(), [], b'abc', (b'a', 'b'), (bytearray(b'a'),), (b'x' * 11,), (b'x' * 8, b'y' * 8), (b'',) * 4]:
            with pytest.raises(InvalidMessageError):
                await d.send(bad)  # type: ignore[arg-type]
            with pytest.raises(InvalidMessageError):
                await p.send(bad)  # type: ignore[arg-type]
            with pytest.raises(InvalidMessageError):
                await r.send(b'r', bad)  # type: ignore[arg-type]

        # Validation precedes any wait or routing decision.
        with pytest.raises(InvalidRoutingIdError):
            await r.send(b'', (b'x',))
        with pytest.raises(InvalidMessageError):
            await s.subscribe(b'12345')
        with pytest.raises(InvalidMessageError):
            await s.subscribe('a')  # type: ignore[arg-type]

        for rid in [b'', b'\x00abc', b'x' * 256]:
            with pytest.raises(InvalidRoutingIdError):
                be.create_dealer(routing_id=rid)

        for addr in ['tcp://127.0.0.1', 'udp://x:1', 'ipc://relative', 'tcp://::1:5', 'tcp://h:port', 'ipc:///a\0b']:
            with pytest.raises(InvalidAddressError):
                await d.bind(addr)
        for addr in ['tcp://127.0.0.1:*', 'tcp://*:5555']:
            with pytest.raises(InvalidAddressError):
                await d.connect(addr)
        with pytest.raises(InvalidAddressError):
            await d.bind('ipc:///' + 'x' * 200)


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_ipc_binding_never_removes_existing_paths(backend_name):
    with short_tmp_dir() as tmp:
        async with new_backend(backend_name) as be:
            a = be.create_router()
            path = os.path.join(tmp, 'ep')
            await a.bind(f'ipc://{path}')
            st = os.lstat(path)

            # A second binder is refused and the first keeps working.
            b = be.create_router()
            with pytest.raises(AddressInUseError):
                await b.bind(f'ipc://{path}')
            assert os.path.samestat(os.lstat(path), st)
            d = be.create_dealer(routing_id=b'd')
            await d.connect(f'ipc://{path}')
            await d.send((b'still',))
            assert (await a.recv(timeout=TIMEOUT)).message == (b'still',)

            # A stale socket, a regular file, and a symlink are all left alone.
            stale = os.path.join(tmp, 'stale')
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.bind(stale)
            s.close()
            regular = os.path.join(tmp, 'file')
            with open(regular, 'w') as f:  # noqa: ASYNC230
                f.write('keep')
            link = os.path.join(tmp, 'link')
            os.symlink(regular, link)
            for p in (stale, regular, link):
                with pytest.raises(AddressInUseError):
                    await b.bind(f'ipc://{p}')
            assert os.path.exists(stale)
            with open(regular) as f:  # noqa: ASYNC230
                assert f.read() == 'keep'
            assert os.path.islink(link)

            # A missing parent directory fails without creating anything.
            with pytest.raises(Exception):  # noqa
                await b.bind(f'ipc://{os.path.join(tmp, "missing", "ep")}')
            assert not os.path.exists(os.path.join(tmp, 'missing'))


def _has_ipv6_loopback() -> bool:
    if not socket.has_ipv6:
        return False
    try:
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            s.bind(('::1', 0))
    except OSError:
        return False
    return True


@pytest.mark.skipif(not _has_ipv6_loopback(), reason='no IPv6 loopback')
@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_ipv6(backend_name):
    async with new_backend(backend_name) as be:
        router = be.create_router()
        bound = await router.bind('tcp://[::1]:*')
        assert isinstance(bound.address, TcpAddress) and bound.address.is_ipv6 and bound.address.port
        assert str(bound.address) == f'tcp://[::1]:{bound.address.port}'

        dealer = be.create_dealer(routing_id=b'v6')
        await dealer.connect(bound.address)
        await dealer.send((b'over v6',))
        assert await router.recv(timeout=TIMEOUT) == RoutedMessage(b'v6', (b'over v6',))


@pytest.mark.asyncs('asyncio')
async def test_unknown_backend_name():
    with pytest.raises(ValueError):  # noqa: PT011
        new_backend('nope')
