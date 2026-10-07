"""
The loop-less hostings.

`serve_inline` is real: it blocks the calling thread on a plain socket until the one client it accepts leaves - a remote
pdb of sorts, for halting a program right where it is and poking at it from outside before it goes on. The protocol is
the same code the asyncio hostings run; its awaits never leave the thread, so `lang.sync_await` drives it. The manhole
must be built with `allow_await=False`: there is no loop here for an await to run on.

`SyncThreadManhole` is the TODO: a background thread serving several connections with `selectors` and no loop at all -
for hosts which want the manhole without asyncio anywhere in the process. Same protocol, a selectors-driven server in
place of `AsyncioManholeServer`; the shape is here, the body is not.
"""
import contextlib
import os
import socket
import stat
import typing as ta

from omcore import check
from omcore import lang
from omcore.logs import all as logs

from .base import Address
from .base import Connection
from .base import TcpAddress
from .base import UnixAddress
from .protocol import decode_line
from .server import Manhole


log = logs.get_module_logger(globals())


##


class SyncSocketConnection(Connection):
    """A blocking socket as a Connection: its async methods never actually await, so a sync driver completes them."""

    def __init__(self, sock: socket.socket) -> None:
        super().__init__()

        self._sock = sock
        self._file = sock.makefile('rb')
        self._closed = False

        try:
            peer = sock.getpeername()
        except OSError:
            peer = None
        self._peer = f'{peer[0]}:{peer[1]}' if isinstance(peer, tuple) and len(peer) >= 2 else 'unix'

    @property
    def peer(self) -> str:
        return self._peer

    async def read_line(self) -> str | None:
        try:
            data = self._file.readline()
        except OSError:
            return None
        if not data:
            return None
        return decode_line(data)

    def post(self, text: str) -> None:
        if self._closed:
            return
        try:
            self._sock.sendall(text.encode('utf-8', 'replace'))
        except OSError:
            pass

    async def drain(self) -> None:
        pass

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        with contextlib.suppress(OSError):
            self._file.close()
        with contextlib.suppress(OSError):
            self._sock.close()


##


def _listen(address: Address) -> tuple[socket.socket, Address]:
    if isinstance(address, UnixAddress):
        if address.unlink_existing and os.path.exists(address.path) and stat.S_ISSOCK(os.stat(address.path).st_mode):
            os.unlink(address.path)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        previous_umask = os.umask(0o777 & ~address.mode)
        try:
            sock.bind(address.path)
        finally:
            os.umask(previous_umask)
        sock.listen(1)
        return sock, address

    if isinstance(address, TcpAddress):
        sock = socket.create_server((address.host, address.port))
        host, port = sock.getsockname()[:2]
        return sock, TcpAddress(host=host, port=port)

    raise TypeError(address)


def serve_inline(
        manhole: Manhole,
        address: Address,
        *,
        on_listening: ta.Callable[[Address], None] | None = None,
) -> None:
    """
    Block the calling thread: listen at `address`, accept one client, serve it until it leaves, close up, return.
    `on_listening` is told the bound address (an ephemeral tcp port, say) before the accept.
    """

    if not manhole.has_interpreter_factory:
        check.state(not manhole.allow_await, 'A manhole served without a loop needs allow_await=False')

    sock, bound = _listen(address)
    log.info('Manhole listening inline on %s', bound)
    try:
        if on_listening is not None:
            on_listening(bound)

        conn, _ = sock.accept()
        connection = SyncSocketConnection(conn)
        try:
            lang.sync_await(manhole.handle(connection))
        finally:
            lang.sync_await(connection.aclose())

    finally:
        sock.close()
        if isinstance(address, UnixAddress):
            with contextlib.suppress(OSError):
                os.unlink(address.path)
        log.info('Manhole inline on %s done', bound)


##


class SyncThreadManhole:
    """
    TODO: the no-asyncio background hosting - a thread running a `selectors` loop over the listening socket and its
    connections, each a `SyncSocketConnection` driven line by line under `lang.sync_await`, with `start` / `stop` /
    context-manager lifecycle like `AsyncioThreadManhole`. Until then it says so.
    """

    def __init__(
            self,
            manhole: Manhole,
            address: Address,
    ) -> None:
        super().__init__()

        self._manhole = manhole
        self._address = address

    def start(self) -> ta.Self:
        raise NotImplementedError('TODO: the selectors-based sync hosting - see the module docstring')

    def stop(self) -> None:
        raise NotImplementedError('TODO: the selectors-based sync hosting - see the module docstring')
