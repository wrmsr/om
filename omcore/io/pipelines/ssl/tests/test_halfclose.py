# ruff: noqa: SLF001 UP006 UP007 UP033 UP045
# @om-lite
import asyncio
import functools
import hashlib
import socket
import ssl
import time
import typing as ta
import unittest

from .....lite.check import check
from .....secrets import tempssl
from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....fdio.manager import FdioManager
from ....fdio.pollers import SelectFdioPoller
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...drivers.fdio import IoPipelineDriverSocketFdioHandler
from ...drivers.pure import PureIoPipelineDriver
from ...drivers.types import IoPipelineDriverState
from ...errors import SawShutdownOutputIoPipelineError
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ..handlers import SslIoPipelineHandler


##


@functools.lru_cache(maxsize=None)
def _cert() -> tempssl.SslCert:
    from .....subprocesses import sync as _  # import side-effect installing _DEFAULT_SUBPROCESSES  # noqa

    return tempssl.generate_temp_localhost_ssl_cert().cert


def _ssl_handlers(
        *,
        strict_eof: bool = True,
        max_version: ta.Optional[ssl.TLSVersion] = None,
        client_config: ta.Optional[SslIoPipelineHandler.Config] = None,
        server_config: ta.Optional[SslIoPipelineHandler.Config] = None,
) -> ta.Tuple[SslIoPipelineHandler, SslIoPipelineHandler]:
    cert = _cert()
    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_ctx.load_cert_chain(cert.cert_file, cert.key_file)
    client_ctx = ssl.create_default_context(cafile=cert.cert_file)
    if max_version is not None:
        server_ctx.maximum_version = max_version
        client_ctx.maximum_version = max_version

    # Strict EOFs turn a transport EOF which did not follow the peer's close_notify into an error, so a clean
    # FinalInput proves close_notify preceded the transport-level half-close.
    def cfg(c: ta.Optional[SslIoPipelineHandler.Config]) -> SslIoPipelineHandler.Config:
        if c is None:
            c = SslIoPipelineHandler.Config()
        if strict_eof:
            c = SslIoPipelineHandler.Config(**{**c.__dict__, 'suppress_ragged_eofs': False})
        return c

    return (
        SslIoPipelineHandler(
            client_ctx,
            server_side=False,
            server_hostname='localhost',
            config=cfg(client_config),
        ),
        SslIoPipelineHandler(
            server_ctx,
            server_side=True,
            config=cfg(server_config),
        ),
    )


def _payload(seed: bytes, size: int) -> bytes:
    out = bytearray()
    block = hashlib.sha256(seed).digest()
    while len(out) < size:
        out.extend(block)
        block = hashlib.sha256(block).digest()
    return bytes(out[:size])


class _Emit(IoPipelineMessages.AfterFinalInput):
    def __init__(self, *msgs: ta.Any) -> None:
        super().__init__()

        self.msgs = msgs


class _App(IoPipelineHandler):
    """
    A half-closing application endpoint. With `send_on_start` it writes that payload and half-closes as soon as input
    begins; with `respond` it writes that response and half-closes once it has read the peer's whole output. Either
    way it closes with FinalOutput once both directions have ended. In manual-read mode it requests one read at a time.
    """

    def __init__(
            self,
            *,
            send_on_start: ta.Optional[bytes] = None,
            respond: ta.Optional[bytes] = None,
            close_on_final_input: bool = True,
            manual_read: bool = False,
    ) -> None:
        super().__init__()

        self._send_on_start = send_on_start
        self._respond = respond
        self._close_on_final_input = close_on_final_input
        self._manual_read = manual_read

        self.received = bytearray()
        self.errors: ta.List[BaseException] = []
        self.saw_final_input = False
        self.shutdown_output = IoPipelineMessages.ShutdownOutput()
        self.final_output = IoPipelineMessages.FinalOutput()
        self.reads_requested = 0

    def _read(self, ctx: IoPipelineHandlerContext) -> None:
        if self._manual_read and not self.saw_final_input:
            self.reads_requested += 1
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

    def _send(self, ctx: IoPipelineHandlerContext, data: bytes) -> None:
        mv = memoryview(data)
        for pos in range(0, len(mv), 16 * 1024):
            ctx.feed_out(mv[pos:pos + 16 * 1024])
        ctx.feed_out(self.shutdown_output)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Emit):
            for out_msg in msg.msgs:
                ctx.feed_out(out_msg)
            return

        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            if self._send_on_start is not None:
                self._send(ctx, self._send_on_start)
            self._read(ctx)
            return

        if ByteStreamBuffers.can_bytes(msg):
            for seg in ByteStreamBuffers.iter_segments(msg):
                self.received.extend(seg)
            return

        if isinstance(msg, IoPipelineFlowMessages.FlushInput):
            self._read(ctx)
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True
            ctx.feed_in(msg)
            if self._respond is not None:
                self._send(ctx, self._respond)
            if self._close_on_final_input:
                ctx.feed_out(self.final_output)
            return

        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            return

        if isinstance(msg, (IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput)):
            return

        ctx.feed_in(msg)


class _OutboundRecorder(IoPipelineHandler):
    """Placed between TLS and the transport, records the kinds of outbound messages in order."""

    def __init__(self) -> None:
        super().__init__()

        self.kinds: ta.List[str] = []

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if ByteStreamBuffers.can_bytes(msg):
            if not self.kinds or self.kinds[-1] != 'bytes':
                self.kinds.append('bytes')
        else:
            self.kinds.append(type(msg).__name__)
        ctx.feed_out(msg)


##


class _PureLink:
    """Steps two pure drivers back to back, moving bytes and delivering EOF on output shutdown or close."""

    def __init__(self, a: PureIoPipelineDriver, b: PureIoPipelineDriver) -> None:
        super().__init__()

        self.a = a
        self.b = b
        self._eof_sent: ta.Set[int] = set()

    def _move(self, src: PureIoPipelineDriver, dst: PureIoPipelineDriver) -> bool:
        moved = False
        if src.state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING) and src.has_pending_output:
            data = src.drain_output()
            if data and dst.is_running:
                dst.feed_input(data)
            moved = True
        src_ended = src.output_shutdown or src.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)
        if src_ended and id(src) not in self._eof_sent:
            self._eof_sent.add(id(src))
            if dst.is_running:
                dst.feed_eof()
            moved = True
        return moved

    def pump(self, max_rounds: int = 10_000) -> None:
        for d in (self.a, self.b):
            if d.state is IoPipelineDriverState.NEW:
                assert d.next(read=False) is None

        for _ in range(max_rounds):
            progressed = False
            for d in (self.a, self.b):
                if d.is_running:
                    assert d.next(read=True, raise_on_stall=False) is None
            progressed |= self._move(self.a, self.b)
            progressed |= self._move(self.b, self.a)
            if not progressed:
                return

        raise RuntimeError('link did not quiesce')


def _pure(*handlers: IoPipelineHandler, manual_read: bool = False) -> PureIoPipelineDriver:
    return PureIoPipelineDriver(IoPipeline.Spec(
        list(handlers),
        services=[StubIoPipelineFlowService(auto_read=not manual_read)],
    ))


##


class TestSslHalfCloseOverPureLink(unittest.TestCase):
    def _request_response(self, *, max_version: ta.Optional[ssl.TLSVersion] = None, manual_read: bool = False) -> None:
        request = _payload(b'request', 100_000)
        response = _payload(b'response', 300_000)

        client_ssl, server_ssl = _ssl_handlers(max_version=max_version)
        client_app = _App(send_on_start=request, manual_read=manual_read)
        server_app = _App(respond=response, manual_read=manual_read)
        client = _pure(client_ssl, client_app, manual_read=manual_read)
        server = _pure(server_ssl, server_app, manual_read=manual_read)
        try:
            _PureLink(client, server).pump()

            self.assertEqual(client_app.errors, [])
            self.assertEqual(server_app.errors, [])
            self.assertTrue(bytes(server_app.received) == request)
            self.assertTrue(bytes(client_app.received) == response)

            for app in (client_app, server_app):
                self.assertTrue(app.saw_final_input)
                self.assertTrue(app.shutdown_output.is_succeeded())
                self.assertTrue(app.final_output.is_succeeded())
                if manual_read:
                    self.assertGreater(app.reads_requested, 1)

            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
            self.assertIs(server.state, IoPipelineDriverState.CLOSED)
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.CLOSED)
            self.assertIs(server_ssl.state, SslIoPipelineHandler.State.CLOSED)

        finally:
            client.close()
            server.close()

    def test_request_half_close_then_response(self) -> None:
        self._request_response()

    def test_request_half_close_then_response_tls12(self) -> None:
        self._request_response(max_version=ssl.TLSVersion.TLSv1_2)

    def test_request_half_close_then_response_manual_read(self) -> None:
        self._request_response(manual_read=True)

    def test_simultaneous_half_close_with_large_payloads(self) -> None:
        a_payload = _payload(b'a', 1_000_000)
        b_payload = _payload(b'b', 1_000_000)

        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(send_on_start=a_payload, manual_read=True)
        server_app = _App(send_on_start=b_payload, manual_read=True)
        client = _pure(client_ssl, client_app, manual_read=True)
        server = _pure(server_ssl, server_app, manual_read=True)
        try:
            _PureLink(client, server).pump()

            self.assertEqual(client_app.errors, [])
            self.assertEqual(server_app.errors, [])
            self.assertTrue(bytes(server_app.received) == a_payload)
            self.assertTrue(bytes(client_app.received) == b_payload)
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
            self.assertIs(server.state, IoPipelineDriverState.CLOSED)

        finally:
            client.close()
            server.close()

    def test_close_notify_precedes_shutdown_and_later_flushes_follow_it(self) -> None:
        client_ssl, server_ssl = _ssl_handlers()
        recorder = _OutboundRecorder()
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(recorder, client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.ESTABLISHED)
            recorder.kinds.clear()

            shutdown_output = IoPipelineMessages.ShutdownOutput()
            flush_before = IoPipelineFlowMessages.FlushOutput()
            flush_after = IoPipelineFlowMessages.FlushOutput()
            client.enqueue(_Emit(b'data', flush_before, shutdown_output, flush_after))
            link.pump()

            # The data and its flush; then the close_notify record with the handler's own progress flush for it; then
            # the ShutdownOutput, and only after it the flush which followed it.
            self.assertEqual(
                recorder.kinds,
                ['bytes', 'FlushOutput', 'bytes', 'FlushOutput', 'ShutdownOutput', 'FlushOutput'],
            )
            self.assertTrue(shutdown_output.is_succeeded())
            self.assertTrue(flush_before.is_succeeded())
            self.assertTrue(flush_after.is_succeeded())
            self.assertEqual(bytes(server_app.received), b'data')
            self.assertTrue(server_app.saw_final_input)
            self.assertEqual(server_app.errors, [])
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.SHUTTING_DOWN)
            self.assertTrue(client.output_shutdown)

            # The client keeps reading after its half-close.
            server.enqueue(_Emit(b'reply'))
            link.pump()
            self.assertEqual(bytes(client_app.received), b'reply')

        finally:
            client.close()
            server.close()

    def test_half_close_during_handshake_waits_for_it(self) -> None:
        client_ssl, server_ssl = _ssl_handlers(
            client_config=SslIoPipelineHandler.Config(handshake_on_initial_input=False),
        )
        client_app = _App(send_on_start=b'early request')
        server_app = _App(respond=b'late response')
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        try:
            self.assertIsNone(client.next(read=False))
            # The request and half-close were accepted before any handshake record existed.
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.HANDSHAKE)
            self.assertFalse(client_app.shutdown_output.is_done())

            _PureLink(client, server).pump()

            self.assertEqual(bytes(server_app.received), b'early request')
            self.assertEqual(bytes(client_app.received), b'late response')
            self.assertTrue(client_app.shutdown_output.is_succeeded())
            self.assertEqual(client_app.errors, [])
            self.assertEqual(server_app.errors, [])

        finally:
            client.close()
            server.close()

    def test_write_after_half_close_is_rejected(self) -> None:
        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()
            client.enqueue(_Emit(IoPipelineMessages.ShutdownOutput()))
            client.enqueue(_Emit(b'too late'))
            link.pump()

            self.assertEqual(len(client_app.errors), 1)
            self.assertIsInstance(client_app.errors[0], SawShutdownOutputIoPipelineError)
            self.assertEqual(bytes(server_app.received), b'')
            self.assertTrue(server_app.saw_final_input)

        finally:
            client.close()
            server.close()

    def test_duplicate_half_close_is_rejected_without_preempting_the_first(self) -> None:
        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()

            first = IoPipelineMessages.ShutdownOutput()
            second = IoPipelineMessages.ShutdownOutput()
            failures: ta.List[ta.Optional[BaseException]] = []
            second.add_listener(lambda m: failures.append(m.get_exception()))
            client.enqueue(_Emit(b'payload', first, second))
            link.pump()

            # The duplicate is held behind the first and then rejected by the pipeline terminal, as without TLS.
            self.assertTrue(first.is_succeeded())
            self.assertTrue(second.is_failed())
            self.assertEqual(len(failures), 1)
            self.assertIsInstance(failures[0], SawShutdownOutputIoPipelineError)
            self.assertEqual(len(client_app.errors), 1)
            self.assertIsInstance(client_app.errors[0], SawShutdownOutputIoPipelineError)
            self.assertEqual(bytes(server_app.received), b'payload')
            self.assertTrue(server_app.saw_final_input)
            self.assertEqual(server_app.errors, [])

        finally:
            client.close()
            server.close()

    def test_final_output_after_half_close_waits_for_peer_close_notify(self) -> None:
        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()

            final_output = IoPipelineMessages.FinalOutput()
            client.enqueue(_Emit(b'request', IoPipelineMessages.ShutdownOutput(), final_output))
            link.pump()

            # The close is retained until the peer finishes: reads continue meanwhile.
            self.assertFalse(final_output.is_done())
            self.assertIs(client.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(server_app.saw_final_input)

            server.enqueue(_Emit(b'response', IoPipelineMessages.ShutdownOutput()))
            link.pump()

            self.assertEqual(bytes(client_app.received), b'response')
            self.assertTrue(client_app.saw_final_input)
            self.assertTrue(final_output.is_succeeded())
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
            self.assertEqual(client_app.errors, [])

        finally:
            client.close()
            server.close()

    def test_shutdown_timeout_runs_only_after_final_output(self) -> None:
        client_ssl, server_ssl = _ssl_handlers(client_config=SslIoPipelineHandler.Config(shutdown_timeout_s=5.))
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()

            client.enqueue(_Emit(IoPipelineMessages.ShutdownOutput()))
            link.pump()
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.SHUTTING_DOWN)
            self.assertIsNone(client_ssl._shutdown_timeout_handle)
            self.assertIsNone(client.next_deadline())

            final_output = IoPipelineMessages.FinalOutput()
            client.enqueue(_Emit(final_output))
            link.pump()
            self.assertIsNotNone(client_ssl._shutdown_timeout_handle)
            self.assertEqual(client.next_deadline(), 5.)
            self.assertFalse(final_output.is_done())

            client.advance_time(5.)
            link.pump()
            self.assertEqual(len(client_app.errors), 1)
            self.assertIn('TLS shutdown timed out', str(client_app.errors[0]))
            self.assertTrue(final_output.is_succeeded())
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)

        finally:
            client.close()
            server.close()

    def test_half_close_preserves_unread_input_and_peer_close_notify(self) -> None:
        # Sending close_notify must not discard application data already received but not yet read - in manual-read
        # mode that is the normal state of affairs - nor the peer's close_notify queued behind it.
        data = _payload(b'unread', 200_000)
        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app, manual_read=True)
        link = _PureLink(client, server)
        try:
            server.enqueue(_Emit(IoPipelineFlowMessages.ReadyForInput()))
            link.pump()
            self.assertIs(server_ssl.state, SslIoPipelineHandler.State.ESTABLISHED)

            client.enqueue(_Emit(data, IoPipelineMessages.ShutdownOutput()))
            link.pump()
            server.enqueue(_Emit(IoPipelineFlowMessages.ReadyForInput()))
            link.pump()

            # One read delivered one record's worth; the rest, and the client's close_notify, are still buffered.
            self.assertLess(len(server_app.received), len(data))
            self.assertGreater(check.not_none(server_ssl.inbound_buffered_bytes()), 0)
            self.assertFalse(server_app.saw_final_input)

            server.enqueue(_Emit(IoPipelineMessages.ShutdownOutput()))
            link.pump()
            self.assertTrue(client_app.saw_final_input)
            self.assertIs(server_ssl.state, SslIoPipelineHandler.State.SHUTTING_DOWN)

            for _ in range(1000):
                if server_app.saw_final_input:
                    break
                server.enqueue(_Emit(IoPipelineFlowMessages.ReadyForInput()))
                link.pump()

            self.assertTrue(bytes(server_app.received) == data)
            self.assertTrue(server_app.saw_final_input)
            self.assertEqual(server_app.errors, [])
            self.assertEqual(client_app.errors, [])

        finally:
            client.close()
            server.close()

    def test_half_closed_manual_reader_reads_only_on_request(self) -> None:
        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(close_on_final_input=False, manual_read=True)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app, manual_read=True)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()
            client.enqueue(_Emit(IoPipelineMessages.ShutdownOutput()))
            link.pump()
            self.assertTrue(server_app.saw_final_input)

            # The app's outstanding read is satisfied by the reply; no further read is made on its behalf.
            requested = client_app.reads_requested
            server.enqueue(_Emit(b'one'))
            link.pump()
            self.assertEqual(bytes(client_app.received), b'one')
            self.assertGreaterEqual(client_app.reads_requested, requested)

        finally:
            client.close()
            server.close()


##


class _FdioPair:
    def __init__(self, client_spec: IoPipeline.Spec, server_spec: IoPipeline.Spec) -> None:
        super().__init__()

        self.client_sock, self.server_sock = socket.socketpair()
        self.poller = SelectFdioPoller()
        self.client = IoPipelineDriverSocketFdioHandler(self.client_sock, ('client', 0), client_spec)
        self.server = IoPipelineDriverSocketFdioHandler(self.server_sock, ('server', 0), server_spec)
        self.manager = FdioManager(self.poller)

    def run(self, timeout_s: float = 30.) -> None:
        for drv in (self.client, self.server):
            assert drv.next(read=False) is None
            self.manager.register(drv)

        deadline = time.monotonic() + timeout_s
        while self.client.is_active or self.server.is_active:
            if time.monotonic() > deadline:
                raise TimeoutError('fdio pair did not finish')
            self.manager.poll(timeout=1.)

    def close(self) -> None:
        self.client.close()
        self.server.close()
        self.poller.close()


class TestSslHalfCloseOverRealSockets(unittest.TestCase):
    def test_fdio_request_half_close_then_response(self) -> None:
        request = _payload(b'request', 200_000)
        response = _payload(b'response', 2_000_000)

        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(send_on_start=request, manual_read=True)
        server_app = _App(respond=response, manual_read=True)
        pair = _FdioPair(
            IoPipeline.Spec([client_ssl, client_app], services=[StubIoPipelineFlowService(auto_read=False)]),
            IoPipeline.Spec([server_ssl, server_app], services=[StubIoPipelineFlowService(auto_read=False)]),
        )
        try:
            pair.run()

            self.assertEqual(client_app.errors, [])
            self.assertEqual(server_app.errors, [])
            self.assertTrue(bytes(server_app.received) == request)
            self.assertTrue(bytes(client_app.received) == response)
            for app in (client_app, server_app):
                self.assertTrue(app.shutdown_output.is_succeeded())
                self.assertTrue(app.final_output.is_succeeded())
            self.assertTrue(pair.client.output_shutdown)
            self.assertTrue(pair.server.output_shutdown)
            self.assertIs(pair.client.state, IoPipelineDriverState.CLOSED)
            self.assertIs(pair.server.state, IoPipelineDriverState.CLOSED)

        finally:
            pair.close()

    def test_fdio_simultaneous_half_close(self) -> None:
        a_payload = _payload(b'a', 3_000_000)
        b_payload = _payload(b'b', 3_000_000)

        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(send_on_start=a_payload)
        server_app = _App(send_on_start=b_payload)
        pair = _FdioPair(
            IoPipeline.Spec([client_ssl, client_app], services=[StubIoPipelineFlowService()]),
            IoPipeline.Spec([server_ssl, server_app], services=[StubIoPipelineFlowService()]),
        )
        try:
            pair.run()

            self.assertEqual(client_app.errors, [])
            self.assertEqual(server_app.errors, [])
            self.assertTrue(bytes(server_app.received) == a_payload)
            self.assertTrue(bytes(client_app.received) == b_payload)
            self.assertIs(pair.client.state, IoPipelineDriverState.CLOSED)
            self.assertIs(pair.server.state, IoPipelineDriverState.CLOSED)

        finally:
            pair.close()

    def test_plain_peer_observes_close_notify_then_tcp_eof_and_can_still_send(self) -> None:
        # A raw ssl.SSLObject peer over a real socket, independent of the pipeline's TLS handler.
        client_ssl, _ = _ssl_handlers()
        client_app = _App(send_on_start=b'hello', close_on_final_input=True)
        sock, peer = socket.socketpair()
        peer.settimeout(5.)
        poller = SelectFdioPoller()
        driver = IoPipelineDriverSocketFdioHandler(
            sock,
            ('client', 0),
            IoPipeline.Spec([client_ssl, client_app], services=[StubIoPipelineFlowService()]),
        )
        manager = FdioManager(poller)

        cert = _cert()
        server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_ctx.load_cert_chain(cert.cert_file, cert.key_file)
        in_bio, out_bio = ssl.MemoryBIO(), ssl.MemoryBIO()
        server = server_ctx.wrap_bio(in_bio, out_bio, server_side=True)

        def exchange() -> bool:
            manager.poll(timeout=.05)
            while out_bio.pending:
                peer.sendall(out_bio.read())
            peer.setblocking(False)
            try:
                data = peer.recv(65536)
            except BlockingIOError:
                return False
            finally:
                peer.settimeout(5.)
            if not data:
                in_bio.write_eof()
                return True
            in_bio.write(data)
            return False

        try:
            self.assertIsNone(driver.next(read=False))
            manager.register(driver)

            received = bytearray()
            saw_close_notify = False
            saw_tcp_eof = False
            for _ in range(200):
                tcp_eof = exchange()
                if not saw_close_notify:
                    try:
                        server.do_handshake()
                        while True:
                            chunk = server.read(65536)
                            if not chunk:
                                saw_close_notify = True
                                break
                            received.extend(chunk)
                    except (ssl.SSLWantReadError, ssl.SSLZeroReturnError) as e:
                        if isinstance(e, ssl.SSLZeroReturnError):
                            saw_close_notify = True
                if tcp_eof:
                    # The transport EOF must come after the close_notify record.
                    self.assertTrue(saw_close_notify)
                    saw_tcp_eof = True
                    break

            self.assertTrue(saw_tcp_eof)
            self.assertEqual(bytes(received), b'hello')
            self.assertTrue(client_app.shutdown_output.is_succeeded())

            # The half-closed client still receives what the server sends, then closes on the server's close_notify.
            server.write(b'world')
            try:
                server.unwrap()
            except ssl.SSLWantReadError:
                pass
            peer.sendall(out_bio.read())
            peer.shutdown(socket.SHUT_WR)

            deadline = time.monotonic() + 10.
            while driver.is_active and time.monotonic() < deadline:
                manager.poll(timeout=.1)

            self.assertEqual(bytes(client_app.received), b'world')
            self.assertTrue(client_app.saw_final_input)
            self.assertTrue(client_app.final_output.is_succeeded())
            self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
            self.assertEqual(client_app.errors, [])

        finally:
            driver.close()
            peer.close()
            poller.close()


class TestSslHalfCloseOverAsyncioTcp(AsyncioIsolatedAsyncTestCase):
    async def test_request_half_close_then_response(self) -> None:
        request = _payload(b'request', 300_000)
        response = _payload(b'response', 3_000_000)

        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(send_on_start=request, manual_read=True)
        server_app = _App(respond=response, manual_read=True)
        server_done: asyncio.Future = asyncio.get_running_loop().create_future()

        async def on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            drv = PollAsyncioStreamIoPipelineDriver(
                IoPipeline.Spec([server_ssl, server_app], services=[StubIoPipelineFlowService(auto_read=False)]),
                reader,
                writer,
            )
            try:
                await drv.loop_until_done()
            except BaseException as e:  # noqa
                server_done.set_exception(e)
            else:
                server_done.set_result(drv)
            finally:
                await drv.close()

        server = await asyncio.start_server(on_connect, '127.0.0.1', 0)
        try:
            port = server.sockets[0].getsockname()[1]
            reader, writer = await asyncio.open_connection('127.0.0.1', port)
            client = PollAsyncioStreamIoPipelineDriver(
                IoPipeline.Spec([client_ssl, client_app], services=[StubIoPipelineFlowService(auto_read=False)]),
                reader,
                writer,
            )
            try:
                await asyncio.wait_for(asyncio.gather(client.loop_until_done(), server_done), 30.)
            finally:
                await client.close()

            server_drv = server_done.result()
            self.assertEqual(client_app.errors, [])
            self.assertEqual(server_app.errors, [])
            self.assertTrue(bytes(server_app.received) == request)
            self.assertTrue(bytes(client_app.received) == response)
            for app in (client_app, server_app):
                self.assertTrue(app.shutdown_output.is_succeeded())
                self.assertTrue(app.final_output.is_succeeded())
            self.assertTrue(client.output_shutdown)
            self.assertTrue(server_drv.output_shutdown)
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
            self.assertIs(server_drv.state, IoPipelineDriverState.CLOSED)

        finally:
            server.close()
            await server.wait_closed()
