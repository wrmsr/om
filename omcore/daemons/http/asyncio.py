import asyncio
import inspect
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...http.pipelines.requests import FullIoPipelineHttpRequest
from ...http.pipelines.responses import FullIoPipelineHttpResponse
from ...io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...logs import all as logs
from .dispatch import HttpHandler
from .dispatch import HttpHealthConfig
from .pipelines import HttpPipelineFailure
from .pipelines import HttpServerRequest
from .pipelines import HttpServerSendResponse
from .pipelines import pipeline_http_server_spec
from .server import HttpServerRuntime
from .server import PipelineHttpServerDrainTimeoutError


log = logs.get_module_logger(globals())


##


class AsyncHttpHandler(ta.Protocol):
    async def __call__(self, request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        raise NotImplementedError


class ThreadedAsyncHttpHandler(lang.Final):
    """Adapt a synchronous HTTP handler without running it on the event-loop thread."""

    def __init__(self, handler: HttpHandler) -> None:
        super().__init__()

        self._handler = handler

    async def __call__(self, request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        return await asyncio.to_thread(self._handler, request)


@dc.dataclass(frozen=True, kw_only=True)
class AsyncioPipelineHttpServerConfig:
    host: str
    port: int
    handler: AsyncHttpHandler

    health: HttpHealthConfig | None = HttpHealthConfig()
    connection_timeout_s: float | None = 30.
    max_request_body_bytes: int = 64 * 1024
    backlog: int = 128

    def __post_init__(self) -> None:
        check.non_empty_str(self.host)
        check.arg(0 <= self.port <= 65_535)
        check.callable(self.handler)
        check.arg(
            inspect.iscoroutinefunction(self.handler) or
            inspect.iscoroutinefunction(self.handler.__call__),
            'Asyncio HTTP handlers must be async; wrap synchronous handlers in ThreadedAsyncHttpHandler',
        )
        check.arg(self.connection_timeout_s is None or self.connection_timeout_s > 0.)
        check.arg(self.max_request_body_bytes >= 0)
        check.arg(self.backlog > 0)


##


class AsyncioPipelineHttpServer(lang.Final):
    """An asyncio TCP host for one-request HTTP pipelines."""

    def __init__(self, config: AsyncioPipelineHttpServerConfig) -> None:
        super().__init__()

        self._config = config
        self._server: asyncio.Server | None = None
        self._runtime: HttpServerRuntime | None = None
        self._bound_address: tuple[str, int] | None = None
        self._connections: set[asyncio.Task[None]] = set()
        self._drivers: dict[asyncio.Task[None], PollAsyncioStreamIoPipelineDriver] = {}
        self._closing = False

    @property
    def config(self) -> AsyncioPipelineHttpServerConfig:
        return self._config

    @property
    def bound_address(self) -> tuple[str, int]:
        return check.not_none(self._bound_address)

    @property
    def started(self) -> bool:
        return self._server is not None

    async def start(self, runtime: HttpServerRuntime) -> tuple[str, int]:
        if self._server is not None or self._closing:
            raise RuntimeError('Asyncio HTTP server is already started or closed')
        self._runtime = runtime
        self._server = await asyncio.start_server(
            self._accept_connection,
            self._config.host,
            self._config.port,
            backlog=self._config.backlog,
        )
        sockets = check.not_none(self._server.sockets)
        raw_address = sockets[0].getsockname()
        self._bound_address = (
            check.isinstance(raw_address[0], str),
            check.isinstance(raw_address[1], int),
        )
        return self._bound_address

    def _accept_connection(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ) -> None:
        task = asyncio.create_task(self._run_connection(reader, writer))
        self._connections.add(task)
        task.add_done_callback(self._connections.discard)

    async def _driver_next(self, driver: PollAsyncioStreamIoPipelineDriver) -> ta.Any:
        return await asyncio.wait_for(
            driver.next(),
            self._config.connection_timeout_s,
        )

    async def _send_response(
            self,
            driver: PollAsyncioStreamIoPipelineDriver,
            response: FullIoPipelineHttpResponse,
    ) -> None:
        driver.enqueue(HttpServerSendResponse(response=response))
        while driver.is_running:
            event = await self._driver_next(driver)
            if isinstance(event, HttpPipelineFailure):
                raise event.exc
            if event is not None:
                raise RuntimeError(f'Unexpected HTTP server event: {event!r}')

    async def _dispatch_application(
            self,
            request: FullIoPipelineHttpRequest,
    ) -> FullIoPipelineHttpResponse:
        try:
            return check.isinstance(
                await self._config.handler(request),
                FullIoPipelineHttpResponse,
            )
        except asyncio.CancelledError:
            raise
        except BaseException as exc:  # noqa
            log.exception(exc)  # noqa: TRY401
            return FullIoPipelineHttpResponse.simple(
                status=500,
                body=b'internal server error',
            )

    async def _handle_connection(self, driver: PollAsyncioStreamIoPipelineDriver) -> None:
        while True:
            event = await self._driver_next(driver)
            if isinstance(event, HttpPipelineFailure):
                raise event.exc
            if isinstance(event, HttpServerRequest):
                request = event.request
                break
            if event is not None:
                raise RuntimeError(f'Unexpected HTTP server event: {event!r}')
            if not driver.is_running:
                return

        runtime = check.not_none(self._runtime)
        if (
                (health := self._config.health) is not None and
                health.matches(request)
        ):
            await self._send_response(
                driver,
                health.response(healthy=not runtime.shutdown_requested),
            )
            return

        if (activity := runtime.acquire_activity()) is None:
            await self._send_response(driver, FullIoPipelineHttpResponse.simple(
                status=503,
                body=b'shutting down',
            ))
            return

        with activity:
            await self._send_response(
                driver,
                await self._dispatch_application(request),
            )

    async def _run_connection(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ) -> None:
        task = check.not_none(asyncio.current_task())
        driver = PollAsyncioStreamIoPipelineDriver(
            pipeline_http_server_spec(
                max_request_body_bytes=self._config.max_request_body_bytes,
            ),
            reader,
            writer,
        )
        self._drivers[task] = driver
        try:
            async with driver:
                await self._handle_connection(driver)
        except (EOFError, OSError):
            pass
        except asyncio.CancelledError:
            raise
        except BaseException as exc:  # noqa
            log.exception(exc)  # noqa: TRY401
        finally:
            self._drivers.pop(task, None)

    async def run(self, runtime: HttpServerRuntime) -> tuple[str, int]:
        await self.start(runtime)
        try:
            await asyncio.to_thread(runtime.wait_shutdown)
        finally:
            if not runtime.shutdown_requested:
                runtime.request_shutdown('asyncio-pipeline-http-server-exiting')
            await self.close()
        return self.bound_address

    async def close(self) -> bool:
        if self._closing:
            return False
        self._closing = True

        runtime = check.not_none(self._runtime)
        if not runtime.shutdown_requested:
            runtime.request_shutdown('asyncio-pipeline-http-server-closing')

        if (server := self._server) is not None:
            self._server = None
            server.close()
            await server.wait_closed()

        try:
            if self._connections:
                done, pending = await asyncio.wait(
                    self._connections,
                    timeout=runtime.drain_timeout_s,
                )
                for task in done:
                    task.result()
                if pending:
                    for task in pending:
                        if (driver := self._drivers.get(task)) is not None:
                            await driver.close()
                        task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)
                    raise PipelineHttpServerDrainTimeoutError('Asyncio HTTP connections did not drain before timeout')
        finally:
            self._connections.clear()
        return True
