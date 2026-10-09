# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
import typing as ta
import unittest

from ...drivers.pure import PureIoPipelineDriver
from ..types import MultiplexMessages
from ..types import MultiplexOpenedStream
from ..types import StreamRefusedMultiplexError
from .apps import AppFactory
from .apps import StreamApp
from .apps import app_spec
from .apps import payload
from .links import PureLink
from .sshlike import ChannelExtData
from .sshlike import ChannelRequest
from .sshlike import SshLikeAdapter
from .sshlike import SshOpenInfo
from .sshlike import ssh_like_spec


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


class _Peer:
    def __init__(
            self,
            factory: AppFactory,
            *,
            adapter: ta.Optional[SshLikeAdapter] = None,
    ) -> None:
        super().__init__()

        self.factory = factory
        spec, self.mux = ssh_like_spec(factory, adapter=adapter)
        self.adapter: SshLikeAdapter = self.mux.adapter  # type: ignore[assignment]
        self.driver = PureIoPipelineDriver(spec)

    def open(self, app: StreamApp, info: bytes = b'', kind: str = 'session') -> _Outcome:
        msg = MultiplexMessages.OpenStream(app_spec(app), SshOpenInfo(kind, info))
        outcome = _Outcome(msg)
        self.driver.enqueue(msg)
        return outcome


def _pair(
        server_factory: AppFactory,
        client_factory: ta.Optional[AppFactory] = None,
        *,
        capacity: ta.Optional[int] = None,
        server_adapter: ta.Optional[SshLikeAdapter] = None,
        client_adapter: ta.Optional[SshLikeAdapter] = None,
) -> ta.Tuple[_Peer, _Peer, PureLink]:
    if client_factory is None:
        client_factory = AppFactory(lambda o: StreamApp())
    client = _Peer(client_factory, adapter=client_adapter)
    server = _Peer(server_factory, adapter=server_adapter)
    return client, server, PureLink(client.driver, server.driver, capacity=capacity)


class TestSshLikeMultiplexing(unittest.TestCase):
    def test_many_concurrent_request_response_streams(self) -> None:
        n = 24
        requests = {i: payload(('req', i), 20_000 + i * 997) for i in range(n)}

        server_factory = AppFactory(
            lambda o: StreamApp(
                respond=payload(('resp', o.info.info), 50_000),
                manual_read=bool(ta.cast(int, o.key) % 2),
            ),
        )
        client, server, link = _pair(server_factory, capacity=32 * 1024)
        try:
            client_apps = {}
            outcomes = {}
            for i in range(n):
                app = StreamApp(
                    send=requests[i],
                    shutdown_after_send=True,
                    manual_read=bool(i % 3 == 0),
                )
                client_apps[i] = app
                outcomes[i] = client.open(app, info=str(i).encode())

            link.pump()

            for i in range(n):
                with self.subTest(stream=i):
                    oc = outcomes[i]
                    self.assertTrue(oc.done)
                    self.assertIsInstance(oc.result, MultiplexOpenedStream)
                    app = client_apps[i]
                    self.assertTrue(bytes(app.received) == payload(('resp', str(i).encode()), 50_000))
                    self.assertTrue(app.saw_final_input)
                    self.assertTrue(app.shutdown_output.is_succeeded())
                    self.assertTrue(app.final_output.is_succeeded())
                    self.assertEqual(app.errors, [])

            self.assertEqual(len(server_factory.apps), n)
            for sapp in server_factory.apps.values():
                i = int(sapp.metadata.info.info)  # type: ignore[union-attr]
                self.assertTrue(bytes(sapp.received) == requests[i])
                self.assertTrue(sapp.final_output.is_succeeded())
                self.assertEqual(sapp.errors, [])

            # Every channel closed both ways and was released.
            self.assertEqual(len(client.mux.streams), 0)
            self.assertEqual(len(server.mux.streams), 0)
            self.assertEqual(client.mux.streams.stats.closed, n)
            self.assertEqual(server.mux.streams.stats.closed, n)
            self.assertFalse(any(client.mux.credit.has_stream(k) for k in client_apps))
        finally:
            link.close()

    def test_streams_opened_from_both_sides(self) -> None:
        client_factory = AppFactory(lambda o: StreamApp(echo=True, close_on_final_input=False))
        server_factory = AppFactory(lambda o: StreamApp(echo=True, close_on_final_input=False))
        client, server, link = _pair(server_factory, client_factory)
        try:
            c_apps = [StreamApp(send=payload(('c', i), 10_000), shutdown_after_send=True) for i in range(4)]
            s_apps = [StreamApp(send=payload(('s', i), 10_000), shutdown_after_send=True) for i in range(4)]
            for a in c_apps:
                client.open(a)
            for a in s_apps:
                server.open(a)

            link.pump()

            for i, a in enumerate(c_apps):
                self.assertEqual(bytes(a.received), payload(('c', i), 10_000))
            for i, a in enumerate(s_apps):
                self.assertEqual(bytes(a.received), payload(('s', i), 10_000))
            self.assertEqual(len(client_factory.apps), 4)
            self.assertEqual(len(server_factory.apps), 4)
            for a in [*client_factory.apps.values(), *server_factory.apps.values()]:
                self.assertTrue(a.saw_final_input)
        finally:
            link.close()

    def test_refusal_by_factory_and_by_limit(self) -> None:
        server_factory = AppFactory(
            lambda o: StreamApp(),
            refuse=lambda o: 'not allowed' if o.info.kind == 'forbidden' else None,
        )
        client, server, link = _pair(server_factory)
        try:
            server.mux.streams.set_limits(max_remote=1)

            # The limit is checked before the factory is consulted.
            forbidden = client.open(StreamApp(), kind='forbidden')
            ok = client.open(StreamApp(), kind='session')
            over = client.open(StreamApp(), kind='session')
            link.pump()

            self.assertIsInstance(ok.result, MultiplexOpenedStream)
            self.assertIsInstance(forbidden.exc, StreamRefusedMultiplexError)
            self.assertEqual(forbidden.exc.reason, 'not allowed')  # type: ignore[union-attr]
            self.assertIsInstance(over.exc, StreamRefusedMultiplexError)
            self.assertIn('remote', str(over.exc.reason))  # type: ignore[union-attr]

            st = server.mux.streams.stats
            self.assertEqual(st.refused_remote, 2)
            self.assertEqual(st.active_remote, 1)
            self.assertEqual(client.mux.streams.stats.refused_local, 2)
        finally:
            link.close()

    def test_typed_messages_ordered_with_data_and_after_eof(self) -> None:
        # Extended data is flow-controlled and split by credit and packet size; requests ride in order with data; and
        # an exit-status request follows both EOFs, before the close.
        ext = payload('ext', 20_000)
        server_factory = AppFactory(lambda o: StreamApp(
            send=b'out-1',
            send_messages=[ChannelExtData(1, ext), ChannelRequest('progress', payload=b'half')],
            shutdown_after_send=True,
            respond=b'',
            respond_messages=[ChannelRequest('exit-status', payload=b'\x00')],
        ))
        client, server, link = _pair(server_factory)
        try:
            # Like a real client, it waits for exit-status before closing: anything after its own CLOSE is discarded.
            capp = StreamApp(
                send=b'in',
                shutdown_after_send=True,
                close_on_final_input=False,
                close_on=lambda m: isinstance(m, ChannelRequest) and m.name == 'exit-status',
            )
            client.open(capp)
            link.pump()

            (sapp,) = server_factory.apps.values()
            self.assertEqual(bytes(sapp.received), b'in')
            self.assertTrue(capp.saw_final_input)
            self.assertEqual(bytes(capp.received), b'out-1')

            exts = [m for m in capp.messages if isinstance(m, ChannelExtData)]
            self.assertGreater(len(exts), 1)
            self.assertEqual(b''.join(m.data for m in exts), ext)
            self.assertLessEqual(max(len(m.data) for m in exts), 8 * 1024)

            reqs = [m for m in capp.messages if isinstance(m, ChannelRequest)]
            self.assertEqual(reqs, [
                ChannelRequest('progress', payload=b'half'),
                ChannelRequest('exit-status', payload=b'\x00'),
            ])
            # Typed messages keep their place relative to each other and to data.
            self.assertEqual(capp.messages.index(reqs[0]), len(exts))

            for a in (capp, sapp):
                self.assertTrue(a.final_output.is_succeeded())
                self.assertEqual(a.errors, [])
            self.assertEqual(len(client.mux.streams), 0)
            self.assertEqual(len(server.mux.streams), 0)
        finally:
            link.close()

    def test_stalled_channel_does_not_block_others(self) -> None:
        # Per-stream credit only: a consumer that never reads fills its own window and nothing else.
        server_factory = AppFactory(
            lambda o: StreamApp(close_on_final_input=o.info.kind != 'stalled'),
            auto_read=lambda o: o.info.kind != 'stalled',
        )
        client, server, link = _pair(server_factory)
        try:
            stalled = StreamApp(send=payload('s', 200_000))
            others = [StreamApp(send=payload(i, 80_000), shutdown_after_send=True) for i in range(3)]
            client.open(stalled, kind='stalled')
            for o in others:
                client.open(o)
            link.pump()

            for o in others:
                self.assertTrue(o.shutdown_output.is_succeeded())
                self.assertTrue(o.final_output.is_succeeded())
            stalled_server = next(s for s in server.mux.streams if s.info.kind == 'stalled')
            self.assertLessEqual(stalled_server.in_cost, 64 * 1024)
            self.assertGreater(stalled_server.in_cost, 0)
            self.assertEqual(len(server.mux.streams), 1)
        finally:
            link.close()

    def test_full_session_releases_without_cyclic_gc(self) -> None:
        import gc
        import weakref

        def run() -> ta.Sequence[weakref.ReferenceType]:
            refs: ta.List[weakref.ReferenceType] = []

            def make(o: ta.Any) -> ta.Any:
                app = StreamApp(respond=b'pong')
                refs.append(weakref.ref(app))
                return app_spec(app)

            client_spec, client_mux = ssh_like_spec(lambda o: app_spec(StreamApp()))
            server_spec, server_mux = ssh_like_spec(make)
            client = PureIoPipelineDriver(client_spec)
            server = PureIoPipelineDriver(server_spec)
            link = PureLink(client, server)
            capp = StreamApp(send=b'ping', shutdown_after_send=True)
            refs.append(weakref.ref(capp))
            client.enqueue(MultiplexMessages.OpenStream(app_spec(capp), SshOpenInfo('session', b'')))
            del capp
            link.pump()
            self.assertEqual(len(client_mux.streams), 0)
            self.assertEqual(len(server_mux.streams), 0)
            refs.extend([weakref.ref(client), weakref.ref(server), weakref.ref(client_mux), weakref.ref(server_mux)])
            link.close()
            return refs

        was_enabled = gc.isenabled()
        gc.collect()
        gc.disable()
        try:
            refs = run()
            self.assertEqual([r() for r in refs], [None] * len(refs))
        finally:
            if was_enabled:
                gc.enable()
