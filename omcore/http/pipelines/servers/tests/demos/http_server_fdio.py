# ruff: noqa: PYI034 UP006 UP037 UP045
# @om-lite
import functools
import socket
import typing as ta
import weakref

from ......io.fdio.handlers import ServerSocketFdioHandler
from ......io.fdio.manager import FdioManager
from ......io.fdio.pollers import SelectFdioPoller
from ......io.pipelines.core import IoPipeline
from ......io.pipelines.core import IoPipelineHandler
from ......io.pipelines.core import IoPipelineHandlerContext
from ......io.pipelines.drivers.fdio import IoPipelineDriverSocketFdioHandler
from ......io.pipelines.sched.types import IoPipelineScheduling
from ......lite.check import check
from ......sockets.addresses import SocketAddress
from ....requests import IoPipelineHttpRequestHead
from ....requests import IoPipelineHttpRequestObject
from ....responses import FullIoPipelineHttpResponse
from ...requests import IoPipelineHttpRequestDecoder
from ...responses import IoPipelineHttpResponseEncoder


##


class PingHandler(IoPipelineHandler):
    """Respond to a single HTTP request after crossing the fdio scheduling path."""

    @staticmethod
    def _respond(
            ctx: IoPipelineHandlerContext,
            *,
            status: int,
            body: bytes,
    ) -> None:
        ctx.feed_out(FullIoPipelineHttpResponse.simple(status=status, body=body))
        ctx.feed_final_output()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if not isinstance(msg, IoPipelineHttpRequestHead):
            if not isinstance(msg, IoPipelineHttpRequestObject):
                ctx.feed_in(msg)
            return

        if msg.method == 'GET' and msg.target == '/ping':
            status, body = 200, b'pong'
        else:
            status, body = 404, b'not found'

        ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            0.,
            functools.partial(self._respond, status=status, body=body),
        )


def build_http_ping_spec() -> IoPipeline.Spec:
    return IoPipeline.Spec([
        IoPipelineHttpRequestDecoder(),
        IoPipelineHttpResponseEncoder(),
        PingHandler(),
    ])


##


class FdioHttpPingServer:
    """Small, single-threaded fdio HTTP server intended for manual use and integration tests."""

    def __init__(
            self,
            *,
            host: str = '127.0.0.1',
            port: int = 8087,
    ) -> None:
        super().__init__()

        self._closed = False
        self._poller = SelectFdioPoller()
        self._manager = FdioManager(self._poller)
        self._connections: ta.Set[IoPipelineDriverSocketFdioHandler] = set()

        server_sock = socket.create_server((host, port))
        self._address: SocketAddress = server_sock.getsockname()

        self_ref = weakref.ref(self)

        def on_connect(sock: socket.socket, addr: SocketAddress) -> None:
            check.not_none(self_ref())._on_connect(sock, addr)  # noqa

        try:
            self._server = ServerSocketFdioHandler(server_sock, on_connect)
            self._manager.register(self._server)
        except BaseException:
            server_sock.close()
            self._poller.close()
            raise

    @property
    def address(self) -> SocketAddress:
        return self._address

    @property
    def port(self) -> int:
        return ta.cast(ta.Tuple[str, int], self._address)[1]

    @property
    def closed(self) -> bool:
        return self._closed

    def _on_connect(self, sock: socket.socket, addr: SocketAddress) -> None:
        conn = IoPipelineDriverSocketFdioHandler(sock, addr, build_http_ping_spec())
        try:
            check.none(conn.next(read=False))
            check.state(conn.is_active)
            self._manager.register(conn)
            self._connections.add(conn)
        except BaseException:
            conn.close()
            raise

    def poll(self, *, timeout: ta.Optional[float] = None) -> None:
        check.state(not self._closed)

        self._manager.poll(timeout=timeout)
        self._connections = {conn for conn in self._connections if not conn.closed}

    def serve_forever(self) -> None:
        while not self._closed:
            self.poll()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        try:
            self._server.close()
            for conn in self._connections:
                conn.close()
            self._connections.clear()

            self._manager.poll(timeout=0.)
        finally:
            self._poller.close()

    def __enter__(self) -> 'FdioHttpPingServer':
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def serve_ping(
        *,
        host: str = '127.0.0.1',
        port: int = 8087,
) -> None:
    with FdioHttpPingServer(host=host, port=port) as server:
        server.serve_forever()


def main() -> None:
    serve_ping()


if __name__ == '__main__':
    main()
