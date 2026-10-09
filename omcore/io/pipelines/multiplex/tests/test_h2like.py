# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
import typing as ta
import unittest

from ...drivers.pure import PureIoPipelineDriver
from ...drivers.types import IoPipelineDriverState
from ..types import ConnectionClosedMultiplexError
from ..types import MultiplexMessages
from ..types import MultiplexOpenedStream
from ..types import StreamResetMultiplexError
from .apps import AppFactory
from .apps import StreamApp
from .apps import app_spec
from .apps import payload
from .h2like import H2Data
from .h2like import H2LikeAdapter
from .h2like import H2RstStream
from .h2like import H2WindowUpdate
from .h2like import Headers
from .h2like import SendRaw
from .h2like import SendSettings
from .h2like import h2_like_spec
from .links import PureLink


##


class _Outcome:
    def __init__(self, msg: ta.Any) -> None:
        self.result: ta.Any = None
        self.exc: ta.Optional[BaseException] = None
        self.done = False
        msg.add_listener(self._done)

    def _done(self, m: ta.Any) -> None:
        self.done = True
        if m.is_succeeded():
            self.result = m.get_result()
        else:
            self.exc = m.get_exception()


class _H2Peer:
    def __init__(
            self,
            role: ta.Literal['client', 'server'],
            factory: AppFactory,
            *,
            adapter: ta.Optional[H2LikeAdapter] = None,
            **kwargs: ta.Any,
    ) -> None:
        super().__init__()

        self.factory = factory
        spec, self.mux = h2_like_spec(role, factory, adapter=adapter, **kwargs)
        self.adapter: H2LikeAdapter = self.mux.adapter  # type: ignore[assignment]
        self.driver = PureIoPipelineDriver(spec)

    def open(self, app: StreamApp, *, auto_read: bool = True) -> _Outcome:
        msg = MultiplexMessages.OpenStream(app_spec(app, auto_read=auto_read))
        outcome = _Outcome(msg)
        self.driver.enqueue(msg)
        return outcome


def _request(i: ta.Any, body: bytes = b'', *, end: bool = True, **kwargs: ta.Any) -> StreamApp:
    return StreamApp(prelude=[Headers(f'GET /{i}')], send=body, shutdown_after_send=end, **kwargs)


def _responder(o: ta.Any, *, size: int = 30_000, **kwargs: ta.Any) -> StreamApp:
    return StreamApp(respond=payload(('resp', o.key), size), respond_messages=[Headers('trailer: done')], **kwargs)


class TestH2LikeMultiplexing(unittest.TestCase):
    def _pair(
            self,
            server_factory: AppFactory,
            *,
            capacity: ta.Optional[int] = 64 * 1024,
            client_adapter: ta.Optional[H2LikeAdapter] = None,
            server_adapter: ta.Optional[H2LikeAdapter] = None,
            **kwargs: ta.Any,
    ) -> ta.Tuple[_H2Peer, _H2Peer, PureLink]:
        client = _H2Peer('client', AppFactory(lambda o: StreamApp()), adapter=client_adapter, **kwargs)
        server = _H2Peer('server', server_factory, adapter=server_adapter, **kwargs)
        return client, server, PureLink(client.driver, server.driver, capacity=capacity)

    def test_many_concurrent_streams_with_headers_trailers_and_padding(self) -> None:
        n = 20
        bodies = {i: payload(('body', i), 10_000 + 503 * i) for i in range(n)}
        manual = lambda o: ta.cast(int, o.key) % 4 == 1  # noqa
        server_factory = AppFactory(
            lambda o: _responder(o, manual_read=manual(o)),
            auto_read=lambda o: not manual(o),
        )
        client, server, link = self._pair(
            server_factory,
            client_adapter=H2LikeAdapter('client', pad=7),
            server_adapter=H2LikeAdapter('server', pad=3),
            connection_send_window=20_000,
            connection_recv_window=20_000,
        )
        try:
            apps = {i: _request(i, bodies[i]) for i in range(n)}
            for app in apps.values():
                client.open(app)

            link.pump()

            # Stream ids are allocated by parity, in order.
            self.assertEqual(sorted(server_factory.apps), list(range(1, 2 * n, 2)))
            for i, app in apps.items():
                with self.subTest(stream=i):
                    sid = 2 * i + 1
                    self.assertTrue(bytes(app.received) == payload(('resp', sid), 30_000))
                    self.assertEqual(app.messages, [Headers('trailer: done')])
                    self.assertTrue(app.final_output.is_succeeded())
                    self.assertEqual(app.errors, [])
                    sapp = server_factory.apps[sid]
                    self.assertEqual(sapp.messages, [Headers(f'GET /{i}')])
                    self.assertTrue(bytes(sapp.received) == bodies[i])
                    self.assertTrue(sapp.final_output.is_succeeded())

            self.assertEqual(len(client.mux.streams), 0)
            self.assertEqual(len(server.mux.streams), 0)
            # Padding was charged against credit, beyond the data itself.
            self.assertGreater(client.mux.credit.totals().send_consumed, sum(map(len, bodies.values())))
        finally:
            link.close()

    def test_settings_drive_send_credit_negative_then_recover(self) -> None:
        body = payload('big', 60_000)
        server_factory = AppFactory(lambda o: StreamApp(manual_read=True))
        client, server, link = self._pair(server_factory, capacity=None)
        try:
            app = _request('post', body)
            client.open(app)
            link.pump(until=lambda: bool(server_factory.apps))
            (sid,) = server_factory.apps

            # The server shrinks every stream window by more than the client has left: credit goes negative.
            server.driver.enqueue(SendSettings(16 * 1024 - 40_000))
            link.pump(until=lambda: client.mux.credit.send_available(sid) < 0)
            self.assertLess(client.mux.credit.send_available(sid), 0)
            self.assertFalse(client.mux._scheduler.is_ready(sid))  # noqa

            sapp = server_factory.apps[sid]
            link.pump()
            self.assertLess(len(sapp.received), len(body))

            # Raising the setting again shifts every window back up; the transfer then completes.
            server.driver.enqueue(SendSettings(16 * 1024))
            link.pump()
            self.assertTrue(bytes(sapp.received) == body)
            self.assertTrue(sapp.saw_final_input)
            self.assertTrue(app.shutdown_output.is_succeeded())
        finally:
            link.close()

    def test_zero_window_opened_later(self) -> None:
        server_factory = AppFactory(lambda o: StreamApp())
        # The client starts with a zero send window; the server then opens it explicitly.
        client, server, link = self._pair(
            server_factory,
            client_adapter=H2LikeAdapter('client', peer_initial_window=0),
        )
        try:
            body = payload('z', 5000)
            app = _request('post', body)
            client.open(app)
            link.pump()

            (sid,) = server_factory.apps
            sapp = server_factory.apps[sid]
            # The headers flowed - they cost no credit - while the data waits.
            self.assertEqual(sapp.messages, [Headers('GET /post')])
            self.assertEqual(bytes(sapp.received), b'')
            self.assertEqual(client.mux.streams[sid].out_bytes, 5000)
            self.assertEqual(client.mux.credit.send_available(sid), 0)

            server.driver.enqueue(SendRaw(H2WindowUpdate(sid, 5000)))
            link.pump()
            self.assertTrue(bytes(sapp.received) == body)
            self.assertTrue(sapp.saw_final_input)
        finally:
            link.close()

    def test_stream_overrun_resets_only_that_stream(self) -> None:
        server_factory = AppFactory(lambda o: StreamApp(close_on_final_input=False))
        client, server, link = self._pair(server_factory)
        try:
            ok_app = _request('ok', b'fine')
            bad_app = _request('bad', end=False, close_on_final_input=False)
            client.open(ok_app)
            client.open(bad_app)
            link.pump()

            # A misbehaving client sends past the stream window, bypassing its own credit accounting.
            client.driver.enqueue(SendRaw(H2Data(3, b'x' * (16 * 1024 + 1), False, 0)))
            link.pump()

            self.assertEqual(len(bad_app.errors), 1)
            self.assertIsInstance(bad_app.errors[0], StreamResetMultiplexError)
            self.assertEqual(bad_app.errors[0].reason, 'FLOW_CONTROL_ERROR')  # type: ignore[attr-defined]
            self.assertEqual(bytes(server_factory.apps[1].received), b'fine')
            self.assertEqual(server.mux.streams.stats.reset_local, 1)
            self.assertIs(server.driver.state, IoPipelineDriverState.RUNNING)
        finally:
            link.close()

    def test_connection_overrun_fails_the_connection(self) -> None:
        server_factory = AppFactory(lambda o: StreamApp(close_on_final_input=False))
        client, server, link = self._pair(
            server_factory,
            connection_send_window=1_000_000,
            connection_recv_window=20_000,
            server_adapter=H2LikeAdapter('server', initial_window=1_000_000),
            client_adapter=H2LikeAdapter('client', peer_initial_window=1_000_000),
        )
        try:
            app = _request('x', end=False, close_on_final_input=False)
            client.open(app)
            link.pump()
            (sapp,) = server_factory.apps.values()

            client.driver.enqueue(SendRaw(H2Data(1, b'x' * 30_000, False, 0)))
            link.pump()

            self.assertEqual(len(sapp.errors), 1)
            self.assertIsInstance(sapp.errors[0], ConnectionClosedMultiplexError)
            self.assertIs(server.driver.state, IoPipelineDriverState.CLOSED)
            # The client saw the GOAWAY and then the end of the connection, which truncated its stream.
            self.assertEqual(client.adapter.goaway_received, 1)
            self.assertEqual(len(app.errors), 1)
            self.assertIs(client.driver.state, IoPipelineDriverState.CLOSED)
        finally:
            link.close()

    def test_reset_by_peer_mid_stream(self) -> None:
        server_factory = AppFactory(lambda o: StreamApp(close_on_final_input=False))
        client, server, link = self._pair(server_factory)
        try:
            app = _request('x', end=False, close_on_final_input=False)
            out = client.open(app)
            link.pump()
            self.assertIsInstance(out.result, MultiplexOpenedStream)
            (sid,) = server_factory.apps

            server.driver.enqueue(SendRaw(H2RstStream(sid, 'CANCEL')))
            link.pump()

            self.assertEqual(len(app.errors), 1)
            err = app.errors[0]
            self.assertIsInstance(err, StreamResetMultiplexError)
            self.assertEqual((err.reason, err.by), ('CANCEL', 'remote'))  # type: ignore[attr-defined]
            self.assertIsNone(client.mux.child_pipeline(sid))
            self.assertEqual(len(client.mux.streams), 0)
            self.assertEqual(client.mux.streams.stats.reset_remote, 1)
            self.assertFalse(app.final_output.is_done())
        finally:
            link.close()

    def test_goaway_from_idle_server_closes_and_resets_crossing_stream(self) -> None:
        server_factory = AppFactory(lambda o: _responder(o, size=5_000))
        client, server, link = self._pair(server_factory)
        try:
            first = [_request(i, b'body') for i in range(2)]
            for a in first:
                client.open(a)
            link.pump(until=lambda: len(server_factory.apps) == 2)

            # The server's GOAWAY crosses a new client stream on the wire. With nothing left active, the server finishes
            # at once, so the crossing stream is never processed there - and the client, told the last processed id,
            # resets it as safe to retry.
            crossing = _request('late', b'body')
            client.open(crossing)
            server.driver.enqueue(MultiplexMessages.Shutdown())
            link.pump()

            self.assertEqual(client.adapter.goaway_received, 3)
            self.assertEqual(len(crossing.errors), 1)
            self.assertEqual(crossing.errors[0].reason, 'REFUSED_STREAM')  # type: ignore[attr-defined]

            for i, a in enumerate(first):
                self.assertTrue(bytes(a.received) == payload(('resp', 2 * i + 1), 5_000))
                self.assertTrue(a.final_output.is_succeeded())
            self.assertIs(server.driver.state, IoPipelineDriverState.CLOSED)
            self.assertIs(client.driver.state, IoPipelineDriverState.CLOSED)
        finally:
            link.close()

    def test_goaway_from_busy_server_refuses_new_streams(self) -> None:
        server_factory = AppFactory(lambda o: StreamApp(close_on_final_input=False))
        client, server, link = self._pair(server_factory)
        try:
            busy = _request('busy', end=False, close_on_final_input=False)
            client.open(busy)
            link.pump()

            crossing = _request('late', b'body')
            client.open(crossing)
            server.driver.enqueue(MultiplexMessages.Shutdown())
            link.pump()

            # The server refused the stream it saw after its GOAWAY; the client, having seen the GOAWAY, reset it too.
            self.assertEqual(server.mux.streams.stats.refused_remote, 1)
            self.assertEqual(client.adapter.goaway_received, 1)
            self.assertEqual(len(crossing.errors), 1)
            self.assertEqual(crossing.errors[0].reason, 'REFUSED_STREAM')  # type: ignore[attr-defined]

            # New local opens fail on both sides; the busy stream keeps both connections up.
            late = client.open(StreamApp())
            link.pump()
            self.assertIsInstance(late.exc, ConnectionClosedMultiplexError)
            self.assertIs(server.driver.state, IoPipelineDriverState.RUNNING)
            self.assertEqual(len(server.mux.streams), 1)
        finally:
            link.close()

    def test_stalled_stream_does_not_block_others(self) -> None:
        for mode in ('receive', 'consume'):
            with self.subTest(mode=mode):
                # Stream 1's consumer is in manual-read mode and never asks for input: its window fills and stays full.
                server_factory = AppFactory(lambda o: StreamApp(), auto_read=lambda o: o.key != 1)
                client, server, link = self._pair(
                    server_factory,
                    connection_send_window=48 * 1024,
                    connection_recv_window=48 * 1024,
                    connection_replenish_on=mode,
                )
                try:
                    # The stalled consumer only reads its first batch, then nothing more.
                    stalled = _request('stalled', payload('s', 100_000), end=False)
                    others = [_request(i, payload(i, 50_000)) for i in range(4)]
                    client.open(stalled)
                    for o in others:
                        client.open(o)
                    link.pump()

                    for i, o in enumerate(others):
                        sid = 3 + 2 * i
                        self.assertTrue(bytes(server_factory.apps[sid].received) == payload(i, 50_000))
                        self.assertTrue(o.shutdown_output.is_succeeded())
                    stalled_stream = server.mux.streams[1]
                    self.assertGreater(stalled_stream.in_cost, 0)
                    self.assertLessEqual(stalled_stream.in_cost, 16 * 1024)
                finally:
                    link.close()
