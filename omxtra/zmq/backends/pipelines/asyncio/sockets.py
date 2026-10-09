"""
Sockets of the in-house backend: an endpoint, the connections serving its peers, and its attachments, on one event loop.

Waiting operations check their condition and wait for a notification from the endpoint in a loop, taking a message only
in a step which does not suspend - so cancellation never loses a received message nor half-admits a sent one.
"""
import abc
import asyncio
import math
import typing as ta

from omcore import lang
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.flow.stub import StubIoPipelineFlowService

from ....api.addresses import AnyAddress
from ....api.addresses import check_bindable
from ....api.addresses import check_connectable
from ....api.configs import SocketConfig
from ....api.configs import resolve_timeout
from ....api.errors import ConcurrentReceiveError
from ....api.errors import SocketClosedError
from ....api.errors import WouldBlockError
from ....api.errors import ZmqTimeoutError
from ....api.messages import Message
from ....api.messages import RoutedMessage
from ....api.messages import check_message
from ....api.messages import check_route
from ....api.messages import check_subscription
from ....api.sockets import Attachment
from ....api.sockets import Dealer
from ....api.sockets import Publisher
from ....api.sockets import Router
from ....api.sockets import Socket
from ....api.sockets import Subscriber
from ....core.dealers import DealerEndpoint
from ....core.endpoints import Endpoint
from ....core.endpoints import EndpointConfig
from ....core.endpoints import EndpointListener
from ....core.publishers import PubEndpoint
from ....core.routers import RouterEndpoint
from ....core.subscribers import SubEndpoint
from ....zmtp.pipelines.codecs import ZmtpCodecConfig
from ....zmtp.pipelines.codecs import ZmtpCodecIoPipelineHandler
from ....zmtp.pipelines.handshakes import ZmtpHandshakeIoPipelineHandler
from ....zmtp.pipelines.sessions import ZmtpSessionIoPipelineHandler
from .attachments import ConnectorAttachment
from .attachments import ListenerAttachment
from .attachments import PipelinesAttachment
from .configs import PipelinesBackendConfig
from .connections import Connection
from .waiters import AsyncioNotifier


T = ta.TypeVar('T')


##


class _Listener(EndpointListener):
    def __init__(self, readable: AsyncioNotifier, writable: AsyncioNotifier) -> None:
        super().__init__()

        self._readable = readable
        self._writable = writable

    def on_readable(self) -> None:
        self._readable.notify()

    def on_writable(self) -> None:
        self._writable.notify()


class PipelinesSocket(Socket, lang.Abstract):
    def __init__(
            self,
            config: SocketConfig,
            backend_config: PipelinesBackendConfig,
            *,
            identity: bytes = b'',
            on_close: ta.Callable[[PipelinesSocket], None],
    ) -> None:
        super().__init__()

        self._config = config
        self._backend_config = backend_config
        self._identity = identity
        self._on_close = on_close

        self._readable = AsyncioNotifier()
        self._writable = AsyncioNotifier()
        self._endpoint = self._new_endpoint(_Listener(self._readable, self._writable))

        self._connections: dict[Connection, None] = {}
        self._attachments: dict[PipelinesAttachment, None] = {}
        self._connection_count = 0

        self._closed = False
        self._closed_fut: asyncio.Future[None] | None = None
        self._receiving = False
        self._waiting_sends = 0

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @abc.abstractmethod
    def _new_endpoint(self, listener: EndpointListener) -> Endpoint:
        raise NotImplementedError

    @property
    def config(self) -> SocketConfig:
        return self._config

    @property
    def endpoint(self) -> Endpoint:
        return self._endpoint

    def _endpoint_config(self) -> EndpointConfig:
        return EndpointConfig(
            limits=self._config.limits,
            send_queue_size=self._config.send_queue_size,
            recv_queue_size=self._config.recv_queue_size,
            max_queue_bytes=self._backend_config.max_queue_bytes,
            max_peers=self._backend_config.max_connections,
            max_peer_subscriptions=self._backend_config.max_peer_subscriptions,
        )

    #

    def _check_open(self) -> None:
        if self._closed:
            raise SocketClosedError

    def _deadline(self, timeout: float | None, default: float | None) -> float | None:
        if (t := resolve_timeout(timeout, default)) is None:
            return None
        return asyncio.get_running_loop().time() + t

    async def _recv(self, try_recv: ta.Callable[[], T | None], timeout: float | None) -> T:
        self._check_open()
        if self._receiving:
            raise ConcurrentReceiveError

        self._receiving = True
        try:
            deadline = self._deadline(timeout, self._config.recv_timeout)
            while True:
                generation = self._readable.generation
                if (r := try_recv()) is not None:
                    return r
                self._check_open()
                try:
                    await self._readable.wait(generation, deadline)
                except TimeoutError:
                    raise ZmqTimeoutError from None

        finally:
            self._receiving = False

    async def _send_waiting(self, try_send: ta.Callable[[], bool], timeout: float | None) -> None:
        deadline = self._deadline(timeout, self._config.send_timeout)
        while True:
            generation = self._writable.generation
            if try_send():
                return
            self._check_open()

            if self._waiting_sends >= self._backend_config.max_waiting_sends:
                raise WouldBlockError('too many waiting sends')
            self._waiting_sends += 1
            try:
                await self._writable.wait(generation, deadline)
            except TimeoutError:
                raise ZmqTimeoutError from None
            finally:
                self._waiting_sends -= 1

    #

    def _new_spec(self, session: ZmtpSessionIoPipelineHandler) -> IoPipeline.Spec:
        return IoPipeline.Spec(
            [
                ZmtpCodecIoPipelineHandler(ZmtpCodecConfig(
                    limits=self._config.limits,
                    max_command_size=self._backend_config.max_command_size,
                )),
                ZmtpHandshakeIoPipelineHandler(
                    self._endpoint.SOCKET_TYPE,
                    identity=self._identity,
                    timeout_s=None if math.isinf(self._config.handshake_timeout) else self._config.handshake_timeout,
                ),
                session,
            ],
            services=[StubIoPipelineFlowService(auto_read=False)],
        )

    def _start_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Connection | None:
        # Includes connections still in their handshake, which are not yet endpoint peers.
        if self._closed or len(self._connections) >= self._backend_config.max_connections:
            writer.transport.abort()
            return None

        self._connection_count += 1
        conn = Connection(
            reader,
            writer,
            endpoint=self._endpoint,
            new_spec=self._new_spec,
            turn_output_budget=self._backend_config.turn_output_budget,
            driver_config=self._backend_config.driver,
            on_done=self._on_connection_done,
            name=f'{self._endpoint.SOCKET_TYPE.value.lower()}-{id(self):x}-{self._connection_count}',
        )
        self._connections[conn] = None
        conn.start()
        return conn

    def _on_connection_done(self, conn: Connection) -> None:
        self._connections.pop(conn, None)

    def _on_attachment_closed(self, att: PipelinesAttachment) -> None:
        self._attachments.pop(att, None)

    async def bind(self, address: AnyAddress) -> Attachment:
        self._check_open()
        att = await ListenerAttachment.bind(check_bindable(address), self._start_connection)
        if self._closed:
            att.stop()
            raise SocketClosedError
        att.set_on_close(self._on_attachment_closed)
        self._attachments[att] = None
        return att

    async def connect(self, address: AnyAddress) -> Attachment:
        self._check_open()
        att = ConnectorAttachment(
            check_connectable(address),
            self._start_connection,
            connect_timeout=self._backend_config.connect_timeout,
            reconnect_interval=self._config.reconnect_interval,
            reconnect_interval_max=self._config.reconnect_interval_max,
        )
        att.set_on_close(self._on_attachment_closed)
        self._attachments[att] = None
        att.start()
        return att

    async def aclose(self) -> None:
        if self._closed:
            # A concurrent close returns only once the first has finished.
            if (fut := self._closed_fut) is not None:
                await asyncio.shield(fut)
            return
        self._closed = True
        self._closed_fut = asyncio.get_running_loop().create_future()
        try:
            await self._close()
        finally:
            self._closed_fut.set_result(None)

    async def _close(self) -> None:
        atts = list(self._attachments)
        self._attachments.clear()
        for att in atts:
            att.stop()

        # Drops every ready peer, aborting its connection, and wakes all waiters to find the socket closed.
        self._endpoint.close()

        conns = list(self._connections)
        for conn in conns:
            conn.abort()

        await asyncio.gather(
            *[att.wait_stopped() for att in atts],
            *[conn.wait_done() for conn in conns],
            return_exceptions=True,
        )
        self._on_close(self)


##


class PipelinesPublisher(PipelinesSocket, Publisher):
    _endpoint: PubEndpoint

    def _new_endpoint(self, listener: EndpointListener) -> Endpoint:
        return PubEndpoint(self._endpoint_config(), listener=listener)

    async def send(self, message: Message) -> None:
        self._check_open()
        self._endpoint.publish(check_message(message, self._config.limits))


class PipelinesSubscriber(PipelinesSocket, Subscriber):
    _endpoint: SubEndpoint

    def _new_endpoint(self, listener: EndpointListener) -> Endpoint:
        return SubEndpoint(self._endpoint_config(), listener=listener)

    async def subscribe(self, prefix: bytes) -> None:
        self._check_open()
        self._endpoint.subscribe(check_subscription(prefix, self._config.limits))

    async def unsubscribe(self, prefix: bytes) -> None:
        self._check_open()
        self._endpoint.unsubscribe(check_subscription(prefix, self._config.limits))

    async def recv(self, *, timeout: float | None = None) -> Message:
        return await self._recv(self._endpoint.recv, timeout)


class PipelinesDealer(PipelinesSocket, Dealer):
    _endpoint: DealerEndpoint

    def _new_endpoint(self, listener: EndpointListener) -> Endpoint:
        return DealerEndpoint(self._endpoint_config(), listener=listener)

    async def send(self, message: Message, *, timeout: float | None = None) -> None:
        self._check_open()
        msg = check_message(message, self._config.limits)
        await self._send_waiting(lambda: self._endpoint.try_send(msg), timeout)

    async def recv(self, *, timeout: float | None = None) -> Message:
        return await self._recv(self._endpoint.recv, timeout)


class PipelinesRouter(PipelinesSocket, Router):
    _endpoint: RouterEndpoint

    def _new_endpoint(self, listener: EndpointListener) -> Endpoint:
        return RouterEndpoint(self._endpoint_config(), listener=listener)

    async def send(self, route: bytes, message: Message) -> None:
        self._check_open()
        self._endpoint.send(check_route(route), check_message(message, self._config.limits))

    async def recv(self, *, timeout: float | None = None) -> RoutedMessage:
        return await self._recv(self._endpoint.recv, timeout)
