"""
Bound listeners and reconnecting connectors. Only these touch the network or filesystem; every connection they produce
gets a fresh pipeline.

An IPC listener binds its own socket, which fails - and so removes nothing - if anything exists at the path. Closing it
unlinks the path only if it is still the entry the bind created.
"""
import abc
import asyncio
import errno
import math
import random
import socket
import typing as ta

from omcore import lang
from omcore.logs import all as logs

from ....api.addresses import Address
from ....api.addresses import IpcAddress
from ....api.addresses import TcpAddress
from ....api.errors import AddressInUseError
from ....api.errors import TransportError
from ....api.sockets import Attachment
from ....ipc.ownership import IpcEntry
from ....ipc.ownership import IpcLease
from ....ipc.ownership import IpcLeaseHeldError
from ....ipc.ownership import record_ipc_entry
from ....ipc.ownership import unlink_ipc_entry_if_owned
from .connections import Connection
from .retries import reconnect_delay


log = logs.get_module_logger(globals())


StreamCallback: ta.TypeAlias = ta.Callable[[asyncio.StreamReader, asyncio.StreamWriter], Connection | None]


##


def _translate_bind_error(e: OSError) -> Exception:
    if e.errno == errno.EADDRINUSE:
        return AddressInUseError(str(e))
    return TransportError(str(e))


class PipelinesAttachment(Attachment, lang.Abstract):
    def __init__(self, address: Address) -> None:
        super().__init__()

        self._address = address
        self._on_close: ta.Callable[[PipelinesAttachment], None] | None = None
        self._stopped = False

    def __repr__(self) -> str:
        return f'{type(self).__name__}<{self._address}>'

    @property
    def address(self) -> Address:
        return self._address

    def set_on_close(self, on_close: ta.Callable[[PipelinesAttachment], None]) -> None:
        self._on_close = on_close

    @abc.abstractmethod
    def stop(self) -> None:
        """Idempotently stop listening or reconnecting."""

        raise NotImplementedError

    async def wait_stopped(self) -> None:
        pass

    async def aclose(self) -> None:
        self.stop()
        await self.wait_stopped()
        if (cb := self._on_close) is not None:
            self._on_close = None
            cb(self)


class ListenerAttachment(PipelinesAttachment):
    """
    Accepts on its own listening socket in its own task, rather than through an asyncio server: stopping is then a hard
    stop, ending an accept in flight and closing anything accepted but not yet handed over.
    """

    def __init__(
            self,
            address: Address,
            sock: socket.socket,
            accept: StreamCallback,
            *,
            ipc_entry: IpcEntry | None = None,
            ipc_lease: IpcLease | None = None,
    ) -> None:
        super().__init__(address)

        self._sock = sock
        self._accept = accept
        self._ipc_entry = ipc_entry
        self._ipc_lease = ipc_lease

        self._task: asyncio.Task | None = None

    @classmethod
    async def _bind_tcp(cls, addr: TcpAddress) -> socket.socket:
        host = '0.0.0.0' if addr.is_wildcard_host else addr.host  # noqa: S104
        infos = await asyncio.get_running_loop().getaddrinfo(
            host,
            addr.port,
            type=socket.SOCK_STREAM,
            flags=socket.AI_PASSIVE,
        )
        if not infos:
            raise TransportError(f'cannot resolve {addr}')
        family, type_, proto, _, sockaddr = infos[0]

        sock = socket.socket(family, type_, proto)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(sockaddr)
        except OSError as e:
            sock.close()
            raise _translate_bind_error(e) from e
        return sock

    @classmethod
    def _bind_ipc(cls, addr: IpcAddress) -> socket.socket:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.bind(addr.path)
        except OSError as e:
            sock.close()
            raise _translate_bind_error(e) from e
        return sock

    @classmethod
    async def bind(cls, addr: Address, accept: StreamCallback) -> ListenerAttachment:
        if isinstance(addr, TcpAddress):
            sock = await cls._bind_tcp(addr)
            try:
                sock.listen(socket.SOMAXCONN)
                sock.setblocking(False)
            except BaseException:
                sock.close()
                raise
            host, port = sock.getsockname()[:2]
            att = cls(TcpAddress(host, port), sock, accept)

        elif isinstance(addr, IpcAddress):
            # The lease keeps a cooperating native binder - which removes an existing path before binding - from taking
            # the path while it is bound here.
            try:
                lease = IpcLease.acquire(addr.path)
            except IpcLeaseHeldError as e:
                raise AddressInUseError(f'path is leased by another binder: {addr.path}') from e
            except OSError as e:
                raise TransportError(str(e)) from e

            entry: IpcEntry | None = None
            try:
                sock = cls._bind_ipc(addr)
                try:
                    entry = record_ipc_entry(addr.path)
                    sock.listen(socket.SOMAXCONN)
                    sock.setblocking(False)
                except BaseException:
                    sock.close()
                    if entry is not None:
                        unlink_ipc_entry_if_owned(entry)
                    raise
            except BaseException:
                lease.release()
                raise
            att = cls(addr, sock, accept, ipc_entry=entry, ipc_lease=lease)

        else:
            raise TypeError(addr)

        att._task = asyncio.create_task(att._run(), name=f'zmq listener {att.address}')  # noqa
        return att

    async def _run(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            try:
                conn, _ = await loop.sock_accept(self._sock)
            except OSError as e:
                # Out of descriptors or memory is waited out rather than spun on; anything else - a connection reset
                # before it was accepted - is skipped.
                log.debug('Accept on %s failed: %r', self._address, e)
                if e.errno in (errno.EMFILE, errno.ENFILE, errno.ENOBUFS, errno.ENOMEM):
                    await asyncio.sleep(.1)
                continue

            try:
                reader, writer = await asyncio.open_connection(sock=conn)
            except BaseException:
                conn.close()
                raise

            self._accept(reader, writer)

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True

        if (task := self._task) is not None:
            task.cancel()
        self._sock.close()

        if (entry := self._ipc_entry) is not None:
            unlink_ipc_entry_if_owned(entry)
        if (lease := self._ipc_lease) is not None:
            lease.release()

    async def wait_stopped(self) -> None:
        if (task := self._task) is not None:
            await asyncio.gather(task, return_exceptions=True)


class ConnectorAttachment(PipelinesAttachment):
    """Connects, runs the connection until it ends, and reconnects with backoff - until stopped."""

    def __init__(
            self,
            address: Address,
            start_connection: StreamCallback,
            *,
            connect_timeout: float,
            reconnect_interval: float,
            reconnect_interval_max: float,
            random_sample: ta.Callable[[], float] = random.random,
    ) -> None:
        super().__init__(address)

        self._start_connection = start_connection
        self._connect_timeout = connect_timeout
        self._reconnect_interval = reconnect_interval
        self._reconnect_interval_max = reconnect_interval_max
        self._random_sample = random_sample

        self._connection: Connection | None = None
        self._task: asyncio.Task | None = None

    @property
    def stopped(self) -> bool:
        return self._stopped

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name=f'zmq connector {self._address}')

    async def _open(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        addr = self._address
        async with asyncio.timeout(self._connect_timeout):
            if isinstance(addr, TcpAddress):
                return await asyncio.open_connection(addr.host, addr.port)
            elif isinstance(addr, IpcAddress):
                return await asyncio.open_unix_connection(addr.path)
            else:
                raise TypeError(addr)

    async def _run(self) -> None:
        attempt = 0
        while not self._stopped:
            try:
                reader, writer = await self._open()
            except Exception as e:  # noqa
                # Including the unexpected - a name the resolver rejects, say: retried like any failure, never silently
                # ending the connection intent.
                log.debug('Connect to %s failed: %r', self._address, e)
            else:
                if (conn := self._start_connection(reader, writer)) is None:
                    # Refused - at the socket's connection limit, which is temporary - unless stopped meanwhile.
                    if self.stopped:
                        return
                else:
                    self._connection = conn
                    try:
                        await conn.wait_done()
                    finally:
                        self._connection = None
                    if conn.was_ready:
                        attempt = 0

            delay = reconnect_delay(
                attempt,
                base=self._reconnect_interval,
                cap=self._reconnect_interval_max,
                sample=self._random_sample(),
            )
            attempt += 1
            if math.isinf(delay):
                # Never again - but no timer either: only stopping ends the wait.
                await asyncio.get_running_loop().create_future()
            await asyncio.sleep(delay)

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True

        if (task := self._task) is not None:
            task.cancel()
        if (conn := self._connection) is not None:
            conn.abort()

    async def wait_stopped(self) -> None:
        # The live connection's disconnection is only initiated: the socket owns and awaits its connections.
        if (task := self._task) is not None:
            await asyncio.gather(task, return_exceptions=True)
