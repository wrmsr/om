# ruff: noqa: UP006 UP007 UP045
# @om-lite
import sys
import typing as ta
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineMessages
from ...requests import FullIoPipelineHttpRequest
from ...responses import FullIoPipelineHttpResponse
from ..apps.wsgi import WsgiIoPipelineHandler
from .demos.http_server_wsgi import ping_app


##


class _ClosingIterable:
    def __init__(self, chunks: ta.Sequence[bytes]) -> None:
        super().__init__()

        self._chunks = chunks
        self.closed = False

    def __iter__(self) -> ta.Iterator[bytes]:
        return iter(self._chunks)

    def close(self) -> None:
        self.closed = True


def _run_wsgi(app, target='/ping', **kwargs) -> FullIoPipelineHttpResponse:
    channel = IoPipeline.new(
        [WsgiIoPipelineHandler(app)],
        IoPipeline.Config(inbound_terminal='drop'),
    )
    try:
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', target, **kwargs))
        out = channel.output.drain()
    finally:
        channel.destroy()

    if [type(msg) for msg in out] != [FullIoPipelineHttpResponse, IoPipelineMessages.FinalOutput]:
        raise AssertionError(out)

    return out[0]


##


class TestWsgiStartResponse(unittest.TestCase):
    def test_accepts_exc_info(self) -> None:
        """PEP 3333 requires the third `exc_info` parameter - middleware passes it on error paths."""

        def app(environ, start_response):  # noqa
            start_response('200 OK', [('Content-Type', 'text/plain')])
            try:
                raise RuntimeError('boom')
            except RuntimeError:
                start_response('500 Internal Server Error', [('Content-Type', 'text/plain')], sys.exc_info())
            return [b'error']

        resp = _run_wsgi(app)

        self.assertEqual(resp.head.status, 500)
        self.assertEqual(resp.head.reason, 'Internal Server Error')
        self.assertEqual(resp.body, b'error')

    def test_returns_write_callable(self) -> None:
        """PEP 3333 requires start_response to return a `write(body_data)` callable."""

        def app(environ, start_response):  # noqa
            write = start_response('200 OK', [('Content-Type', 'text/plain')])
            write(b'hello ')
            write(b'world')
            return []

        resp = _run_wsgi(app)

        self.assertEqual(resp.head.status, 200)
        self.assertEqual(resp.body, b'hello world')

    def test_write_output_precedes_iterable_output(self) -> None:
        def app(environ, start_response):  # noqa
            write = start_response('200 OK', [])
            write(b'1')

            def gen():
                yield b'2'
                write(b'3')
                yield b'4'

            return gen()

        self.assertEqual(_run_wsgi(app).body, b'1234')


class TestWsgiReturnValues(unittest.TestCase):
    def test_generator(self) -> None:
        def app(environ, start_response):  # noqa
            start_response('200 OK', [])

            def gen():
                yield b'a'
                yield b'b'
                yield b'c'

            return gen()

        self.assertEqual(_run_wsgi(app).body, b'abc')

    def test_iterator(self) -> None:
        def app(environ, start_response):  # noqa
            start_response('200 OK', [])
            return iter([b'x', b'y'])

        self.assertEqual(_run_wsgi(app).body, b'xy')

    def test_list(self) -> None:
        def app(environ, start_response):  # noqa
            start_response('200 OK', [])
            return [b'l', b'r']

        self.assertEqual(_run_wsgi(app).body, b'lr')

    def test_bytes(self) -> None:
        def app(environ, start_response):  # noqa
            start_response('200 OK', [])
            return b'raw'

        self.assertEqual(_run_wsgi(app).body, b'raw')

    def test_close_is_called(self) -> None:
        it = _ClosingIterable([b'z'])

        def app(environ, start_response):  # noqa
            start_response('200 OK', [])
            return it

        self.assertEqual(_run_wsgi(app).body, b'z')
        self.assertTrue(it.closed)


class TestWsgiEnviron(unittest.TestCase):
    @staticmethod
    def _environ_app(out: ta.List[ta.Any]):
        def app(environ, start_response):
            out.append(environ)
            start_response('200 OK', [])
            return []

        return app

    def test_path_info_and_query_string(self) -> None:
        environs: ta.List[ta.Any] = []

        _run_wsgi(self._environ_app(environs), '/ping?x=1&y=2')

        self.assertEqual(environs[0]['PATH_INFO'], '/ping')
        self.assertEqual(environs[0]['QUERY_STRING'], 'x=1&y=2')

    def test_path_info_is_url_decoded(self) -> None:
        environs: ta.List[ta.Any] = []

        _run_wsgi(self._environ_app(environs), '/pi%20ng?q=a%20b')

        self.assertEqual(environs[0]['PATH_INFO'], '/pi ng')
        self.assertEqual(environs[0]['QUERY_STRING'], 'q=a%20b')

    def test_no_query_string(self) -> None:
        environs: ta.List[ta.Any] = []

        _run_wsgi(self._environ_app(environs), '/ping')

        self.assertEqual(environs[0]['PATH_INFO'], '/ping')
        self.assertEqual(environs[0]['QUERY_STRING'], '')

    def test_cgi_and_wsgi_keys(self) -> None:
        environs: ta.List[ta.Any] = []

        _run_wsgi(
            self._environ_app(environs),
            '/upload',
            method='POST',
            body=b'payload',
            content_type='text/plain',
        )

        environ = environs[0]
        self.assertEqual(environ['REQUEST_METHOD'], 'POST')
        self.assertEqual(environ['SCRIPT_NAME'], '')
        self.assertEqual(environ['SERVER_PROTOCOL'], 'HTTP/1.1')
        self.assertEqual(environ['HTTP_HOST'], 'test')
        self.assertEqual(environ['CONTENT_TYPE'], 'text/plain')
        self.assertEqual(environ['CONTENT_LENGTH'], '7')
        self.assertNotIn('HTTP_CONTENT_LENGTH', environ)
        self.assertEqual(environ['wsgi.version'], (1, 0))
        self.assertEqual(environ['wsgi.url_scheme'], 'http')
        self.assertEqual(environ['wsgi.input'].read(), b'payload')


class TestWsgiPingDemo(unittest.TestCase):
    def test_ping_with_query_string_is_routed(self) -> None:
        resp = _run_wsgi(ping_app, '/ping?x=1')

        self.assertEqual(resp.head.status, 200)
        self.assertEqual(resp.body, b'pong')

    def test_ping_without_query_string_is_routed(self) -> None:
        resp = _run_wsgi(ping_app, '/ping')

        self.assertEqual(resp.head.status, 200)
        self.assertEqual(resp.body, b'pong')

    def test_unknown_path_is_not_found(self) -> None:
        resp = _run_wsgi(ping_app, '/nope')

        self.assertEqual(resp.head.status, 404)
        self.assertEqual(resp.body, b'not found')
