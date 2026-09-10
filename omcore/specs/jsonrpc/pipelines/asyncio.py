"""
The asyncio connection: a session handler taped to a PollAsyncioStreamDriver.

One pump task owns the driver, looping on `next()` and handing every event to the base demultiplexer. Callers of
`request` await a future the pump resolves; inbound requests each get a task running the dispatcher. The session
enforces every timeout, so nothing here needs its own, other than the optional bound on `close`.
"""
import asyncio
import errno
import socket
import sys
import typing as ta

from .... import check
from .... import lang
from ....asyncs.asyncio.streams import asyncio_open_stream_reader
from ....asyncs.asyncio.streams import asyncio_open_stream_writer
from ....asyncs.asyncio.timeouts import asyncio_maybe_timeout
from ....io.pipelines import all as ipl
from ....logs import all as logs
from ..dispatch import AsyncJsonrpcDispatcher
from ..errors import JsonrpcConnectionClosedError
from ..errors import JsonrpcMethodError
from ..errors import JsonrpcTimeoutError
from ..errors import KnownErrors
from ..ids import JsonrpcIdCreatorLike
from ..types import Batch
from ..types import Id
from ..types import NotSpecified
from ..types import Params
from ..types import Request
from ..types import Response
from .base import BaseAsyncJsonrpcConnection
from .base import JsonrpcResponseWaiter
from .configs import JsonrpcPipelineConfig
from .messages import JsonrpcPipelineMessages as Jpm
from .specs import build_jsonrpc_pipeline_spec


log = logs.get_module_logger(globals())


AsyncJsonrpcNotificationHandler: ta.TypeAlias = ta.Callable[
    ['AsyncioJsonrpcConnection', Request],
    ta.Awaitable[None],
]


##


class _AsyncioWaiter(JsonrpcResponseWaiter):
    def __init__(self, fut: asyncio.Future) -> None:
        super().__init__()

        self._fut = fut

    def set_response(self, response: Response) -> None:
        if not self._fut.done():
            self._fut.set_result(response)

    def set_exception(self, exc: BaseException) -> None:
        if not self._fut.done():
            self._fut.set_exception(exc)


##


class AsyncioJsonrpcConnection(BaseAsyncJsonrpcConnection):
    """
    Must be started (via `start` or `async with`) before use, and pumps only while its task runs: a connection which
    is never started never reads its transport.
    """

    def __init__(
            self,
            driver: ipl.PollAsyncioStreamDriver,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            dispatcher: AsyncJsonrpcDispatcher | None = None,
            notification_handler: AsyncJsonrpcNotificationHandler | None = None,
            id_creator: JsonrpcIdCreatorLike | None = None,
            include_error_details: bool = False,
            send_timeout_s: float | None = None,
    ) -> None:
        """
        `send_timeout_s` bounds how long a send waits for its bytes to reach the transport when the peer is not keeping
        up; None waits indefinitely, in which case the session's write timeout still bounds a stalled transport.
        """

        super().__init__(
            config,
            id_creator=id_creator,
            include_error_details=include_error_details,
        )

        self._driver = driver
        self._dispatcher = dispatcher
        self._notification_handler = notification_handler
        self._send_timeout_s = send_timeout_s

        self._pump_task: asyncio.Task | None = None
        self._handler_tasks: dict[Id, asyncio.Task] = {}
        self._notification_tasks: set[asyncio.Task] = set()
        self._send_futs: dict[int, asyncio.Future] = {}

        self._closed_event = asyncio.Event()

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._driver!r}>'

    @property
    def driver(self) -> ipl.PollAsyncioStreamDriver:
        return self._driver

    ##
    # lifecycle

    @property
    def is_started(self) -> bool:
        return self._pump_task is not None

    async def start(self) -> None:
        check.none(self._pump_task, 'already started')
        check.state(not self._closed, 'already closed')

        self._pump_task = asyncio.create_task(
            self._pump(),
            name=f'{type(self).__name__}._pump',
        )

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close(graceful=exc_type is None)

    async def wait_closed(self) -> None:
        """Wait until the connection has closed for any reason and its pump has finished."""

        await self._closed_event.wait()
        if (t := self._pump_task) is not None and t is not asyncio.current_task():
            await asyncio.gather(t, return_exceptions=True)

    def _default_close_timeout_s(self, graceful: bool) -> float | None:
        # The session bounds draining and the write timeout handler bounds flushing, but the driver's final transport
        # flush happens outside the pipeline's reach, so closing needs its own bound: a peer which stops reading
        # would otherwise hang a close forever.
        c = self._config
        parts = [t for t in ((c.close_drain_timeout_s if graceful else None), c.write_timeout_s) if t is not None]
        return sum(parts) if parts else None

    async def close(
            self,
            *,
            graceful: bool = True,
            timeout_s: float | None | type[NotSpecified] = NotSpecified,
    ) -> None:
        """
        Close the connection, gracefully by default (see Close), waiting for closure to complete.

        The wait is bounded: by `timeout_s` if given, else by the sum of the configured drain and write timeouts (or
        not at all if both are None). On expiry the transport is aborted. Never raises for a connection which failed
        earlier - the failure is available as `close_exception`.
        """

        if timeout_s is NotSpecified:
            timeout_s = self._default_close_timeout_s(graceful)

        if self._pump_task is None:
            # Never started: nothing is pumping, so just tear the driver down.
            self._mark_closed(None)
            await self._driver.close()
            self._closed_event.set()
            return

        if not self._closed:
            if not self._enqueue(Jpm.Close(graceful=graceful)):
                self._mark_closed(None)

        try:
            await asyncio_maybe_timeout(self.wait_closed(), ta.cast('float | None', timeout_s))
        except TimeoutError:
            log.warning('Close did not complete within %r seconds, aborting transport', timeout_s)
            await self._driver.close()
            await self.wait_closed()

    ##
    # pumping

    def _enqueue(self, *cmds: Jpm.Command) -> bool:
        """Hand commands to the driver, returning False if it is no longer accepting them."""

        if self._closed:
            return False
        try:
            self._driver.enqueue(*cmds)
        except Exception:  # noqa
            log.debug('Driver refused commands', exc_info=True)
            return False
        return True

    async def _send(self, cmd: Jpm.Command) -> None:
        """
        Hand a send command to the driver and wait until the session reports it Sent.

        Waiting is what makes backpressure real: Sent means the bytes crossed into the transport, so a peer which stops
        reading stalls the sender here rather than growing buffers without bound. The wait is bounded by
        `send_timeout_s`; on expiry a request is cancelled locally, while a notification may still go out later.
        """

        if self._closed:
            raise self._closed_error()

        fut: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._send_futs[id(cmd)] = fut
        try:
            if not self._enqueue(cmd):
                raise self._closed_error()

            try:
                await asyncio_maybe_timeout(fut, self._send_timeout_s)
            except TimeoutError as e:
                raise JsonrpcTimeoutError(
                    f'send timed out after {self._send_timeout_s!r} seconds waiting for the transport',
                ) from e

        finally:
            self._send_futs.pop(id(cmd), None)

    def _on_sent(self, cmd: Jpm.Command) -> None:
        if (f := self._send_futs.pop(id(cmd), None)) is not None and not f.done():
            f.set_result(None)

    async def _pump(self) -> None:
        exc: BaseException | None = None
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
                    # A failing close surfaced directly; the driver may be stuck flushing to a stalled peer, so do not
                    # wait for the session's orderly shutdown to reach us.
                    exc = out
                    break

                self._handle_event(out)

        except asyncio.CancelledError:
            exc = JsonrpcConnectionClosedError('connection pump cancelled')
            raise

        finally:
            if exc is not None:
                if not isinstance(exc, JsonrpcConnectionClosedError):
                    log.debug('Connection pump failed: %r', exc)
                self._mark_closed(exc)
            else:
                # The session announces Closed before the driver stops; this is only a backstop.
                self._mark_closed(None)

            try:
                await self._driver.close()
            except Exception:  # noqa
                log.debug('Error closing driver', exc_info=True)

            self._closed_event.set()

    ##
    # sending

    async def send_request(
            self,
            req: Request,
            *,
            timeout_s: float | None | type[NotSpecified] = NotSpecified,
    ) -> Response:
        """Send a prepared request (with id) and await its raw response."""

        check.arg(not req.is_notification, 'request must have an id')

        if self._closed:
            raise self._closed_error()

        fut: asyncio.Future[Response] = asyncio.get_running_loop().create_future()
        self._add_waiter(req, _AsyncioWaiter(fut))

        try:
            await self._send(Jpm.SendRequest(req, timeout_s=timeout_s))

            return await fut

        except asyncio.CancelledError:
            if self._pop_waiter(req.id_value()) is not None:
                self._enqueue(Jpm.CancelRequest(req.id_value()))
            raise

        finally:
            self._pop_waiter(req.id_value())
            self._observe(fut)

    @staticmethod
    def _observe(fut: asyncio.Future) -> None:
        # A waiter which was failed after its caller already gave up would otherwise log 'exception never retrieved'.
        if fut.done() and not fut.cancelled():
            fut.exception()

    async def request(
            self,
            method: str,
            params: Params | None = None,
            *,
            timeout_s: float | None | type[NotSpecified] = NotSpecified,
    ) -> ta.Any:
        return self._result_of(await self.send_request(self._new_request(method, params), timeout_s=timeout_s))

    async def notify(self, method: str, params: Params | None = None) -> None:
        await self._send(Jpm.SendNotification(self._new_notification(method, params)))

    async def send_batch(
            self,
            reqs: ta.Sequence[Request],
            *,
            timeout_s: float | None | type[NotSpecified] = NotSpecified,
    ) -> list[Response | None]:
        """
        Send prepared requests and notifications as one batch, returning responses in order (None for notifications).

        Raises for the first request which fails; the others are cancelled.
        """

        if self._closed:
            raise self._closed_error()

        futs: list[asyncio.Future[Response] | None] = []
        loop = asyncio.get_running_loop()
        for req in reqs:
            if req.is_notification:
                futs.append(None)
                continue
            fut: asyncio.Future[Response] = loop.create_future()
            self._add_waiter(req, _AsyncioWaiter(fut))
            futs.append(fut)

        try:
            await self._send(Jpm.SendBatch(Batch(reqs), timeout_s=timeout_s))

            return [await f if f is not None else None for f in futs]

        finally:
            for req, f in zip(reqs, futs):
                if f is None:
                    continue
                if self._pop_waiter(req.id_value()) is not None:
                    self._enqueue(Jpm.CancelRequest(req.id_value()))
                self._observe(f)

    ##
    # receiving

    def _on_request_received(self, req: Request) -> None:
        rid = req.id_value()
        task = asyncio.create_task(
            self._handle_request(req),
            name=f'{type(self).__name__}._handle_request({req.method})',
        )
        self._handler_tasks[rid] = task

        def on_done(t: asyncio.Task) -> None:
            if self._handler_tasks.get(rid) is t:
                del self._handler_tasks[rid]

        task.add_done_callback(on_done)

    async def _handle_request(self, req: Request) -> None:
        response: Response
        try:
            if (d := self._dispatcher) is None:
                raise JsonrpcMethodError(KnownErrors.METHOD_NOT_FOUND, data=req.method)

            result = await d.dispatch(self, req)
            response = Response(req.id_value(), result=result)

        except asyncio.CancelledError:
            raise

        except JsonrpcMethodError as e:
            response = Response(req.id_value(), error=e.error)

        except Exception as e:  # noqa
            log.exception('Unhandled error handling request %r', req.method)
            response = self._error_response(req, e)

        self._enqueue(Jpm.SendResponse(response))

    def _on_request_handling_aborted(self, req: Request, exc: BaseException) -> None:
        if (t := self._handler_tasks.pop(req.id_value(), None)) is not None and not t.done():
            t.cancel()

    def _on_notification_received(self, note: Request) -> None:
        if (h := self._notification_handler) is None:
            log.debug('Dropping notification with no handler: %r', note.method)
            return

        task = asyncio.create_task(
            self._handle_notification(h, note),
            name=f'{type(self).__name__}._handle_notification({note.method})',
        )
        self._notification_tasks.add(task)
        task.add_done_callback(self._notification_tasks.discard)

    async def _handle_notification(self, h: AsyncJsonrpcNotificationHandler, note: Request) -> None:
        try:
            await h(self, note)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa
            log.exception('Unhandled error handling notification %r', note.method)

    def _on_closed(self, exc: BaseException | None) -> None:
        closed_exc = self._closed_error()
        for f in list(self._send_futs.values()):
            if not f.done():
                f.set_exception(closed_exc)
        self._send_futs.clear()

        for t in list(self._handler_tasks.values()):
            if not t.done():
                t.cancel()
        self._handler_tasks.clear()

        for t in list(self._notification_tasks):
            if not t.done():
                t.cancel()


##
# construction helpers


def _try_set_nodelay(sock: socket.socket) -> None:
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError as e:
        if e.errno != errno.ENOPROTOOPT:
            raise


class AsyncioJsonrpcConnections(lang.Namespace):
    """Factories taping the connection onto the transports in use: sockets, a subprocess's stdio, or our own."""

    @staticmethod
    def of_streams(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            driver_config: ipl.PollAsyncioStreamDriver.Config | None = None,
            ssl_kwargs: ta.Mapping[str, ta.Any] | None = None,
            spec_kwargs: ta.Mapping[str, ta.Any] | None = None,
            **kwargs: ta.Any,
    ) -> AsyncioJsonrpcConnection:
        spec = build_jsonrpc_pipeline_spec(
            config,
            ssl_kwargs=ssl_kwargs,
            **(spec_kwargs or {}),
        )
        driver = ipl.PollAsyncioStreamDriver(spec, reader, writer, driver_config)
        return AsyncioJsonrpcConnection(driver, config, **kwargs)

    @classmethod
    async def connect_tcp(
            cls,
            host: str,
            port: int,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            connect_timeout_s: float | None = 10.,
            ssl: bool | ta.Mapping[str, ta.Any] = False,
            **kwargs: ta.Any,
    ) -> AsyncioJsonrpcConnection:
        reader, writer = await asyncio_maybe_timeout(
            asyncio.open_connection(host, port),
            connect_timeout_s,
        )

        try:
            if (sock := writer.get_extra_info('socket')) is not None:
                _try_set_nodelay(sock)

            ssl_kwargs: ta.Mapping[str, ta.Any] | None
            if ssl is True:
                ssl_kwargs = dict(server_side=False, server_hostname=host)
            elif ssl is False:
                ssl_kwargs = None
            else:
                ssl_kwargs = ssl

            return cls.of_streams(reader, writer, config, ssl_kwargs=ssl_kwargs, **kwargs)

        except BaseException:
            writer.close()
            raise

    @classmethod
    async def connect_unix(
            cls,
            path: str,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            connect_timeout_s: float | None = 10.,
            **kwargs: ta.Any,
    ) -> AsyncioJsonrpcConnection:
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
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            **kwargs: ta.Any,
    ) -> AsyncioJsonrpcConnection:
        """Talk to a child process over its stdio. The process must have been created with piped stdin and stdout."""

        return cls.of_streams(
            check.not_none(proc.stdout),
            check.not_none(proc.stdin),
            config,
            **kwargs,
        )

    @classmethod
    async def of_stdio(
            cls,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            stdin: ta.IO | None = None,
            stdout: ta.IO | None = None,
            **kwargs: ta.Any,
    ) -> AsyncioJsonrpcConnection:
        """Serve or talk over this process's own stdio, as a stdio MCP or ACP server does."""

        reader = await asyncio_open_stream_reader(stdin if stdin is not None else sys.stdin.buffer)
        writer = await asyncio_open_stream_writer(stdout if stdout is not None else sys.stdout.buffer)

        return cls.of_streams(reader, writer, config, **kwargs)
