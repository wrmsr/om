"""Regression tests for defects found by an adversarial review."""
import asyncio
import math
import socket
import time

import pytest

from omcore import lang
from omcore.testing.pytest import skip

from ..api.configs import SocketConfig
from ..api.errors import WouldBlockError
from ..api.errors import ZmqTimeoutError
from ..api.messages import MessageLimits
from ..api.messages import RoutedMessage
from ..backends.pipelines.asyncio.backends import AsyncioPipelinesBackend
from ..backends.pipelines.asyncio.configs import PipelinesBackendConfig
from ..backends.pyzmq.backends import PyzmqBackend
from ..backends.selection import new_backend
from ..core.sockettypes import SocketType
from ..zmtp.commands import encode_ready
from ..zmtp.frames import encode_command_frame
from ..zmtp.frames import encode_frame_header
from ..zmtp.greetings import ZmtpGreeting
from ..zmtp.greetings import encode_greeting


with lang.auto_proxy_import(globals()):
    import zmq
    import zmq.asyncio


##


@skip.if_cant_import('zmq')
@pytest.mark.parametrize('heartbeat', [False, True])
@pytest.mark.asyncs('asyncio')
async def test_native_heartbeat_pings_do_not_stall_connections(heartbeat):
    """A read batch holding only a command - a native heartbeat PING - still leads to the next read."""

    ctx = zmq.asyncio.Context()
    be = AsyncioPipelinesBackend()
    try:
        router = be.create_router()
        bound = await router.bind('tcp://127.0.0.1:*')

        dealer = ctx.socket(zmq.DEALER)
        dealer.linger = 0
        dealer.setsockopt(zmq.ROUTING_ID, b'native')
        if heartbeat:
            dealer.setsockopt(zmq.HEARTBEAT_IVL, 20)
            # Never time out waiting for a PONG, so the native side keeps the connection up.
            dealer.setsockopt(zmq.HEARTBEAT_TIMEOUT, 60_000)
        dealer.connect(str(bound.address))

        await dealer.send_multipart([b'first'])
        assert await router.recv(timeout=5) == RoutedMessage(b'native', (b'first',))

        # Let the native side send a few PINGs, each arriving in a read batch of its own.
        await asyncio.sleep(.3)

        await dealer.send_multipart([b'second'])
        assert await router.recv(timeout=5) == RoutedMessage(b'native', (b'second',))

    finally:
        await be.aclose()
        ctx.destroy(linger=0)


@pytest.mark.asyncs('asyncio')
async def test_connector_retries_after_a_refusal_at_the_connection_limit():
    """A connection refused at the socket's connection limit, which is temporary, is retried."""

    be = AsyncioPipelinesBackend(PipelinesBackendConfig(max_connections=1))
    other = AsyncioPipelinesBackend()
    try:
        ra = other.create_router()
        rb = other.create_router()
        aa = await ra.bind('tcp://127.0.0.1:*')
        ab = await rb.bind('tcp://127.0.0.1:*')

        dealer = be.create_dealer(routing_id=b'd')
        await dealer.connect(aa.address)
        await dealer.send((b'to a',), timeout=5)
        assert (await ra.recv(timeout=5)).message == (b'to a',)

        # The only connection slot is taken: this connection attempt is refused locally.
        await dealer.connect(ab.address)
        await asyncio.sleep(.3)

        # Free the slot. The connector to B should retry and connect.
        await ra.aclose()

        await dealer.send((b'to b',), timeout=5)
        assert (await rb.recv(timeout=5)).message == (b'to b',)

    finally:
        await be.aclose()
        await other.aclose()


@skip.if_cant_import('zmq')
@pytest.mark.parametrize('backend', ['pipelines', 'pyzmq'])
@pytest.mark.asyncs('asyncio')
async def test_messages_received_before_peer_disconnect_are_still_delivered(backend):
    """Messages received whole before the peer disconnected stay receivable, on both backends."""

    ctx = zmq.asyncio.Context()
    be = new_backend(backend)
    try:
        router = be.create_router()
        bound = await router.bind('tcp://127.0.0.1:*')

        dealer = ctx.socket(zmq.DEALER)
        dealer.setsockopt(zmq.ROUTING_ID, b'client')
        dealer.setsockopt(zmq.LINGER, 5_000)
        dealer.connect(str(bound.address))
        for i in range(3):
            await dealer.send_multipart([b'msg-%d' % i])
        # A linger close flushes everything first: the router receives all three, then sees the disconnect.
        dealer.close()

        await asyncio.sleep(.5)

        got = [(await router.recv(timeout=2)).message for _ in range(3)]
        assert got == [(b'msg-0',), (b'msg-1',), (b'msg-2',)]

    finally:
        await be.aclose()
        ctx.destroy(linger=0)


@pytest.mark.asyncs('asyncio')
async def test_closing_right_after_an_accept():
    """Closing while an accept is in flight, at any point of it, completes and leaves no transport behind."""

    for spins in range(12):
        be = AsyncioPipelinesBackend()
        router = be.create_router()
        bound = await router.bind('tcp://127.0.0.1:*')

        client = socket.create_connection((bound.address.host, bound.address.port))  # type: ignore[attr-defined]
        try:
            # Let the accept get partway: the loop accepts, builds the transport, then calls back into the socket.
            for _ in range(spins):
                await asyncio.sleep(0)

            try:
                async with asyncio.timeout(2):
                    await router.aclose()
            except TimeoutError:
                raise AssertionError(f'aclose hung after {spins} loop turns') from None

        finally:
            client.close()


def _raw_frames(*frames: bytes) -> bytes:

    return b''.join(encode_frame_header(len(f), more=i < len(frames) - 1) + f for i, f in enumerate(frames))


def _raw_dealer_handshake(identity: bytes) -> bytes:

    ready = encode_ready(SocketType.DEALER, identity=identity)
    return encode_greeting(ZmtpGreeting()) + encode_command_frame(ready.name, ready.data)


@pytest.mark.asyncs('asyncio')
async def test_peer_eof_with_unread_output_ends_the_connection():
    """A peer which closes without reading frees its connection: output it will never read does not hold it open."""

    be = AsyncioPipelinesBackend(PipelinesBackendConfig(max_connections=1))
    other = AsyncioPipelinesBackend()
    raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        router = be.create_router(SocketConfig(send_queue_size=1))
        bound = await router.bind('tcp://127.0.0.1:*')

        raw.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
        raw.connect((bound.address.host, bound.address.port))  # type: ignore[attr-defined]
        raw.sendall(_raw_dealer_handshake(b'raw') + _raw_frames(b'request'))
        assert await router.recv(timeout=5) == RoutedMessage(b'raw', (b'request',))

        # Reply far more than the peer will ever read.
        big = (b'x' * (1024 * 1024),)
        for _ in range(40):
            try:
                await router.send(b'raw', big)
            except WouldBlockError:
                pass
            await asyncio.sleep(.01)

        # The peer ends its side - without ever reading.
        raw.shutdown(socket.SHUT_WR)

        # Its connection should end; the only slot is then free for this dealer.
        dealer = other.create_dealer(routing_id=b'second')
        await dealer.connect(bound.address)
        await dealer.send((b'hello',), timeout=5)
        assert await router.recv(timeout=8) == RoutedMessage(b'second', (b'hello',))

    finally:
        raw.close()
        await be.aclose()
        await other.aclose()


@pytest.mark.asyncs('asyncio')
async def test_closing_a_connect_attachment_then_its_socket():
    """Closing a connect attachment, then the socket, completes."""

    be = AsyncioPipelinesBackend()
    try:
        router = be.create_router()
        bound = await router.bind('tcp://127.0.0.1:*')

        dealer = be.create_dealer(routing_id=b'd')
        att = await dealer.connect(bound.address)
        await dealer.send((b'hi',), timeout=5)
        assert (await router.recv(timeout=5)).message == (b'hi',)

        await att.aclose()
        try:
            async with asyncio.timeout(3):
                await dealer.aclose()
        except TimeoutError:
            raise AssertionError('dealer.aclose() hung') from None

    finally:
        try:
            async with asyncio.timeout(3):
                await be.aclose()
        except TimeoutError:
            pass


@skip.if_cant_import('zmq')
@pytest.mark.asyncs('asyncio')
async def test_pyzmq_recv_deadline_holds_across_dropped_messages():
    """Discarding over-limit messages does not push back a receive's deadline."""

    ctx = zmq.asyncio.Context()
    be = PyzmqBackend()
    try:
        router = ctx.socket(zmq.ROUTER)
        router.linger = 0
        router.bind('tcp://127.0.0.1:*')

        dealer = be.create_dealer(SocketConfig(limits=MessageLimits(max_frames=1)), routing_id=b'd')
        await dealer.connect(router.getsockopt_string(zmq.LAST_ENDPOINT))
        await dealer.send((b'hello',), timeout=5)
        assert await router.recv_multipart() == [b'd', b'hello']

        async def trickle():
            for _ in range(30):
                await router.send_multipart([b'd', b'two', b'frames'])
                await asyncio.sleep(.05)

        task = asyncio.create_task(trickle())
        start = time.monotonic()
        with pytest.raises(ZmqTimeoutError):
            await dealer.recv(timeout=.3)
        elapsed = time.monotonic() - start
        await task

        assert elapsed < 1., f'recv(timeout=.3) took {elapsed:.2f}s to time out'

    finally:
        await be.aclose()
        ctx.destroy(linger=0)


@skip.if_cant_import('zmq')
@pytest.mark.parametrize('backend', ['pipelines', 'pyzmq'])
@pytest.mark.asyncs('asyncio')
async def test_infinite_config_intervals_accepted_by_both_backends(backend):
    """Unbounded intervals are accepted by both backends."""

    be = new_backend(backend)
    try:
        cfg = SocketConfig(handshake_timeout=math.inf, reconnect_interval_max=math.inf)
        router = be.create_router(cfg)
        bound = await router.bind('tcp://127.0.0.1:*')
        dealer = be.create_dealer(cfg, routing_id=b'd')
        await dealer.connect(bound.address)
        await dealer.send((b'x',), timeout=5)
        assert await router.recv(timeout=5) == RoutedMessage(b'd', (b'x',))
    finally:
        await be.aclose()


@pytest.mark.parametrize('backend', [n for n in ('pipelines', 'pyzmq') if n != 'pyzmq' or lang.can_import('zmq')])
@pytest.mark.asyncs('asyncio')
async def test_concurrent_closes_both_wait_for_the_close(backend):
    be = new_backend(backend)
    try:
        router = be.create_router()
        await router.bind('tcp://127.0.0.1:*')
        first = asyncio.ensure_future(router.aclose())
        await asyncio.sleep(0)
        await router.aclose()
        assert router not in be._sockets  # type: ignore[attr-defined]  # noqa
        await first
    finally:
        await be.aclose()
