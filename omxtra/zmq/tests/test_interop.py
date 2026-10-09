"""
Backends against each other, and the in-house backend against unwrapped native sockets, over TCP and IPC in both bind
directions.
"""
import asyncio
import contextlib
import itertools
import os
import typing as ta

import pytest

from omcore import lang
from omcore.testing.pytest import skip

from ..api.backends import Backend
from ..api.errors import AddressInUseError
from ..api.errors import UnroutableError
from ..api.messages import RoutedMessage
from .support import TIMEOUT
from .support import await_subscribed
from .support import backend_names
from .support import new_backend
from .support import recv_skipping_probes
from .support import short_tmp_dir


with lang.auto_proxy_import(globals()):
    import zmq
    import zmq.asyncio


PAIRS = [(a, b) for a, b in itertools.product(backend_names(), repeat=2) if a != b]


@contextlib.asynccontextmanager
async def _backends(*names: str) -> ta.AsyncIterator[list[Backend]]:
    bes = [new_backend(n) for n in names]
    try:
        yield bes
    finally:
        for be in bes:
            await be.aclose()


def _addr(transport: str, tmp: str) -> str:
    return 'tcp://127.0.0.1:*' if transport == 'tcp' else f'ipc://{os.path.join(tmp, "ep")}'


##


@pytest.mark.parametrize('transport', ['tcp', 'ipc'])
@pytest.mark.parametrize(('binder', 'connector'), PAIRS)
@pytest.mark.asyncs('asyncio')
async def test_dealer_router_across_backends(binder, connector, transport):
    for router_side in ('binder', 'connector'):
        with short_tmp_dir() as tmp:
            async with _backends(binder, connector) as (bb, cb):
                rbe, dbe = (bb, cb) if router_side == 'binder' else (cb, bb)
                router = rbe.create_router(routing_id=b'the-router')
                dealer = dbe.create_dealer(routing_id=b'the-dealer')
                b, c = (router, dealer) if router_side == 'binder' else (dealer, router)
                await c.connect((await b.bind(_addr(transport, tmp))).address)

                await dealer.send((b'ping', b'', b'\x00'))
                assert await router.recv(timeout=TIMEOUT) == RoutedMessage(b'the-dealer', (b'ping', b'', b'\x00'))
                await router.send(b'the-dealer', (b'pong',))
                assert await dealer.recv(timeout=TIMEOUT) == (b'pong',)

                big = (os.urandom(3 * 1024 * 1024), b'tail')
                await dealer.send(big)
                assert (await router.recv(timeout=TIMEOUT)).message == big


@pytest.mark.parametrize(('binder', 'connector'), PAIRS)
@pytest.mark.asyncs('asyncio')
async def test_router_router_and_dealer_dealer_across_backends(binder, connector):
    async with _backends(binder, connector) as (bb, cb):
        r1 = bb.create_router(routing_id=b'r1')
        r2 = cb.create_router(routing_id=b'r2')
        await r2.connect((await r1.bind('tcp://127.0.0.1:*')).address)

        # A router learns a route only when the handshake completes, which nothing in the shared contract signals: retry
        # the unroutable send, boundedly.
        async with asyncio.timeout(TIMEOUT):
            while True:
                try:
                    await r2.send(b'r1', (b'hello r1',))
                    break
                except UnroutableError:
                    await asyncio.sleep(.01)
        assert await r1.recv(timeout=TIMEOUT) == RoutedMessage(b'r2', (b'hello r1',))
        await r1.send(b'r2', (b'hello r2',))
        assert await r2.recv(timeout=TIMEOUT) == RoutedMessage(b'r1', (b'hello r2',))

        d1 = bb.create_dealer()
        d2 = cb.create_dealer()
        await d2.connect((await d1.bind('tcp://127.0.0.1:*')).address)
        await d2.send((b'a',))
        await d1.send((b'b',))
        assert await d1.recv(timeout=TIMEOUT) == (b'a',)
        assert await d2.recv(timeout=TIMEOUT) == (b'b',)


@pytest.mark.parametrize('transport', ['tcp', 'ipc'])
@pytest.mark.parametrize(('binder', 'connector'), PAIRS)
@pytest.mark.asyncs('asyncio')
async def test_pub_sub_across_backends(binder, connector, transport):
    for pub_side in ('binder', 'connector'):
        with short_tmp_dir() as tmp:
            async with _backends(binder, connector) as (bb, cb):
                pbe, sbe = (bb, cb) if pub_side == 'binder' else (cb, bb)
                pub = pbe.create_publisher()
                sub = sbe.create_subscriber()
                b, c = (pub, sub) if pub_side == 'binder' else (sub, pub)
                await c.connect((await b.bind(_addr(transport, tmp))).address)

                await sub.subscribe(b'x')
                await sub.subscribe(b'x')
                await sub.subscribe(b'y')
                await sub.unsubscribe(b'x')
                await sub.unsubscribe(b'y')
                await await_subscribed(pub, sub, b'x')
                await pub.send((b'y-not',))
                await pub.send((b'x-yes', b'part'))
                assert await recv_skipping_probes(sub) == (b'x-yes', b'part')


##


class _Native:
    def __init__(self) -> None:
        super().__init__()

        self.ctx = zmq.asyncio.Context()
        self.socks: list[ta.Any] = []

    def socket(self, t: int, **opts: ta.Any) -> ta.Any:
        s = self.ctx.socket(t)
        s.linger = 0
        for k, v in opts.items():
            s.setsockopt(getattr(zmq, k), v)
        self.socks.append(s)
        return s

    def close(self) -> None:
        for s in self.socks:
            s.close(linger=0)
        self.ctx.term()


async def _nrecv(s: ta.Any) -> list[bytes]:
    async with asyncio.timeout(TIMEOUT):
        return await s.recv_multipart()


@skip.if_cant_import('zmq')
@pytest.mark.parametrize('transport', ['tcp', 'ipc'])
@pytest.mark.asyncs('asyncio')
async def test_in_house_router_with_native_dealers(transport):
    native = _Native()
    try:
        with short_tmp_dir() as tmp:
            async with _backends('pipelines') as (be,):
                router = be.create_router()
                bound = await router.bind(_addr(transport, tmp))
                named = native.socket(zmq.DEALER, ROUTING_ID=b'named')
                anon = native.socket(zmq.DEALER)
                for s in (named, anon):
                    s.connect(str(bound.address))

                await named.send_multipart([b'from named', b''])
                await anon.send_multipart([b'from anon'])
                got: dict[bytes, RoutedMessage] = {}
                for _ in range(2):
                    rm = await router.recv(timeout=TIMEOUT)
                    got[rm.message[0]] = rm
                assert got[b'from named'] == RoutedMessage(b'named', (b'from named', b''))
                anon_route = got[b'from anon'].route
                assert anon_route[0] == 0

                await router.send(b'named', (b'to named',))
                await router.send(anon_route, (b'to anon', b'2'))
                assert await _nrecv(named) == [b'to named']
                assert await _nrecv(anon) == [b'to anon', b'2']
    finally:
        native.close()


@skip.if_cant_import('zmq')
@pytest.mark.asyncs('asyncio')
async def test_in_house_dealer_with_native_router():
    native = _Native()
    try:
        async with _backends('pipelines') as (be,):
            router = native.socket(zmq.ROUTER, ROUTER_MANDATORY=1)
            router.bind('tcp://127.0.0.1:*')
            dealer = be.create_dealer(routing_id=b'in-house')
            await dealer.connect(router.getsockopt_string(zmq.LAST_ENDPOINT))

            await dealer.send((b'one',))
            await dealer.send((b'two', b''))
            assert await _nrecv(router) == [b'in-house', b'one']
            assert await _nrecv(router) == [b'in-house', b'two', b'']
            await router.send_multipart([b'in-house', b'back'])
            assert await dealer.recv(timeout=TIMEOUT) == (b'back',)
    finally:
        native.close()


@skip.if_cant_import('zmq')
@pytest.mark.asyncs('asyncio')
async def test_in_house_subscriber_observed_by_native_xpub():
    native = _Native()
    try:
        async with _backends('pipelines') as (be,):
            xpub = native.socket(zmq.XPUB)
            xpub.bind('tcp://127.0.0.1:*')
            sub = be.create_subscriber()
            await sub.subscribe(b'early')  # replayed when the connection becomes ready
            await sub.connect(xpub.getsockopt_string(zmq.LAST_ENDPOINT))

            # The native publisher's view of subscriptions is the barrier: no probes needed.
            assert await _nrecv(xpub) == [b'\x01early']
            await sub.subscribe(b'late')
            assert await _nrecv(xpub) == [b'\x01late']

            await xpub.send_multipart([b'late-1'])
            await xpub.send_multipart([b'other'])
            await xpub.send_multipart([b'early-1', b'x'])
            assert await sub.recv(timeout=TIMEOUT) == (b'late-1',)
            assert await sub.recv(timeout=TIMEOUT) == (b'early-1', b'x')

            await sub.unsubscribe(b'late')
            assert await _nrecv(xpub) == [b'\x00late']
    finally:
        native.close()


@skip.if_cant_import('zmq')
@pytest.mark.asyncs('asyncio')
async def test_in_house_publisher_with_native_xsub_and_sub():
    native = _Native()
    try:
        async with _backends('pipelines') as (be,):
            pub = be.create_publisher()
            bound = await pub.bind('tcp://127.0.0.1:*')
            xsub = native.socket(zmq.XSUB)
            xsub.connect(str(bound.address))
            sub = native.socket(zmq.SUB)
            sub.connect(str(bound.address))
            sub.setsockopt(zmq.SUBSCRIBE, b'b')

            await xsub.send_multipart([b'\x01a'])
            # An XSUB may send other messages: never treated as publications.
            await xsub.send_multipart([b'not a subscription'])

            async with asyncio.timeout(TIMEOUT):
                while True:
                    await pub.send((b'a-probe',))
                    await pub.send((b'b-probe',))
                    a_ready = await xsub.poll(10) != 0
                    b_ready = await sub.poll(10) != 0
                    if a_ready and b_ready:
                        break
            for s in (xsub, sub):
                while await s.poll(50):
                    await s.recv_multipart()

            await pub.send((b'a-real', b'1'))
            await pub.send((b'b-real', b'2'))
            await pub.send((b'c-none',))
            assert await _nrecv(xsub) == [b'a-real', b'1']
            assert await _nrecv(sub) == [b'b-real', b'2']
    finally:
        native.close()


@pytest.mark.parametrize(('first', 'second'), PAIRS)
@pytest.mark.asyncs('asyncio')
async def test_cooperating_binders_never_take_each_others_ipc_path(first, second):
    with short_tmp_dir() as tmp:
        path = os.path.join(tmp, 'ep')
        async with _backends(first, second) as (fb, sb):
            holder = fb.create_router()
            att = await holder.bind(f'ipc://{path}')
            st = os.lstat(path)

            with pytest.raises(AddressInUseError):
                await sb.create_router().bind(f'ipc://{path}')
            assert os.path.samestat(os.lstat(path), st)

            d = sb.create_dealer(routing_id=b'd')
            await d.connect(f'ipc://{path}')
            await d.send((b'reaches the holder',))
            assert (await holder.recv(timeout=TIMEOUT)).message == (b'reaches the holder',)

            # Released, the path can be bound by the other.
            await att.aclose()
            await sb.create_router().bind(f'ipc://{path}')
