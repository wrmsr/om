# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The asyncio runtime: one pump task steps the driver and delivers events; every handler runs as a tracked task.

Promises are asynclite event promises over asyncio events, so waiting suspends the waiting task. Request handlers are
keyed by request id, so a peer's cancel, a handling timeout, or the connection closing cancels exactly the right task.
Every task the runtime creates is tracked from creation to completion: `close` cancels them, `wait_closed` waits for
them (save the task calling it), and their exceptions are observed.

Cancellation, the asyncio reality:
 - A caller cancelled while awaiting a response abandons the request: its waiter is dropped and, if so configured, the
   peer is sent a cancel.
 - A peer's cancel, or the session giving up on an inbound request, cancels that request's handler task.
 - A handler task cancelled from anywhere else answers the peer with a `cancelled` error, if the request is still in
   flight, and then lets the cancellation propagate.
 - The pump task being cancelled fails the connection: every waiter fails, every handler is cancelled, the driver is
   aborted.
Handlers should let CancelledError propagate. One which swallows it delays `wait_closed` for as long as it keeps
running.
"""
import asyncio
import errno
import functools
import socket
import sys
import typing as ta

from ..asyncs.asyncio.streams import asyncio_open_stream_reader
from ..asyncs.asyncio.streams import asyncio_open_stream_writer
from ..asyncs.asyncio.timeouts import asyncio_maybe_timeout
from ..asyncs.asynclite.asyncio.events import AsyncioAsyncliteEvent
from ..asyncs.asynclite.eventpromises import EventAsynclitePromise
from ..asyncs.asynclite.promises import AsynclitePromise
from ..io.pipelines.drivers.asyncio.streams import PollAsyncioStreamIoPipelineDriver
from ..lite.check import check
from ..logs.modules import get_module_logger
from .configs import RpcConfig
from .connection import RpcConnection
from .dispatch import RpcHandler
from .errors import RpcConnectionClosedError
from .runtime import RpcRuntime
from .runtime import RpcRuntimeSink
from .specs import rpc_build_pipeline_spec


log = get_module_logger(globals())  # noqa


##


class AsyncioRpcRuntime(RpcRuntime):
    """Must be started on the loop which will run it; the driver's streams must belong to that loop too."""

    def __init__(
            self,
            driver: PollAsyncioStreamIoPipelineDriver,
            *,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
    ) -> None:
        super().__init__()

        self._driver = driver
        self._closers = list(closers)

        self._sink: ta.Optional[RpcRuntimeSink] = None
        self._pump_task: ta.Optional[asyncio.Task] = None
        self._closed_event: ta.Optional[asyncio.Event] = None
        self._driver_done = False
        self._closed = False

        self._keyed_tasks: ta.Dict[ta.Any, asyncio.Task] = {}
        self._unkeyed_tasks: ta.Set[asyncio.Task] = set()

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._driver!r}>'

    @property
    def driver(self) -> PollAsyncioStreamIoPipelineDriver:
        return self._driver

    @property
    def is_started(self) -> bool:
        return self._sink is not None

    @property
    def is_driver_done(self) -> bool:
        return self._driver_done

    @property
    def num_tasks(self) -> int:
        """Handler tasks currently tracked, excluding the pump."""

        return len(self._keyed_tasks) + len(self._unkeyed_tasks)

    #

    def make_promise(self) -> AsynclitePromise:
        return EventAsynclitePromise(AsyncioAsyncliteEvent(asyncio.Event()))

    def is_cancelled_exception(self, exc: BaseException) -> bool:
        return isinstance(exc, asyncio.CancelledError)

    def enqueue(self, *commands: ta.Any) -> bool:
        if self._driver_done or self._closed:
            return False
        try:
            self._driver.enqueue(*commands)
        except Exception:  # noqa
            log.debug('Driver refused commands', exc_info=True)
            return False
        return True

    #

    async def start(self, sink: RpcRuntimeSink) -> None:
        check.none(self._sink, 'already started')
        check.state(not self._closed, 'already closed')

        self._sink = sink
        self._closed_event = asyncio.Event()
        self._pump_task = asyncio.create_task(self._pump(sink), name=f'{type(self).__name__}._pump')

    async def _pump(self, sink: RpcRuntimeSink) -> None:
        exc: ta.Optional[BaseException] = None
        try:
            while True:
                try:
                    out = await self._driver.next()
                except asyncio.CancelledError:
                    raise
                except Exception as e:  # noqa
                    exc = e
                    break

                if out is None:
                    if not self._driver.is_running:
                        break
                    continue

                if isinstance(out, BaseException):
                    # A failing close the session surfaced: the driver may be stuck flushing to a stalled peer, so do
                    # not wait for its orderly shutdown.
                    exc = out
                    break

                await sink.on_event(out)

        except asyncio.CancelledError:
            if exc is None:
                exc = RpcConnectionClosedError('rpc pump cancelled')
            raise

        except Exception as e:  # noqa
            log.exception('Rpc pump failed delivering an event')
            exc = e

        finally:
            self._driver_done = True
            try:
                sink.on_driver_done(exc)
            except Exception:  # noqa
                log.exception('Error reporting rpc driver done')

            try:
                await self._driver.close()
            except Exception:  # noqa
                log.debug('Error closing rpc driver', exc_info=True)

            self._run_closers()

            check.not_none(self._closed_event).set()

    #

    @staticmethod
    def _observe(task: asyncio.Task) -> None:
        if not task.cancelled() and (e := task.exception()) is not None:
            log.error('Rpc handler task failed', exc_info=e)

    def _on_keyed_done(self, key: ta.Any, task: asyncio.Task) -> None:
        if self._keyed_tasks.get(key) is task:
            del self._keyed_tasks[key]
        self._observe(task)

    def _on_unkeyed_done(self, task: asyncio.Task) -> None:
        self._unkeyed_tasks.discard(task)
        self._observe(task)

    @staticmethod
    async def _run_spawned(fn: ta.Callable[[], ta.Awaitable[None]]) -> None:
        try:
            await fn()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa
            log.exception('Unhandled error in rpc handler')

    async def spawn(self, key: ta.Any, fn: ta.Callable[[], ta.Awaitable[None]]) -> None:
        if self._closed or self._driver_done:
            return

        task = asyncio.create_task(self._run_spawned(fn))

        if key is not None:
            if (prev := self._keyed_tasks.get(key)) is not None and not prev.done():
                # The session never lets an id be in flight twice, so this is a bug; keep tracking the old task anyway.
                log.warning('Rpc handler key %r spawned while still running', key)
                self._unkeyed_tasks.add(prev)
                prev.add_done_callback(self._unkeyed_tasks.discard)
            self._keyed_tasks[key] = task
            task.add_done_callback(functools.partial(self._on_keyed_done, key))

        else:
            self._unkeyed_tasks.add(task)
            task.add_done_callback(self._on_unkeyed_done)

    def cancel(self, key: ta.Any) -> None:
        if (task := self._keyed_tasks.get(key)) is not None and not task.done():
            task.cancel()

    def _all_tasks_but_current(self) -> ta.List[asyncio.Task]:
        try:
            cur = asyncio.current_task()
        except RuntimeError:
            cur = None
        return [t for t in (*self._keyed_tasks.values(), *self._unkeyed_tasks) if t is not cur]

    def cancel_all(self) -> None:
        for task in self._all_tasks_but_current():
            if not task.done():
                task.cancel()

    #

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        self.cancel_all()

        try:
            await self._driver.close()

        except Exception:  # noqa
            log.debug('Error closing rpc driver', exc_info=True)

        finally:
            if self._pump_task is None:
                # Never started: no pump will run them.
                self._run_closers()

    def _run_closers(self) -> None:
        """Run once the driver is done, however that came about. Idempotent: the closers run once."""

        closers, self._closers = self._closers, []
        for c in closers:
            try:
                c()
            except Exception:  # noqa
                log.exception('Error in rpc runtime closer %r', c)

    async def wait_closed(self) -> None:
        if (ev := self._closed_event) is not None:
            await ev.wait()

        try:
            cur = asyncio.current_task()
        except RuntimeError:
            cur = None

        while True:
            tasks = [
                t
                for t in (self._pump_task, *self._keyed_tasks.values(), *self._unkeyed_tasks)
                if t is not None and t is not cur and not t.done()
            ]
            if tasks:
                # asyncio.wait, unlike gather, does not cancel what it waits for when the waiter itself is cancelled.
                await asyncio.wait(tasks)
                continue

            if any(t is not cur for t in (*self._keyed_tasks.values(), *self._unkeyed_tasks)):
                # Finished, but with their done callbacks - which observe and untrack them - not yet run: they run on
                # the next loop iteration, so yield one.
                await asyncio.sleep(0)
                continue

            return


##


class AsyncioSerializingRpcHandler(RpcHandler):
    """
    Runs the wrapped handler's requests and spawned notifications one at a time, in arrival order, for a backend which
    is not safe to call concurrently. Inline notifications are untouched: they already run one at a time on the pump.
    """

    def __init__(self, handler: RpcHandler) -> None:
        super().__init__()

        self._handler = handler
        self._lock: ta.Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        if (lock := self._lock) is None:
            lock = self._lock = asyncio.Lock()
        return lock

    async def handle_request(self, method: str, params: ta.Any) -> ta.Any:
        async with self._get_lock():
            return await self._handler.handle_request(method, params)

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        return self._handler.handle_notification_inline(method, params)

    async def handle_notification(self, method: str, params: ta.Any) -> None:
        async with self._get_lock():
            await self._handler.handle_notification(method, params)


##


def _rpc_asyncios_try_set_nodelay(sock: socket.socket) -> None:
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError as e:
        if e.errno != errno.ENOPROTOOPT:
            raise


class AsyncioRpcConnections:
    """
    Factories taping an asyncio connection onto the transports in use: sockets, a subprocess's stdio, or our own.
    Connection keyword arguments (`handler`, `id_creator`, ...) pass through. The connections are not started.
    """

    def __new__(cls, *args, **kwargs):  # noqa
        raise TypeError

    @staticmethod
    def of_streams(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            driver_config: ta.Optional[PollAsyncioStreamIoPipelineDriver.Config] = None,
            spec_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
            **kwargs: ta.Any,
    ) -> RpcConnection:
        """TLS is a transport handler: `spec_kwargs=dict(transport_handlers=[SslIoPipelineHandler(...)])`."""

        spec = rpc_build_pipeline_spec(
            config,
            **(spec_kwargs or {}),
        )
        driver = PollAsyncioStreamIoPipelineDriver(spec, reader, writer, driver_config)
        return RpcConnection(AsyncioRpcRuntime(driver, closers=closers), config, **kwargs)

    @classmethod
    async def connect_tcp(
            cls,
            host: str,
            port: int,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            connect_timeout_s: ta.Optional[float] = 10.,
            **kwargs: ta.Any,
    ) -> RpcConnection:
        reader, writer = await asyncio_maybe_timeout(
            asyncio.open_connection(host, port),
            connect_timeout_s,
        )

        try:
            if (sock := writer.get_extra_info('socket')) is not None:
                _rpc_asyncios_try_set_nodelay(sock)

            return cls.of_streams(reader, writer, config, **kwargs)

        except BaseException:
            writer.close()
            raise

    @classmethod
    async def connect_unix(
            cls,
            path: str,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            connect_timeout_s: ta.Optional[float] = 10.,
            **kwargs: ta.Any,
    ) -> RpcConnection:
        reader, writer = await asyncio_maybe_timeout(
            asyncio.open_unix_connection(path),
            connect_timeout_s,
        )

        try:
            return cls.of_streams(reader, writer, config, **kwargs)
        except BaseException:
            writer.close()
            raise

    @classmethod
    def of_subprocess(
            cls,
            proc: asyncio.subprocess.Process,
            config: RpcConfig = RpcConfig.DEFAULT,
            **kwargs: ta.Any,
    ) -> RpcConnection:
        """Talks to a child process over its stdio. The process must have been created with piped stdin and stdout."""

        return cls.of_streams(
            check.not_none(proc.stdout),
            check.not_none(proc.stdin),
            config,
            **kwargs,
        )

    @classmethod
    async def of_stdio(
            cls,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            stdin: ta.Optional[ta.IO] = None,
            stdout: ta.Optional[ta.IO] = None,
            **kwargs: ta.Any,
    ) -> RpcConnection:
        """Serves or talks over this process's own stdio, as a remotely bootstrapped process does."""

        reader = await asyncio_open_stream_reader(stdin if stdin is not None else sys.stdin.buffer)
        writer = await asyncio_open_stream_writer(stdout if stdout is not None else sys.stdout.buffer)

        return cls.of_streams(reader, writer, config, **kwargs)
