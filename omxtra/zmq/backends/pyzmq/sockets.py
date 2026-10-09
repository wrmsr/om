"""
Sockets adapting `zmq.asyncio` sockets to the shared interfaces.

Every native send and receive is non-blocking and synchronous, made through a synchronous shadow of the native socket -
a whole multipart message is sent or received in one step, or not at all. Waiting is done separately by polling the
asyncio socket, which consumes nothing, so cancelling a waiting operation never loses or splits a message.
"""
import asyncio
import errno
import os
import typing as ta

from omcore import check
from omcore import lang
from omcore.logs import all as logs

from ...api.addresses import Address
from ...api.addresses import AnyAddress
from ...api.addresses import IpcAddress
from ...api.addresses import TcpAddress
from ...api.addresses import check_bindable
from ...api.addresses import check_connectable
from ...api.addresses import parse_address
from ...api.configs import SocketConfig
from ...api.configs import resolve_timeout
from ...api.errors import AddressInUseError
from ...api.errors import ConcurrentReceiveError
from ...api.errors import InvalidMessageError
from ...api.errors import SocketClosedError
from ...api.errors import TransportError
from ...api.errors import UnroutableError
from ...api.errors import WouldBlockError
from ...api.errors import ZmqTimeoutError
from ...api.messages import Message
from ...api.messages import RoutedMessage
from ...api.messages import check_message
from ...api.messages import check_route
from ...api.messages import check_subscription
from ...api.sockets import Attachment
from ...api.sockets import Dealer
from ...api.sockets import Publisher
from ...api.sockets import Router
from ...api.sockets import Socket
from ...api.sockets import Subscriber
from ...ipc.ownership import IpcEntry
from ...ipc.ownership import IpcLease
from ...ipc.ownership import IpcLeaseHeldError
from ...ipc.ownership import record_ipc_entry
from ...ipc.ownership import unlink_ipc_entry_if_owned


with lang.auto_proxy_import(globals()):
    import zmq
    import zmq.asyncio


log = logs.get_module_logger(globals())


##


def _translate_zmq_error(e: BaseException) -> Exception:
    if isinstance(e, zmq.ZMQError):
        if e.errno == zmq.EADDRINUSE:
            return AddressInUseError(str(e))
        if e.errno == zmq.EHOSTUNREACH:
            return UnroutableError(str(e))
    return TransportError(str(e))


def _acquire_ipc_lease(path: str) -> IpcLease:
    try:
        return IpcLease.acquire(path)
    except IpcLeaseHeldError as e:
        raise AddressInUseError(f'path is leased by another binder: {path}') from e
    except OSError as e:
        raise TransportError(str(e)) from e


class PyzmqAttachment(Attachment):
    def __init__(
            self,
            sock: PyzmqSocket,
            *,
            kind: ta.Literal['bind', 'connect'],
            address: Address,
            endpoint: str,
            ipc_entry: IpcEntry | None = None,
            ipc_lease: IpcLease | None = None,
    ) -> None:
        super().__init__()

        self._sock = sock
        self._kind = kind
        self._address = address
        self._endpoint = endpoint
        self._ipc_entry = ipc_entry
        self._ipc_lease = ipc_lease

    def __repr__(self) -> str:
        return f'{type(self).__name__}<{self._kind} {self._endpoint}>'

    @property
    def kind(self) -> ta.Literal['bind', 'connect']:
        return self._kind

    @property
    def address(self) -> Address:
        return self._address

    @property
    def endpoint(self) -> str:
        return self._endpoint

    def release_ipc(self) -> None:
        # Native sockets leave a bound IPC path behind, removing stale ones before binding instead - which this side
        # never lets them do - so the wrapper removes its own entry, then gives up its lease.
        if (entry := self._ipc_entry) is not None:
            self._ipc_entry = None
            unlink_ipc_entry_if_owned(entry)
        if (lease := self._ipc_lease) is not None:
            self._ipc_lease = None
            lease.release()

    async def aclose(self) -> None:
        await self._sock._remove_attachment(self)  # noqa


class PyzmqSocket(Socket, lang.Abstract):
    def __init__(
            self,
            zsock: zmq.asyncio.Socket,
            config: SocketConfig,
            *,
            on_close: ta.Callable[[PyzmqSocket], None],
    ) -> None:
        super().__init__()

        self._zsock = zsock
        self._sync: zmq.Socket = zmq.Socket.shadow(zsock.underlying)
        self._config = config
        self._on_close = on_close

        self._closed = False
        self._closed_fut: asyncio.Future[None] | None = None
        self._receiving = False
        self._attachments: list[PyzmqAttachment] = []
        self._dropped_oversized = 0

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def config(self) -> SocketConfig:
        return self._config

    @property
    def dropped_oversized(self) -> int:
        """Received messages discarded for exceeding the message limits."""

        return self._dropped_oversized

    #

    def _check_open(self) -> None:
        if self._closed:
            raise SocketClosedError

    def _deadline(self, timeout: float | None, default: float | None) -> float | None:
        if (t := resolve_timeout(timeout, default)) is None:
            return None
        return asyncio.get_running_loop().time() + t

    async def _wait(self, event: int, deadline: float | None) -> None:
        loop = asyncio.get_running_loop()

        remaining: float | None = None
        if deadline is not None:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise ZmqTimeoutError

        if (closed_fut := self._closed_fut) is None:
            closed_fut = self._closed_fut = loop.create_future()

        # The stubs omit poll's flags parameter.
        poll_fut: asyncio.Future = asyncio.ensure_future(ta.cast(ta.Any, self._zsock).poll(None, event))
        try:
            await asyncio.wait([poll_fut, closed_fut], timeout=remaining, return_when=asyncio.FIRST_COMPLETED)
        finally:
            if not poll_fut.done():
                poll_fut.cancel()

        self._check_open()

        if poll_fut.done() and not poll_fut.cancelled() and (e := poll_fut.exception()) is not None:
            raise _translate_zmq_error(e) from e

    #

    def _try_send(self, frames: ta.Sequence[bytes]) -> bool:
        try:
            self._sync.send_multipart(frames, flags=zmq.NOBLOCK)
        except zmq.Again:
            return False
        except zmq.ZMQError as e:
            raise _translate_zmq_error(e) from e
        return True

    async def _send_waiting(self, frames: ta.Sequence[bytes], timeout: float | None) -> None:
        deadline = self._deadline(timeout, self._config.send_timeout)
        while not self._try_send(frames):
            await self._wait(zmq.POLLOUT, deadline)

    def _try_recv(self) -> list[bytes] | None:
        try:
            return self._sync.recv_multipart(flags=zmq.NOBLOCK)
        except zmq.Again:
            return None
        except zmq.ZMQError as e:
            raise _translate_zmq_error(e) from e

    def _check_received(self, frames: ta.Sequence[bytes]) -> Message | None:
        try:
            return check_message(tuple(frames), self._config.limits)
        except InvalidMessageError as e:
            self._dropped_oversized += 1
            log.warning('Dropping received message exceeding limits: %s: %s', self, e)
            return None

    async def _recv_frames(self, deadline: float | None) -> list[bytes]:
        self._check_open()
        if self._receiving:
            raise ConcurrentReceiveError

        self._receiving = True
        try:
            while True:
                if (frames := self._try_recv()) is not None:
                    return frames
                await self._wait(zmq.POLLIN, deadline)

        finally:
            self._receiving = False

    #

    async def _remove_attachment(self, att: PyzmqAttachment) -> None:
        if self._closed or att not in self._attachments:
            return

        self._attachments.remove(att)
        try:
            if att.kind == 'bind':
                self._sync.unbind(att.endpoint)
            else:
                self._sync.disconnect(att.endpoint)
        except zmq.ZMQError as e:
            if e.errno != errno.ENOENT:
                raise _translate_zmq_error(e) from e
        finally:
            att.release_ipc()

    def _native_endpoint(self, addr: Address, *, bind: bool) -> str:
        if isinstance(addr, TcpAddress):
            if addr.is_ipv6:
                self._sync.setsockopt(zmq.IPV6, 1)
            host = f'[{addr.host}]' if addr.is_ipv6 else addr.host
            port = '*' if (bind and addr.is_ephemeral) else str(addr.port)
            return f'tcp://{host}:{port}'

        elif isinstance(addr, IpcAddress):
            return str(addr)

        else:
            raise TypeError(addr)

    async def bind(self, address: AnyAddress) -> Attachment:
        self._check_open()
        addr = check_bindable(address)

        lease: IpcLease | None = None
        if isinstance(addr, IpcAddress):
            lease = _acquire_ipc_lease(addr.path)
            if os.path.lexists(addr.path):
                # Native binding unlinks an existing path first - never let it remove something not ours.
                lease.release()
                raise AddressInUseError(f'path already exists: {addr.path}')

        endpoint = self._native_endpoint(addr, bind=True)
        try:
            self._sync.bind(endpoint)
        except BaseException as e:
            if lease is not None:
                lease.release()
            if isinstance(e, zmq.ZMQError):
                raise _translate_zmq_error(e) from e
            raise

        actual = self._sync.getsockopt_string(zmq.LAST_ENDPOINT)
        ipc_entry = record_ipc_entry(addr.path) if isinstance(addr, IpcAddress) else None
        att = PyzmqAttachment(
            self,
            kind='bind',
            address=parse_address(actual),
            endpoint=actual,
            ipc_entry=ipc_entry,
            ipc_lease=lease,
        )
        self._attachments.append(att)
        return att

    async def connect(self, address: AnyAddress) -> Attachment:
        self._check_open()
        addr = check_connectable(address)

        endpoint = self._native_endpoint(addr, bind=False)
        try:
            self._sync.connect(endpoint)
        except zmq.ZMQError as e:
            raise _translate_zmq_error(e) from e

        att = PyzmqAttachment(self, kind='connect', address=addr, endpoint=endpoint)
        self._attachments.append(att)
        return att

    async def aclose(self) -> None:
        if self._closed:
            return

        self._closed = True
        if (fut := self._closed_fut) is not None and not fut.done():
            fut.set_result(None)

        atts = list(self._attachments)
        self._attachments.clear()
        self._zsock.close(linger=0)
        self._on_close(self)

        for att in atts:
            att.release_ipc()


##


class PyzmqPublisher(PyzmqSocket, Publisher):
    async def send(self, message: Message) -> None:
        self._check_open()
        msg = check_message(message, self._config.limits)

        # A publisher never waits: a native publisher drops for subscribers at their high-water mark rather than
        # refusing, so a refusal here is equally a drop.
        self._try_send(msg)


class PyzmqSubscriber(PyzmqSocket, Subscriber):
    async def subscribe(self, prefix: bytes) -> None:
        self._check_open()
        self._sync.setsockopt(zmq.SUBSCRIBE, check_subscription(prefix, self._config.limits))

    async def unsubscribe(self, prefix: bytes) -> None:
        self._check_open()
        self._sync.setsockopt(zmq.UNSUBSCRIBE, check_subscription(prefix, self._config.limits))

    async def recv(self, *, timeout: float | None = None) -> Message:
        # One deadline for the whole receive, however many over-limit messages are discarded meanwhile.
        deadline = self._deadline(timeout, self._config.recv_timeout)
        while True:
            if (msg := self._check_received(await self._recv_frames(deadline))) is not None:
                return msg


class PyzmqDealer(PyzmqSocket, Dealer):
    async def send(self, message: Message, *, timeout: float | None = None) -> None:
        self._check_open()
        await self._send_waiting(check_message(message, self._config.limits), timeout)

    async def recv(self, *, timeout: float | None = None) -> Message:
        # One deadline for the whole receive, however many over-limit messages are discarded meanwhile.
        deadline = self._deadline(timeout, self._config.recv_timeout)
        while True:
            if (msg := self._check_received(await self._recv_frames(deadline))) is not None:
                return msg


class PyzmqRouter(PyzmqSocket, Router):
    async def send(self, route: bytes, message: Message) -> None:
        self._check_open()
        frames = (check_route(route), *check_message(message, self._config.limits))
        if not self._try_send(frames):
            raise WouldBlockError

    async def recv(self, *, timeout: float | None = None) -> RoutedMessage:
        deadline = self._deadline(timeout, self._config.recv_timeout)
        while True:
            frames = await self._recv_frames(deadline)
            check.state(len(frames) >= 2)
            if (msg := self._check_received(frames[1:])) is not None:
                return RoutedMessage(frames[0], msg)
