"""Failure, lifetime, and load behavior through real transports."""
import asyncio
import os
import socket

import pytest

from ..api.configs import SocketConfig
from ..api.errors import SocketClosedError
from ..api.errors import ZmqTimeoutError
from ..api.messages import RoutedMessage
from .support import TIMEOUT
from .support import await_subscribed
from .support import backend_names
from .support import new_backend
from .support import recv_skipping_probes
from .support import short_tmp_dir


BACKENDS = backend_names()

FAST_RECONNECT = SocketConfig(reconnect_interval=.01, reconnect_interval_max=.05)


def _open_fds() -> int:
    return len(os.listdir('/proc/self/fd')) if os.path.isdir('/proc/self/fd') else -1


##


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_simultaneous_large_full_duplex(backend_name):
    # Both sides send far more than every buffer and queue holds before either receives anything. Each side's sends
    # complete only as the other side's receives make room, so sending and receiving must run concurrently - and
    # neither side's stalled output may stop its input.
    n, size = 40, 512 * 1024
    cfg = SocketConfig(send_queue_size=2, recv_queue_size=2)
    async with new_backend(backend_name) as be:
        a = be.create_dealer(cfg)
        b = be.create_dealer(cfg)
        await b.connect((await a.bind('tcp://127.0.0.1:*')).address)

        async def send_all(s, tag):
            for i in range(n):
                await s.send((tag, b'%d' % i, bytes([i]) * size), timeout=TIMEOUT)

        async def recv_all(s, tag):
            for i in range(n):
                m = await s.recv(timeout=TIMEOUT)
                assert m[:2] == (tag, b'%d' % i) and m[2] == bytes([i]) * size

        async with asyncio.timeout(30):
            await asyncio.gather(send_all(a, b'a'), send_all(b, b'b'), recv_all(a, b'b'), recv_all(b, b'a'))


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_slow_receiver_backpressures_dealer(backend_name):
    cfg = SocketConfig(send_queue_size=2, recv_queue_size=2)
    async with new_backend(backend_name) as be:
        router = be.create_router(cfg)
        dealer = be.create_dealer(cfg, routing_id=b'd')
        await dealer.connect((await router.bind('tcp://127.0.0.1:*')).address)

        chunk = b'x' * (256 * 1024)
        sent = 0

        async def fill() -> None:
            nonlocal sent
            for _ in range(10_000):
                await dealer.send((chunk,), timeout=.2)
                sent += 1

        with pytest.raises(ZmqTimeoutError):
            await fill()
        assert 0 < sent < 1000

        # Receiving everything restores flow.
        for _ in range(sent):
            assert (await router.recv(timeout=TIMEOUT)).route == b'd'
        await dealer.send((b'after',), timeout=TIMEOUT)
        while (await router.recv(timeout=TIMEOUT)).message != (b'after',):
            pass


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.parametrize('restarting', ['router', 'dealer'])
@pytest.mark.asyncs('asyncio')
async def test_peer_restart(backend_name, restarting):
    with short_tmp_dir() as tmp:
        addr = f'ipc://{os.path.join(tmp, "ep")}'
        async with new_backend(backend_name) as be:
            router = be.create_router(FAST_RECONNECT)
            await router.bind(addr)
            dealer_id = b'd'
            dealer = be.create_dealer(FAST_RECONNECT, routing_id=dealer_id)
            await dealer.connect(addr)
            await dealer.send((b'first',))
            assert await router.recv(timeout=TIMEOUT) == RoutedMessage(b'd', (b'first',))

            if restarting == 'router':
                await router.aclose()
                router = be.create_router(FAST_RECONNECT)
                await router.bind(addr)
            else:
                # A restarted peer reusing its identity can be refused until the router notices the old connection is
                # gone - which is not portably prompt - so it takes a new one.
                await dealer.aclose()
                dealer_id = b'd-restarted'
                dealer = be.create_dealer(FAST_RECONNECT, routing_id=dealer_id)
                await dealer.connect(addr)

            # Delivery across a restart is not guaranteed, so probe until one arrives.
            async with asyncio.timeout(TIMEOUT):
                while True:
                    await dealer.send((b'again',), timeout=TIMEOUT)
                    try:
                        if (await router.recv(timeout=.05)).message == (b'again',):
                            break
                    except ZmqTimeoutError:
                        pass
            await router.send(dealer_id, (b'reply',))
            assert await dealer.recv(timeout=TIMEOUT) == (b'reply',)


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_subscriptions_replayed_after_publisher_restart(backend_name):
    with short_tmp_dir() as tmp:
        addr = f'ipc://{os.path.join(tmp, "ep")}'
        async with new_backend(backend_name) as be:
            pub = be.create_publisher()
            await pub.bind(addr)
            sub = be.create_subscriber(FAST_RECONNECT)
            await sub.connect(addr)
            await sub.subscribe(b'topic')
            await await_subscribed(pub, sub, b'topic')

            await pub.aclose()
            pub = be.create_publisher()
            await pub.bind(addr)

            # Nothing is subscribed again by the application: the new connection gets the subscriptions replayed.
            await await_subscribed(pub, sub, b'topic')
            await pub.send((b'topic', b'after restart'))
            await pub.send((b'other',))
            assert await recv_skipping_probes(sub) == (b'topic', b'after restart')


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_garbage_and_silent_peers_do_not_disturb_others(backend_name):
    async with new_backend(backend_name) as be:
        router = be.create_router(SocketConfig(handshake_timeout=.2))
        bound = await router.bind('tcp://127.0.0.1:*')
        host, port = '127.0.0.1', bound.address.port  # type: ignore[attr-defined]

        garbage_r, garbage_w = await asyncio.open_connection(host, port)
        garbage_w.write(b'GET / HTTP/1.1\r\n\r\n' * 10)
        silent_r, silent_w = await asyncio.open_connection(host, port)

        dealer = be.create_dealer(routing_id=b'good')
        await dealer.connect(bound.address)
        await dealer.send((b'fine',))
        assert await router.recv(timeout=TIMEOUT) == RoutedMessage(b'good', (b'fine',))

        # The in-house backend drops both: the garbage one at once, the silent one at the handshake deadline. A native
        # socket takes a peer not starting with a ZMTP 3 signature for a legacy one, so only non-interference is
        # portable.
        if backend_name == 'pipelines':
            async with asyncio.timeout(TIMEOUT):
                await garbage_r.read()
                await silent_r.read()
        garbage_w.close()
        silent_w.close()

        await router.send(b'good', (b'still fine',))
        assert await dealer.recv(timeout=TIMEOUT) == (b'still fine',)


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_duplicate_identity_never_takes_over(backend_name):
    async with new_backend(backend_name) as be:
        router = be.create_router()
        bound = await router.bind('tcp://127.0.0.1:*')
        first = be.create_dealer(routing_id=b'same')
        await first.connect(bound.address)
        await first.send((b'first',))
        assert await router.recv(timeout=TIMEOUT) == RoutedMessage(b'same', (b'first',))

        # The second connection is refused its identity. What its sends then do differs - the in-house backend ends
        # the connection, a native router keeps it unidentified - but the route stays with the first.
        second = be.create_dealer(routing_id=b'same')
        await second.connect(bound.address)
        await second.send((b'second',), timeout=TIMEOUT)
        await asyncio.sleep(.1)

        for i in range(3):
            await router.send(b'same', (b'to first %d' % i,))
        for i in range(3):
            assert await first.recv(timeout=TIMEOUT) == (b'to first %d' % i,)
        with pytest.raises(ZmqTimeoutError):
            await second.recv(timeout=.1)

        await first.send((b'first again',))
        while (rm := await router.recv(timeout=TIMEOUT)).message != (b'first again',):
            assert rm.route != b'same'
        assert rm.route == b'same'


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_cancelled_send_before_admission_is_never_delivered(backend_name):
    async with new_backend(backend_name) as be:
        dealer = be.create_dealer()
        send = asyncio.ensure_future(dealer.send((b'cancelled',), timeout=TIMEOUT))
        await asyncio.sleep(0)
        send.cancel()
        with pytest.raises(asyncio.CancelledError):
            await send

        router = be.create_router()
        await dealer.connect((await router.bind('tcp://127.0.0.1:*')).address)
        await dealer.send((b'admitted',), timeout=TIMEOUT)
        assert (await router.recv(timeout=TIMEOUT)).message == (b'admitted',)
        with pytest.raises(ZmqTimeoutError):
            await router.recv(timeout=.1)


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_close_during_connect_and_unreachable_retries(backend_name):
    with short_tmp_dir() as tmp:
        async with new_backend(backend_name) as be:
            dealer = be.create_dealer(FAST_RECONNECT)
            # Nothing listens on either: retries continue until the attachment or socket closes.
            att = await dealer.connect(f'ipc://{os.path.join(tmp, "never")}')
            await dealer.connect('tcp://127.0.0.1:1')
            await asyncio.sleep(.05)
            await att.aclose()
            async with asyncio.timeout(TIMEOUT):
                await dealer.aclose()
            with pytest.raises(SocketClosedError):
                await dealer.send((b'x',))


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_removed_listener_accepts_no_more(backend_name):
    async with new_backend(backend_name) as be:
        router = be.create_router()
        att = await router.bind('tcp://127.0.0.1:*')
        address = att.address
        await att.aclose()
        with pytest.raises(ConnectionRefusedError):
            await asyncio.wait_for(asyncio.open_connection('127.0.0.1', address.port), TIMEOUT)  # type: ignore[attr-defined]  # noqa


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_repeated_lifetimes_release_everything(backend_name):
    async def one_lifetime():
        with short_tmp_dir() as tmp:
            async with new_backend(backend_name) as be:
                router = be.create_router()
                bound = await router.bind(f'ipc://{os.path.join(tmp, "ep")}')
                await router.bind('tcp://127.0.0.1:*')
                dealers = [be.create_dealer(routing_id=b'%d' % i) for i in range(3)]
                for d in dealers:
                    await d.connect(bound.address)
                    await d.send((b'hi',))
                for _ in dealers:
                    await router.recv(timeout=TIMEOUT)
                pub = be.create_publisher()
                sub = be.create_subscriber()
                await sub.connect((await pub.bind('tcp://127.0.0.1:*')).address)
                await sub.subscribe(b'')
                await await_subscribed(pub, sub, b'')
                # Leave things pending: queued output, a waiting receive.
                pending = asyncio.ensure_future(dealers[0].recv(timeout=TIMEOUT))
                await asyncio.sleep(0)
            with pytest.raises(SocketClosedError):
                await pending

    await one_lifetime()
    tasks_before = len(asyncio.all_tasks())
    fds_before = _open_fds()
    for _ in range(10):
        await one_lifetime()
    await asyncio.sleep(0)
    assert len(asyncio.all_tasks()) == tasks_before
    assert _open_fds() == fds_before


@pytest.mark.asyncs('asyncio')
async def test_in_house_idle_socket_runs_no_polling_tasks():
    before = asyncio.all_tasks()
    async with new_backend('pipelines') as be:
        router = be.create_router()
        dealer = be.create_dealer(routing_id=b'd')
        await dealer.connect((await router.bind('tcp://127.0.0.1:*')).address)
        await dealer.send((b'x',))
        await router.recv(timeout=TIMEOUT)

        # Idle and connected: the listener, the connector, and per connection its run task and its driver's read task -
        # and nothing timed. The handshake deadlines were cancelled on readiness.
        tasks = sorted(t.get_coro().__qualname__ for t in asyncio.all_tasks() - before)  # type: ignore[union-attr]
        assert tasks == sorted([
            'ListenerAttachment._run',
            'ConnectorAttachment._run',
            'Connection._run',
            'Connection._run',
            'PollAsyncioStreamIoPipelineDriver._read_task_main',
            'PollAsyncioStreamIoPipelineDriver._read_task_main',
        ])
        loop = asyncio.get_running_loop()
        assert [h for h in getattr(loop, '_scheduled', []) if not h.cancelled()] == []


@pytest.mark.parametrize('backend_name', BACKENDS)
@pytest.mark.asyncs('asyncio')
async def test_ipc_cleanup_only_removes_its_own_entry(backend_name):
    with short_tmp_dir() as tmp:
        path = os.path.join(tmp, 'ep')
        async with new_backend(backend_name) as be:
            router = be.create_router()
            att = await router.bind(f'ipc://{path}')
            await att.aclose()
            assert not os.path.exists(path)

            # Replaced between bind and cleanup: the replacement is left alone, whether by removing the attachment or by
            # closing the socket.
            for close_socket in (False, True):
                att = await router.bind(f'ipc://{path}')
                os.unlink(path)
                other = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                other.bind(path)
                try:
                    if close_socket:
                        await router.aclose()
                    else:
                        await att.aclose()
                    assert os.path.exists(path)
                finally:
                    other.close()
                    os.unlink(path)
