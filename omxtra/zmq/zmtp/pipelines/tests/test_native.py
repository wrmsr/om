"""The codec and handshake stages under the asyncio driver over real TCP, against unwrapped native sockets."""
import asyncio
import typing as ta

import pytest

from omcore import lang
from omcore.io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from omcore.testing.pytest import skip

from ....core.sockettypes import SocketType
from ..messages import ZmtpMessage
from ..messages import ZmtpPeerReady
from .harness import Collector
from .harness import Send
from .harness import zmtp_spec


with lang.auto_proxy_import(globals()):
    import zmq
    import zmq.asyncio


TIMEOUT = 10.


class _Peer:
    """A pipeline-driven ZMTP connection, with a way to wait for what it collects."""

    def __init__(self, socket_type: SocketType, *, identity: bytes = b'') -> None:
        super().__init__()

        self.changed = asyncio.Event()
        self.collector = Collector(on_change=self.changed.set)
        self.spec = zmtp_spec(self.collector, socket_type, identity=identity, timeout_s=TIMEOUT)
        self.driver: PollAsyncioStreamIoPipelineDriver | None = None
        self.task: asyncio.Task | None = None

    def start(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.driver = PollAsyncioStreamIoPipelineDriver(self.spec, reader, writer)
        self.task = asyncio.create_task(self.driver.loop_until_done())

    async def wait_for(self, pred: ta.Callable[[Collector], bool]) -> None:
        async with asyncio.timeout(TIMEOUT):
            while not pred(self.collector):
                self.changed.clear()
                await self.changed.wait()

    async def messages(self, n: int) -> list[ZmtpMessage]:
        await self.wait_for(lambda c: len(c.of_type(ZmtpMessage)) >= n)
        return self.collector.of_type(ZmtpMessage)[:n]

    def send(self, *frames_list: tuple[bytes, ...]) -> None:
        ta.cast(PollAsyncioStreamIoPipelineDriver, self.driver).enqueue(Send([ZmtpMessage(f) for f in frames_list]))

    async def close(self) -> None:
        if self.driver is not None:
            await self.driver.close()
        if self.task is not None:
            await asyncio.gather(self.task, return_exceptions=True)


class _Native:
    def __init__(self) -> None:
        super().__init__()

        self.ctx = zmq.asyncio.Context()
        self.socks: list[zmq.asyncio.Socket] = []

    def socket(self, t: int, **opts: ta.Any) -> zmq.asyncio.Socket:
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


class _Server:
    """Accepts connections, driving each with a pipeline peer of the given type."""

    def __init__(self, socket_type: SocketType) -> None:
        super().__init__()

        self._socket_type = socket_type
        self.peers: list[_Peer] = []
        self._accepted = asyncio.Event()
        self._server: asyncio.Server | None = None

    def _on_connect(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        p = _Peer(self._socket_type)
        p.start(reader, writer)
        self.peers.append(p)
        self._accepted.set()

    async def start(self) -> int:
        self._server = await asyncio.start_server(self._on_connect, '127.0.0.1', 0)
        return self._server.sockets[0].getsockname()[1]

    async def accepted(self) -> _Peer:
        async with asyncio.timeout(TIMEOUT):
            await self._accepted.wait()
        return self.peers[0]

    async def close(self) -> None:
        for p in self.peers:
            await p.close()
        if (server := self._server) is not None:
            server.close()
            await server.wait_closed()


async def _recv(s: zmq.asyncio.Socket) -> list[bytes]:
    async with asyncio.timeout(TIMEOUT):
        return await s.recv_multipart()


def _port(s: zmq.asyncio.Socket) -> int:
    return int(s.getsockopt_string(zmq.LAST_ENDPOINT).rsplit(':', 1)[1])


##


@skip.if_cant_import('zmq')
@pytest.mark.asyncs('asyncio')
async def test_pipeline_dealer_connects_to_native_router():
    native = _Native()
    peer = _Peer(SocketType.DEALER, identity=b'pipeline-dealer')
    try:
        router = native.socket(zmq.ROUTER, ROUTER_MANDATORY=1, ROUTING_ID=b'native-router')
        router.bind('tcp://127.0.0.1:*')
        peer.start(*await asyncio.open_connection('127.0.0.1', _port(router)))

        await peer.wait_for(lambda c: bool(c.of_type(ZmtpPeerReady)))
        (ready,) = peer.collector.of_type(ZmtpPeerReady)
        assert (ready.socket_type, ready.identity) == (SocketType.ROUTER, b'native-router')

        peer.send((b'hello', b'', b'world'), (b'second',))
        assert await _recv(router) == [b'pipeline-dealer', b'hello', b'', b'world']
        assert await _recv(router) == [b'pipeline-dealer', b'second']

        await router.send_multipart([b'pipeline-dealer', b'reply', b''])
        await router.send_multipart([b'pipeline-dealer', b'\x00\x01'])
        assert await peer.messages(2) == [ZmtpMessage((b'reply', b'')), ZmtpMessage((b'\x00\x01',))]
        assert not peer.collector.errors

    finally:
        await peer.close()
        native.close()


@skip.if_cant_import('zmq')
@pytest.mark.asyncs('asyncio')
async def test_native_dealer_connects_to_pipeline_router():
    native = _Native()
    server = _Server(SocketType.ROUTER)
    try:
        dealer = native.socket(zmq.DEALER)
        dealer.connect(f'tcp://127.0.0.1:{await server.start()}')

        # The native dealer sends no identity, so its route is for the router to generate.
        await dealer.send_multipart([b'a', b'b'])
        peer = await server.accepted()
        assert await peer.messages(1) == [ZmtpMessage((b'a', b'b'))]
        (ready,) = peer.collector.of_type(ZmtpPeerReady)
        assert (ready.socket_type, ready.identity) == (SocketType.DEALER, b'')

        peer.send((b'back',))
        assert await _recv(dealer) == [b'back']

    finally:
        await server.close()
        native.close()


@skip.if_cant_import('zmq')
@pytest.mark.asyncs('asyncio')
async def test_native_sub_subscriptions_reach_pipeline_pub_as_3_0_messages():
    # libzmq advertises ZMTP 3.1; against this side's 3.0 greeting it must send subscriptions as data messages, not 3.1
    # SUBSCRIBE and CANCEL commands.
    native = _Native()
    server = _Server(SocketType.PUB)
    try:
        sub = native.socket(zmq.SUB)
        sub.connect(f'tcp://127.0.0.1:{await server.start()}')
        sub.setsockopt(zmq.SUBSCRIBE, b'topic')
        sub.setsockopt(zmq.SUBSCRIBE, b'')
        sub.setsockopt(zmq.UNSUBSCRIBE, b'topic')

        peer = await server.accepted()
        assert await peer.messages(3) == [
            ZmtpMessage((b'\x01topic',)),
            ZmtpMessage((b'\x01',)),
            ZmtpMessage((b'\x00topic',)),
        ]

        peer.send((b'anything', b'payload'))
        assert await _recv(sub) == [b'anything', b'payload']

    finally:
        await server.close()
        native.close()


@skip.if_cant_import('zmq')
@pytest.mark.asyncs('asyncio')
async def test_pipeline_sub_subscribes_to_native_xpub():
    native = _Native()
    peer = _Peer(SocketType.SUB)
    try:
        xpub = native.socket(zmq.XPUB)
        xpub.bind('tcp://127.0.0.1:*')
        peer.start(*await asyncio.open_connection('127.0.0.1', _port(xpub)))
        await peer.wait_for(lambda c: bool(c.of_type(ZmtpPeerReady)))

        peer.send((b'\x01news',))
        assert await _recv(xpub) == [b'\x01news']

        await xpub.send_multipart([b'news', b'item'])
        assert await peer.messages(1) == [ZmtpMessage((b'news', b'item'))]

        peer.send((b'\x00news',))
        assert await _recv(xpub) == [b'\x00news']

    finally:
        await peer.close()
        native.close()


@skip.if_cant_import('zmq')
@pytest.mark.asyncs('asyncio')
async def test_native_rejects_incompatible_pipeline_peer():
    native = _Native()
    peer = _Peer(SocketType.DEALER)
    try:
        pub = native.socket(zmq.PUB)
        pub.bind('tcp://127.0.0.1:*')
        peer.start(*await asyncio.open_connection('127.0.0.1', _port(pub)))

        # Both sides refuse: whichever notices first, this side's handshake fails or the connection ends.
        await peer.wait_for(lambda c: bool(c.errors) or c.final_input)
        assert not peer.collector.of_type(ZmtpPeerReady)

    finally:
        await peer.close()
        native.close()
