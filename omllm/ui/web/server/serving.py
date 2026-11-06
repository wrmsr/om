"""
An asgi app served over `omcore.io.pipelines` http: one pipeline per connection, each driven by its own asyncio driver,
on a socket bound before anything is served from it - so that its address, an ephemeral port's included, is known up
front.

The app is not run as a task of its own: the pipeline's asgi handler steps it inside the connection's driver, and closes
it when the connection goes. An app wanting to outlive its request - an agent run - starts a task for that.
"""
import asyncio
import socket
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore.http import asgi
from omcore.http.pipelines.requests import FullIoPipelineHttpRequest
from omcore.http.pipelines.servers.apps.asgi import AsgiIoPipelineHandler
from omcore.http.pipelines.servers.requests import IoPipelineHttpRequestAggregatorDecoder
from omcore.http.pipelines.servers.requests import IoPipelineHttpRequestDecoder
from omcore.http.pipelines.servers.responses import IoPipelineHttpResponseChunker
from omcore.http.pipelines.servers.responses import IoPipelineHttpResponseEncoder
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineHandlerNotification
from omcore.io.pipelines.core import IoPipelineHandlerNotifications
from omcore.io.pipelines.drivers.asyncio.streams import PollAsyncioStreamIoPipelineDriver
from omcore.io.pipelines.flow.stub import StubIoPipelineFlowService
from omcore.io.pipelines.sched.types import IoPipelineScheduling
from omcore.logs import all as logs


log = logs.get_module_logger(globals())


##


@ta.final
@dc.dataclass(frozen=True)
class WebServerAddress:
    host: str
    port: int

    @property
    def url(self) -> str:
        host = f'[{self.host}]' if ':' in self.host else self.host
        return f'http://{host}:{self.port}/'


def bind_web_server_socket(host: str, port: int) -> socket.socket:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE)
    family, type_, proto, _, sockaddr = infos[0]

    sock = socket.socket(family, type_, proto)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(sockaddr)
        sock.listen()
        sock.setblocking(False)
    except BaseException:
        sock.close()
        raise

    return sock


def get_web_server_socket_address(sock: socket.socket) -> WebServerAddress:
    host, port, *_ = sock.getsockname()
    return WebServerAddress(host, port)


##


class RequestReadTimeoutIoPipelineHandler(IoPipelineHandler):
    """
    Closes a connection which has not delivered a whole request within the timeout of being opened. A connection carries
    one exchange here, so once its request is in there is nothing left to time: the response takes as long as it takes
    - a streamed one, as long as its submission runs.
    """

    def __init__(self, timeout_s: float) -> None:
        super().__init__()

        check.arg(timeout_s > 0)
        self._timeout_s = timeout_s

        self._handle: IoPipelineScheduling.Handle | None = None
        self._received = False

    def _cancel(self) -> None:
        if (handle := self._handle) is not None:
            self._handle = None
            handle.cancel()

    def _on_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._handle = None

        if not self._received:
            log.debug('Closing a connection which sent no request in %ss', self._timeout_s)
            ctx.feed_final_output()

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            self._handle = ctx.services[IoPipelineScheduling].schedule_context(
                ctx.ref,
                self._timeout_s,
                lambda ctx2: check.isinstance(ctx2.handler, RequestReadTimeoutIoPipelineHandler)._on_timeout(ctx2),  # noqa
            )

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._cancel()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, FullIoPipelineHttpRequest):
            self._received = True
            self._cancel()

        ctx.feed_in(msg)


##


class AsgiPipelineServer:
    def __init__(
            self,
            *,
            app: asgi.App,
            sock: socket.socket,
            request_read_timeout_s: float = 30.,
    ) -> None:
        super().__init__()

        self._app = app
        self._sock = sock
        self._request_read_timeout_s = request_read_timeout_s

        self._server: asyncio.Server | None = None
        self._handlers: set[asyncio.Task] = set()

    def _build_pipeline_spec(
            self,
            *,
            server_address: ta.Any = None,
            client_address: ta.Any = None,
    ) -> IoPipeline.Spec:
        return IoPipeline.Spec(
            [
                IoPipelineHttpRequestDecoder(),
                IoPipelineHttpRequestAggregatorDecoder(),
                RequestReadTimeoutIoPipelineHandler(self._request_read_timeout_s),
                IoPipelineHttpResponseEncoder(),

                # Streamed responses are chunked, each chunk flushed as the app sends it - which takes the flow
                # service, without which the chunker holds everything until the response ends.
                IoPipelineHttpResponseChunker(),

                AsgiIoPipelineHandler(
                    self._app,
                    server_address=server_address,
                    client_address=client_address,
                ),
            ],
            services=[
                StubIoPipelineFlowService(),
            ],
        )

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        task = check.not_none(asyncio.current_task())
        self._handlers.add(task)

        try:
            drv = PollAsyncioStreamIoPipelineDriver(
                self._build_pipeline_spec(
                    server_address=writer.get_extra_info('sockname'),
                    client_address=writer.get_extra_info('peername'),
                ),
                reader,
                writer,
            )

            await drv.loop_until_done()

        except ConnectionError as e:
            # A browser closing a tab mid-stream, say - routine.
            log.debug('Connection lost: %r', e)

        except Exception:
            log.exception('Error serving connection')

        finally:
            self._handlers.discard(task)

    async def start(self) -> None:
        check.none(self._server)

        self._server = await asyncio.start_server(self._handle_client, sock=self._sock)

    async def aclose(self, *, grace_s: float = 1.) -> None:
        """Stops accepting, gives the connections open a moment to finish what they are sending, then cuts them off."""

        if (server := self._server) is not None:
            server.close()

        if handlers := list(self._handlers):
            _, pending = await asyncio.wait(handlers, timeout=grace_s)

            for task in pending:
                task.cancel()

            if pending:
                await asyncio.wait(pending)

        if server is not None:
            await server.wait_closed()

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
