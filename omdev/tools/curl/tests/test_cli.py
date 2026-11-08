import contextlib
import gzip
import http.server
import io
import queue
import threading
import typing as ta

import pytest

from ..cli import main


##


@contextlib.contextmanager
def _server():
    received: queue.Queue[ta.Any] = queue.Queue()

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, fmt, *args):
            pass

        def _read_body(self):
            if self.headers.get('Transfer-Encoding') == 'chunked':
                parts: list[bytes] = []
                while True:
                    size = int(self.rfile.readline().split(b';', 1)[0], 16)
                    if not size:
                        trailers = []
                        while line := self.rfile.readline():
                            if line == b'\r\n':
                                break
                            trailers.append(line.rstrip(b'\r\n'))
                        return b''.join(parts), trailers
                    parts.append(self.rfile.read(size))
                    assert self.rfile.read(2) == b'\r\n'
            length = int(self.headers.get('Content-Length', '0'))
            return self.rfile.read(length), []

        def _handle(self):
            body, trailers = self._read_body()
            received.put((self.command, self.path, self.headers, body, trailers))
            if self.path.startswith('/missing'):
                status, data = 404, b'missing'
            elif self.path.startswith('/json'):
                status, data = 200, b'{"ok":true,"count":2}'
            elif self.path.startswith('/gzip'):
                status, data = 200, gzip.compress(b'compressed reply')
            elif self.path.startswith('/large'):
                status, data = 200, b'x' * 200_000
            else:
                status, data = 200, body or b'hello'
            self.send_response(status)
            self.send_header('Content-Type', 'application/octet-stream')
            if self.path.startswith('/gzip'):
                self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            if self.command != 'HEAD':
                for pos in range(0, len(data), 8192):
                    self.wfile.write(data[pos:pos + 8192])

        def do_GET(self):
            self._handle()

        def do_POST(self):
            self._handle()

        def do_HEAD(self):
            self._handle()

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', received
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _run(args, *, stdin=None):
    out = io.BytesIO()
    err = io.StringIO()
    code = main(args, stdin=stdin, stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


@pytest.mark.parametrize('mode', [[], ['--asyncio']])
def test_get_and_options(mode):
    with _server() as (url, received):
        code, out, err = _run([
            *mode, '-q', 'a=hello world', '-H', 'X-Test: one', '-i', '--show-status',
            url + '/large?x=1',
        ])
        method, path, headers, body, trailers = received.get_nowait()
    assert code == 0
    assert err == '200\n'
    assert out.startswith(b'HTTP 200 OK\r\n')
    assert out.endswith(b'x' * 200_000)
    assert (method, path, body, trailers) == ('GET', '/large?x=1&a=hello+world', b'', [])
    assert headers['X-Test'] == 'one'


class _TrackingReader(io.BytesIO):
    reads = 0

    def read(self, n=-1):
        assert 0 < n <= 1024
        self.reads += 1
        return super().read(n)


@pytest.mark.parametrize('mode', [[], ['--asyncio']])
def test_streamed_upload_and_trailers(mode):
    source = _TrackingReader(b'abc' * 5000)
    with _server() as (url, received):
        code, out, err = _run([
            *mode, '--data-file', '-', '--chunk-size', '1024',
            '--trailer', 'X-Checksum: done', url + '/upload',
        ], stdin=source)
        method, path, headers, body, trailers = received.get_nowait()
    assert code == 0, err
    assert out == body == b'abc' * 5000
    assert source.reads > 10
    assert (method, path) == ('POST', '/upload')
    assert headers['Transfer-Encoding'] == 'chunked'
    assert trailers == [b'X-Checksum: done']


@pytest.mark.parametrize('mode', [[], ['--asyncio']])
def test_json_gzip_head_and_fail(mode):
    with _server() as (url, received):
        code, out, err = _run([*mode, '--json', '{"a":1}', url + '/echo'])
        method, _, headers, body, _ = received.get_nowait()
        assert (code, out, err) == (0, body, '')
        assert method == 'POST'
        assert headers['Content-Type'] == 'application/json'

        assert _run([*mode, '--pretty', url + '/json'])[:2] == (0, b'{\n  "ok": true,\n  "count": 2\n}\n')
        received.get_nowait()

        assert _run([*mode, '--compressed', url + '/gzip'])[:2] == (0, b'compressed reply')
        received.get_nowait()

        code, out, _ = _run([*mode, '--head', url + '/echo'])
        received.get_nowait()
        assert code == 0
        assert out.startswith(b'HTTP 200 OK\r\n')
        assert out.endswith(b'\r\n\r\n')

        assert _run([*mode, '--fail', url + '/missing'])[:2] == (22, b'missing')


def test_invalid_header_does_not_connect():
    code, _, err = _run(['-H', 'X-Test: ok\r\nInjected: yes', 'http://127.0.0.1:1/'])
    assert code == 2
    assert 'invalid HTTP header value' in err
