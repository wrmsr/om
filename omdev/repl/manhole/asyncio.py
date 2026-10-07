"""
The asyncio hostings - the one asyncio import under manhole/. Connections over asyncio streams; a server over
`start_unix_server` / `start_server`, usable on the host's own loop; and the dedicated thread owning a loop of its own
which `start_manhole` puts a manhole on. That last is the default: a manhole which stays answerable whatever the host's
loop is doing, which matters most when what the host's loop is doing is the thing you came to look at.
"""
import asyncio
import contextlib
import os
import stat
import threading
import typing as ta

from omcore import check
from omcore.logs import all as logs

from ..dispatch import Dispatcher
from .base import Address
from .base import Connection
from .base import ConnectionHandler
from .base import ManholeServer
from .base import TcpAddress
from .base import UnixAddress
from .base import parse_address
from .protocol import decode_line
from .server import InterpreterFactory
from .server import Manhole


T = ta.TypeVar('T')


log = logs.get_module_logger(globals())


##


class AsyncioConnection(Connection):
    """
    Over an asyncio stream pair. Posted output is handed to the loop with `call_soon_threadsafe`, from any thread, and
    written in order; `drain` lets the loop turn so what was posted lands, then waits on the transport.
    """

    def __init__(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ) -> None:
        super().__init__()

        self._reader = reader
        self._writer = writer
        self._loop = asyncio.get_running_loop()
        self._closed = False

        peer = writer.get_extra_info('peername')
        self._peer = f'{peer[0]}:{peer[1]}' if isinstance(peer, tuple) and len(peer) >= 2 else 'unix'

    @property
    def peer(self) -> str:
        return self._peer

    async def read_line(self) -> str | None:
        try:
            data = await self._reader.readline()
        except (ConnectionError, OSError):
            return None
        if not data:
            return None
        return decode_line(data)

    def _write_now(self, data: bytes) -> None:
        if self._closed or self._writer.is_closing():
            return
        try:
            self._writer.write(data)
        except (ConnectionError, OSError):
            pass

    def post(self, text: str) -> None:
        self._loop.call_soon_threadsafe(self._write_now, text.encode('utf-8', 'replace'))

    async def drain(self) -> None:
        await asyncio.sleep(0)  # posted writes, queued ahead of this, land
        if self._closed or self._writer.is_closing():
            return
        try:
            await self._writer.drain()
        except (ConnectionError, OSError):
            pass

    async def aclose(self) -> None:
        if self._closed:
            return
        await self.drain()
        self._closed = True
        self._writer.close()
        try:
            await self._writer.wait_closed()
        except (ConnectionError, OSError):
            pass


##


class AsyncioManholeServer(ManholeServer):
    """Serves on the loop it is started on - the host's own, when that is wanted."""

    def __init__(
            self,
            address: Address,
            handler: ConnectionHandler,
    ) -> None:
        super().__init__()

        self._address = address
        self._handler = handler

        self._server: asyncio.Server | None = None
        self._bound: Address | None = None
        self._tasks: set[asyncio.Task] = set()

    @property
    def address(self) -> Address | None:
        return self._bound

    @property
    def num_connections(self) -> int:
        return len(self._tasks)

    def _on_connected(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        connection = AsyncioConnection(reader, writer)
        task = asyncio.get_running_loop().create_task(self._serve(connection))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _serve(self, connection: AsyncioConnection) -> None:
        try:
            await self._handler(connection)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            log.exception('Manhole connection from %s failed', connection.peer)
        finally:
            await connection.aclose()

    async def start(self) -> None:
        check.state(self._server is None, 'Already started')
        address = self._address

        if isinstance(address, UnixAddress):
            if (
                    address.unlink_existing and
                    os.path.exists(address.path) and
                    stat.S_ISSOCK(os.stat(address.path).st_mode)
            ):
                os.unlink(address.path)
            # The socket file's mode is set at bind through the umask, so there is no window at wider permissions.
            previous_umask = os.umask(0o777 & ~address.mode)
            try:
                server = await asyncio.start_unix_server(self._on_connected, path=address.path)
            finally:
                os.umask(previous_umask)
            self._bound = address

        elif isinstance(address, TcpAddress):
            server = await asyncio.start_server(self._on_connected, host=address.host, port=address.port)
            host, port = check.not_none(server.sockets)[0].getsockname()[:2]
            self._bound = TcpAddress(host=host, port=port)

        else:
            raise TypeError(address)

        self._server = server
        log.info('Manhole listening on %s', self._bound)

    async def stop(self) -> None:
        if (server := self._server) is None:
            return
        self._server = None

        server.close()

        # Connections are closed by their handlers' unwinding; only then does `wait_closed` return.
        tasks = list(self._tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        with contextlib.suppress(OSError):
            await server.wait_closed()

        if isinstance(self._address, UnixAddress):
            with contextlib.suppress(OSError):
                os.unlink(self._address.path)

        self._bound = None
        log.info('Manhole stopped')


##


class AsyncioLoopThread:
    """A thread owning an asyncio loop: `run` a coroutine on it and wait for the result from any other thread."""

    def __init__(
            self,
            *,
            name: str = 'om-manhole',
            daemon: bool = True,
    ) -> None:
        super().__init__()

        self._thread = threading.Thread(target=self._main, name=name, daemon=daemon)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ready = threading.Event()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return check.not_none(self._loop)

    @property
    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def _main(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        self._ready.set()
        try:
            loop.run_forever()
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
            finally:
                asyncio.set_event_loop(None)
                loop.close()

    def start(self) -> None:
        check.state(not self._ready.is_set(), 'Already started')
        self._thread.start()
        self._ready.wait()

    def run(self, fn: ta.Callable[[], ta.Awaitable[T]], *, timeout: float | None = None) -> T:
        """Run `fn` on the loop and wait for its result here."""

        async def inner() -> T:
            return await fn()

        return asyncio.run_coroutine_threadsafe(inner(), self.loop).result(timeout)

    def stop(self, *, timeout: float | None = None) -> None:
        if (loop := self._loop) is not None and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)
        if self._thread.is_alive():
            self._thread.join(timeout)


class AsyncioThreadManhole:
    """
    The default hosting: the manhole on a dedicated thread with a loop of its own. `start` returns once listening,
    `stop` once everything is closed and the thread has ended; or use it as a context manager.
    """

    def __init__(
            self,
            manhole: Manhole,
            address: Address,
            *,
            thread_name: str = 'om-manhole',
            stop_timeout_s: float | None = 10.,
    ) -> None:
        super().__init__()

        self._manhole = manhole
        self._address = address
        self._stop_timeout_s = stop_timeout_s

        self._thread = AsyncioLoopThread(name=thread_name)
        self._server: AsyncioManholeServer | None = None

    @property
    def manhole(self) -> Manhole:
        return self._manhole

    @property
    def thread(self) -> AsyncioLoopThread:
        return self._thread

    @property
    def address(self) -> Address | None:
        return self._server.address if self._server is not None else None

    @property
    def is_running(self) -> bool:
        return self._server is not None

    def start(self) -> ta.Self:
        check.state(self._server is None, 'Already started')
        self._thread.start()
        server = AsyncioManholeServer(self._address, self._manhole.handle)
        try:
            self._thread.run(server.start)
        except BaseException:
            self._thread.stop(timeout=self._stop_timeout_s)
            raise
        self._server = server
        return self

    def stop(self) -> None:
        if (server := self._server) is not None:
            self._server = None
            try:
                self._thread.run(server.stop, timeout=self._stop_timeout_s)
            finally:
                self._thread.stop(timeout=self._stop_timeout_s)

    def __enter__(self) -> ta.Self:
        if self._server is None:
            self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()


def start_manhole(
        address: Address | str,
        *,
        seed: ta.Mapping[str, ta.Any] | None = None,
        interpreter_factory: InterpreterFactory | None = None,
        banner: str | None = None,
        dispatcher: Dispatcher | None = None,
        thread_name: str = 'om-manhole',
) -> AsyncioThreadManhole:
    """
    The one-call default: a manhole on its own thread and loop, listening at `address` by the time this returns. Stop
    it with `stop()`, or use the result as a context manager. `seed` is what the host puts in reach of every
    connection; `dispatcher` runs the code elsewhere - an `AsyncioLoopDispatcher` over the host's loop lets the repl
    await the host's coroutines.
    """

    manhole = Manhole(
        seed=seed,
        interpreter_factory=interpreter_factory,
        banner=banner,
        dispatcher=dispatcher,
    )
    return AsyncioThreadManhole(
        manhole,
        parse_address(address) if isinstance(address, str) else address,
        thread_name=thread_name,
    ).start()
