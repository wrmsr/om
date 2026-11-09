# ruff: noqa: UP045
# @om-lite
import errno
import socket
import typing as ta

from ......io.pipelines.core import IoPipeline
from ......io.pipelines.core import IoPipelineHandler
from ......io.pipelines.core import IoPipelineHandlerContext
from ......io.pipelines.drivers.sync.sockets import SocketSyncIoPipelineDriver
from ....requests import IoPipelineHttpRequestHead
from ....requests import IoPipelineHttpRequestObject
from ....responses import FullIoPipelineHttpResponse
from ...requests import IoPipelineHttpRequestDecoder
from ...responses import IoPipelineHttpResponseEncoder


##


class PingHandler(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if not isinstance(msg, IoPipelineHttpRequestHead):
            if not isinstance(msg, IoPipelineHttpRequestObject):
                ctx.feed_in(msg)
            return

        if msg.method == 'GET' and msg.target == '/ping':
            ctx.feed_out(FullIoPipelineHttpResponse.simple(
                status=200,
                body=b'pong',
            ))

        else:
            ctx.feed_out(FullIoPipelineHttpResponse.simple(
                status=404,
                body=b'not found',
            ))

        ctx.feed_final_output()


def build_http_ping_spec() -> IoPipeline.Spec:
    return IoPipeline.Spec([
        IoPipelineHttpRequestDecoder(),
        IoPipelineHttpResponseEncoder(),
        PingHandler(),
    ])


def serve_ping(
        *,
        host: str = '127.0.0.1',
        port: int = 8087,
) -> None:
    def _handle_client(conn: socket.socket, addr: ta.Any) -> None:  # noqa
        try:
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError as e:
            if e.errno != errno.ENOPROTOOPT:
                raise

        drv = SocketSyncIoPipelineDriver(
            build_http_ping_spec(),
            conn,
        )

        drv.loop_until_done()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()

        while True:
            conn, addr = server.accept()
            _handle_client(conn, addr)


def main() -> None:
    serve_ping()


if __name__ == '__main__':
    main()
