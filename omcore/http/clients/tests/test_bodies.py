import asyncio
import contextlib
import gzip
import http.server
import threading

import pytest

from ..base import HttpClientError
from ..base import HttpClientRequest
from ..httpx import HttpxAsyncHttpClient
from ..httpx import HttpxHttpClient
from ..middleware import MiddlewareHttpClient
from ..middleware import RedirectHandlingHttpClientMiddleware
from ..pipelines.asyncio import AsyncioIoPipelineAsyncHttpClient
from ..pipelines.sync import IoPipelineHttpClient
from ..pipelines.tests.test_transport_errors import ResettingLoopbackHttpServer
from ..urllib import UrllibHttpClient


PAYLOAD = b'hello, compressed world! ' * 20
GZIPPED = gzip.compress(PAYLOAD)


class _GzipHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa
        if self.path == '/redir':
            self.send_response(302)
            self.send_header('Location', '/gz')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        self.send_response(200)
        self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', str(len(GZIPPED)))
        self.end_headers()
        self.wfile.write(GZIPPED)

    def log_message(self, format, *args):  # noqa
        pass


@pytest.fixture
def gzip_server():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _GzipHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f'http://127.0.0.1:{srv.server_address[1]}'
    finally:
        srv.shutdown()
        srv.server_close()
        t.join()


SYNC_CLIENTS = {
    'urllib': (UrllibHttpClient, GZIPPED),
    'httpx': (HttpxHttpClient, PAYLOAD),
    'pipelines': (IoPipelineHttpClient, PAYLOAD),
}


@pytest.mark.parametrize('name', list(SYNC_CLIENTS))
def test_sync_no_decompress(gzip_server, name):
    cls, default_body = SYNC_CLIENTS[name]
    with cls() as cli:
        assert cli.request(HttpClientRequest(gzip_server + '/gz')).data == default_body
        assert cli.request(HttpClientRequest(gzip_server + '/gz', no_decompress=True)).data == GZIPPED


def test_redirect_keeps_no_decompress(gzip_server):
    with MiddlewareHttpClient(IoPipelineHttpClient(), [RedirectHandlingHttpClientMiddleware()]) as cli:
        assert cli.request(HttpClientRequest(gzip_server + '/redir')).data == PAYLOAD
        assert cli.request(HttpClientRequest(gzip_server + '/redir', no_decompress=True)).data == GZIPPED


def test_request_repr():
    assert 'no_decompress' not in repr(HttpClientRequest('http://x/'))
    assert 'True' in repr(HttpClientRequest('http://x/', no_decompress=True))


@pytest.mark.asyncs('asyncio')
@pytest.mark.parametrize('cls', [HttpxAsyncHttpClient, AsyncioIoPipelineAsyncHttpClient])
async def test_async_no_decompress(gzip_server, cls):
    async with cls() as cli:
        assert (await cli.request(HttpClientRequest(gzip_server + '/gz'))).data == PAYLOAD
        assert (await cli.request(HttpClientRequest(gzip_server + '/gz', no_decompress=True))).data == GZIPPED


##


@contextlib.contextmanager
def _resetting_server():
    server = ResettingLoopbackHttpServer()
    try:
        yield server
    finally:
        server.close()


@pytest.mark.parametrize('cls', [UrllibHttpClient, HttpxHttpClient])
def test_sync_reset_mid_body(cls):
    with _resetting_server() as server:
        with cls() as cli:
            with cli.stream_request(HttpClientRequest(f'http://127.0.0.1:{server.port}/', timeout_s=5.)) as resp:
                server.wait_sent()
                server.reset()
                with pytest.raises(HttpClientError):
                    resp.stream.read()


@pytest.mark.asyncs('asyncio')
async def test_httpx_async_reset_mid_body():
    with _resetting_server() as server:
        async with HttpxAsyncHttpClient() as cli:
            resp = await cli.stream_request(HttpClientRequest(f'http://127.0.0.1:{server.port}/', timeout_s=5.))
            async with resp:
                await asyncio.get_running_loop().run_in_executor(None, server.wait_sent)
                server.reset()
                with pytest.raises(HttpClientError):
                    await resp.stream.read()
