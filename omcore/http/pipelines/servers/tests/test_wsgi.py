# ruff: noqa: UP006 UP007 UP045
# @om-lite
import sys
import typing as ta
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.flow.stub import StubIoPipelineFlowService
from .....io.pipelines.flow.types import IoPipelineFlowMessages
from .....io.pipelines.yielding import CountingIoPipelineYieldPolicy
from .....io.pipelines.yielding import NeverIoPipelineYieldPolicy
from .....io.streambufs.utils import ByteStreamBuffers
from .....lite.check import check
from ...requests import FullIoPipelineHttpRequest
from ...responses import FullIoPipelineHttpResponse
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..apps.wsgi import IoPipelineWsgiConfig
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


def drain_wsgi(
        channel: IoPipeline,
        *,
        max_turns: int = 1000,
) -> ta.List[ta.Any]:
    """Drains output, running deferrals as they appear, until the pipeline is quiescent."""

    out: ta.List[ta.Any] = []

    for _ in range(max_turns):
        if not (msgs := channel.output.drain()):
            return out

        deferred: ta.List[IoPipelineMessages.Defer] = []
        for msg in msgs:
            if isinstance(msg, IoPipelineMessages.Defer):
                deferred.append(msg)
            else:
                out.append(msg)

        for dfl in deferred:
            channel.run_deferred(dfl)

    raise RuntimeError('WSGI pipeline did not settle')


def _run_wsgi(app, target='/ping', *, handler=None, **kwargs) -> FullIoPipelineHttpResponse:
    """Reassembles the streamed response so tests can assert against it as a whole."""

    channel = IoPipeline.new(
        [handler if handler is not None else WsgiIoPipelineHandler(app)],
        IoPipeline.Config(inbound_terminal='drop'),
    )
    try:
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', target, **kwargs))
        out = drain_wsgi(channel)
    finally:
        channel.destroy()

    return reassemble_wsgi_response(out)


def reassemble_wsgi_response(out: ta.Sequence[ta.Any]) -> FullIoPipelineHttpResponse:
    types = [type(msg) for msg in out]
    if (
            len(out) < 3 or
            types[0] is not IoPipelineHttpResponseHead or
            types[-2] is not IoPipelineHttpResponseEnd or
            types[-1] is not IoPipelineMessages.FinalOutput or
            any(ty is not IoPipelineHttpResponseBodyData for ty in types[1:-2])
    ):
        raise AssertionError(types)

    return FullIoPipelineHttpResponse(
        head=out[0],
        body=b''.join(ByteStreamBuffers.to_bytes(msg.data, strict=True) for msg in out[1:-2]),
    )


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


##


def _new_streaming_pipeline(
        app,
        *,
        config: IoPipelineWsgiConfig = IoPipelineWsgiConfig.DEFAULT,
        flow: bool = False,
        raise_immediately: bool = False,
) -> ta.Tuple[IoPipeline, WsgiIoPipelineHandler]:
    handler = WsgiIoPipelineHandler(app, config=config)
    return (
        IoPipeline.new(
            [handler],
            IoPipeline.Config(inbound_terminal='drop', raise_immediately=raise_immediately),
            services=[StubIoPipelineFlowService()] if flow else [],
        ),
        handler,
    )


def _turns(channel: IoPipeline, max_turns: int = 100) -> ta.List[ta.List[ta.Any]]:
    """Drains one driver turn at a time, so the interleaving of data and deferrals is observable."""

    turns: ta.List[ta.List[ta.Any]] = []

    for _ in range(max_turns):
        if not (msgs := channel.output.drain()):
            return turns

        turns.append(list(msgs))

        for msg in msgs:
            if isinstance(msg, IoPipelineMessages.Defer):
                channel.run_deferred(msg)

    raise RuntimeError('WSGI pipeline did not settle')


def _framed_app(*chunks: bytes):
    """An app which declares its own Content-Length and streams the given chunks."""

    def app(environ, start_response):  # noqa
        start_response('200 OK', [('Content-Length', str(sum(map(len, chunks))))])
        return iter(chunks)

    return app


class TestWsgiStreaming(unittest.TestCase):
    def test_body_is_streamed_not_aggregated(self) -> None:
        channel, _ = _new_streaming_pipeline(_framed_app(b'aaa', b'bbb', b'ccc'))
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))

        out = drain_wsgi(channel)

        self.assertEqual(
            [type(msg) for msg in out],
            [
                IoPipelineHttpResponseHead,
                IoPipelineHttpResponseBodyData,
                IoPipelineHttpResponseBodyData,
                IoPipelineHttpResponseBodyData,
                IoPipelineHttpResponseEnd,
                IoPipelineMessages.FinalOutput,
            ],
        )
        self.assertNotIn(FullIoPipelineHttpResponse, [type(msg) for msg in out])

    def test_one_chunk_per_turn_by_default(self) -> None:
        channel, _ = _new_streaming_pipeline(_framed_app(b'aaa', b'bbb', b'ccc'))
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))

        turns = _turns(channel)

        # Head + first chunk, then one chunk per turn, then the terminator - and the deferral trails its own data so
        # the driver writes the bytes before resuming us.
        self.assertEqual(
            [[type(msg) for msg in turn] for turn in turns],
            [
                [IoPipelineHttpResponseHead, IoPipelineHttpResponseBodyData, IoPipelineMessages.Defer],
                [IoPipelineHttpResponseBodyData, IoPipelineMessages.Defer],
                [IoPipelineHttpResponseBodyData, IoPipelineMessages.Defer],
                [IoPipelineHttpResponseEnd, IoPipelineMessages.FinalOutput],
            ],
        )

    def test_yield_policy_is_configurable(self) -> None:
        channel, _ = _new_streaming_pipeline(
            _framed_app(b'aaa', b'bbb', b'ccc'),
            config=IoPipelineWsgiConfig(yield_policy=CountingIoPipelineYieldPolicy(2)),
        )
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))

        self.assertEqual(len(_turns(channel)), 2)

    def test_never_yielding_policy_completes_in_one_turn(self) -> None:
        channel, _ = _new_streaming_pipeline(
            _framed_app(b'aaa', b'bbb', b'ccc'),
            config=IoPipelineWsgiConfig(yield_policy=NeverIoPipelineYieldPolicy()),
        )
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))

        turns = _turns(channel)
        self.assertEqual(len(turns), 1)
        self.assertNotIn(IoPipelineMessages.Defer, [type(msg) for msg in turns[0]])

    def test_flush_output_per_chunk_under_flow(self) -> None:
        channel, _ = _new_streaming_pipeline(_framed_app(b'aaa', b'bbb'), flow=True)
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))

        out = drain_wsgi(channel)

        self.assertEqual(
            sum(isinstance(msg, IoPipelineFlowMessages.FlushOutput) for msg in out),
            3,  # head+chunk, chunk, terminator
        )

        # Nothing may follow FinalOutput at the terminal - the fence has to precede it.
        self.assertIsInstance(out[-1], IoPipelineMessages.FinalOutput)
        self.assertIsInstance(out[-2], IoPipelineFlowMessages.FlushOutput)


class TestWsgiStreamingBackpressure(unittest.TestCase):
    def test_pause_parks_the_pump_and_ready_resumes_it(self) -> None:
        channel, _ = _new_streaming_pipeline(
            _framed_app(b'aaa', b'bbb', b'ccc'),
            flow=True,
        )
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))

        first = channel.output.drain()
        self.assertIsInstance(first[0], IoPipelineHttpResponseHead)

        channel.feed_in(IoPipelineFlowMessages.PauseOutput())
        for msg in first:
            if isinstance(msg, IoPipelineMessages.Defer):
                channel.run_deferred(msg)

        # Parked: the deferred pump produced nothing.
        self.assertEqual(channel.output.drain(), [])

        channel.feed_in(IoPipelineFlowMessages.ReadyForOutput())

        rest = [msg for turn in _turns(channel) for msg in turn]
        self.assertIsInstance(rest[-1], IoPipelineMessages.FinalOutput)
        self.assertEqual(
            sum(isinstance(msg, IoPipelineHttpResponseBodyData) for msg in rest),
            2,
        )

    def test_pause_before_the_request_blocks_the_first_chunk(self) -> None:
        channel, _ = _new_streaming_pipeline(
            _framed_app(b'aaa'),
            flow=True,
        )

        channel.feed_in(IoPipelineFlowMessages.PauseOutput())
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))

        self.assertEqual(channel.output.drain(), [])

        channel.feed_in(IoPipelineFlowMessages.ReadyForOutput())

        out = [msg for turn in _turns(channel) for msg in turn]
        self.assertIsInstance(out[0], IoPipelineHttpResponseHead)


class TestWsgiStreamingHeaders(unittest.TestCase):
    def test_head_is_withheld_until_the_first_non_empty_chunk(self) -> None:
        # PEP 3333: nothing may be transmitted until the app produces real data, which is what makes the exc_info
        # re-invocation of start_response meaningful.
        seen: ta.List[ta.Any] = []

        def app(environ, start_response):  # noqa
            start_response('200 OK', [('Content-Length', '3')])

            def gen():
                yield b''
                seen.append(tuple(type(m).__name__ for m in channel.output.drain()))
                yield b'abc'

            return gen()

        channel, _ = _new_streaming_pipeline(app)
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))
        _turns(channel)

        # Nothing at all had gone out by the time the empty chunk was processed - in particular, no head.
        self.assertEqual(seen, [()])

    def test_exc_info_replaces_before_the_head_is_sent(self) -> None:
        def app(environ, start_response):  # noqa
            start_response('200 OK', [])
            try:
                raise RuntimeError('boom')
            except RuntimeError:
                start_response('500 Internal Server Error', [], sys.exc_info())
            return [b'error']

        self.assertEqual(_run_wsgi(app).head.status, 500)

    def test_exc_info_re_raises_once_the_head_is_sent(self) -> None:
        error = RuntimeError('boom')

        def app(environ, start_response):  # noqa
            write = start_response('200 OK', [('Content-Length', '3')])

            def gen():
                yield b'abc'
                try:
                    raise error
                except RuntimeError:
                    # Too late - the peer already has the head.
                    start_response('500 Internal Server Error', [], sys.exc_info())
                yield b'unreachable'

            del write
            return gen()

        channel, _ = _new_streaming_pipeline(app, raise_immediately=True)
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))

        with self.assertRaises(RuntimeError) as raised:
            _turns(channel)

        self.assertIs(raised.exception, error)

    def test_undeclared_framing_is_close_delimited(self) -> None:
        def app(environ, start_response):  # noqa
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [b'hi']

        head = _run_wsgi(app).head

        self.assertTrue(head.headers.contains_list_value('connection', 'close', ignore_case=True))

    def test_declared_content_length_is_left_alone(self) -> None:
        def app(environ, start_response):  # noqa
            start_response('200 OK', [('Content-Length', '2')])
            return [b'hi']

        self.assertNotIn('connection', _run_wsgi(app).head.headers)

    def test_declared_chunked_is_left_alone(self) -> None:
        def app(environ, start_response):  # noqa
            start_response('200 OK', [('Transfer-Encoding', 'chunked')])
            return [b'hi']

        self.assertNotIn('connection', _run_wsgi(app).head.headers)


class TestWsgiStreamingLifecycle(unittest.TestCase):
    def test_close_is_called_on_mid_stream_error(self) -> None:
        closing = _ClosingIterable([])

        def app(environ, start_response):  # noqa
            start_response('200 OK', [('Content-Length', '3')])

            def gen():
                yield b'abc'
                raise RuntimeError('boom')

            closing._chunks = gen()  # noqa
            return closing

        channel, _ = _new_streaming_pipeline(app, raise_immediately=True)
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))

        with self.assertRaises(RuntimeError):
            _turns(channel)

        self.assertTrue(closing.closed)

    def test_removal_closes_an_in_flight_app(self) -> None:
        closing = _ClosingIterable([b'a', b'b', b'c'])

        def app(environ, start_response):  # noqa
            start_response('200 OK', [('Content-Length', '3')])
            return closing

        channel, handler = _new_streaming_pipeline(app)
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))

        self.assertFalse(closing.closed)

        channel.remove(check.not_none(channel.find_handler(handler)))

        self.assertTrue(closing.closed)

    def test_final_input_abandons_an_in_flight_app(self) -> None:
        closing = _ClosingIterable([b'a', b'b', b'c'])

        def app(environ, start_response):  # noqa
            start_response('200 OK', [('Content-Length', '3')])
            return closing

        channel, _ = _new_streaming_pipeline(app)
        channel.feed_in(FullIoPipelineHttpRequest.simple('test', '/x'))
        channel.output.drain()

        channel.feed_final_input()

        self.assertTrue(closing.closed)
