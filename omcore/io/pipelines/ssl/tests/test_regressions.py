# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
"""
Regression tests for defects found reviewing the TLS half-close work. The ids in the comments are those of the review
findings recorded in FINDINGS.md at commit 323de87b3; each comment describes the defect as it was found.
"""
import ssl
import typing as ta
import unittest

from .....lite.check import check
from ...bytes.buffers import OutboundBytesBufferIoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...drivers.types import IoPipelineDriverState
from ...errors import SawShutdownOutputIoPipelineError
from ...errors import TimeoutIoPipelineError
from ...flow.types import IoPipelineFlowMessages
from ..handlers import SslIoPipelineHandler
from .test_halfclose import _App
from .test_halfclose import _cert
from .test_halfclose import _Emit
from .test_halfclose import _payload
from .test_halfclose import _pure
from .test_halfclose import _PureLink
from .test_halfclose import _ssl_handlers


##


class _WritabilityApp(_App):
    """Records each writability transition together with whether output shutdown had reached the terminal."""

    def __init__(self) -> None:
        super().__init__(close_on_final_input=False)

        self.writability: ta.List[ta.Tuple[type, bool]] = []

    def inbound(self, ctx, msg):
        if isinstance(msg, (IoPipelineFlowMessages.ReadyForOutput, IoPipelineFlowMessages.PauseOutput)):
            self.writability.append((type(msg), ctx.pipeline.saw_shutdown_output))
        super().inbound(ctx, msg)


class TestFencesAfterFailedHandshake(unittest.TestCase):
    # O24 (reviewer 2's TLS-01). A client which does not trust the server's certificate queues plaintext, a flush and
    # a shutdown before the handshake. Verification fails and the application is told; when its error policy then
    # closes, both earlier fences report success, although TLS never established and the plaintext was discarded.

    def test_failed_certificate_verification_fails_undelivered_output_fences(self) -> None:
        # The server uses the real temporary self-signed certificate; this client deliberately does not trust it.
        _, server_ssl = _ssl_handlers()
        client_ssl = SslIoPipelineHandler(
            ssl.create_default_context(),
            server_side=False,
            server_hostname='localhost',
        )
        app = _App(close_on_final_input=False)
        client = _pure(client_ssl, app)
        server = _pure(server_ssl, _App(close_on_final_input=False))
        link = _PureLink(client, server)
        flush = IoPipelineFlowMessages.FlushOutput()
        shutdown = IoPipelineMessages.ShutdownOutput()
        try:
            client.enqueue(_Emit(b'undelivered plaintext', flush, shutdown))
            link.pump()
            self.assertTrue(any(isinstance(exc, ssl.SSLCertVerificationError) for exc in app.errors))

            # Application error policy closes after seeing the verification failure.
            client.enqueue(_Emit(IoPipelineMessages.FinalOutput()))
            link.pump()
            for name, fence in (('flush', flush), ('shutdown', shutdown)):
                with self.subTest(fence=name):
                    self.assertTrue(fence.is_failed(), 'TLS never established, but its output fence succeeded')
        finally:
            client.close()
            server.close()

    # O25 (reviewer 2's TLS-02, and TODO.md's "fail TLS's pending ShutdownOutput and flushes when a failed or EOF'd
    # handshake drops queued plaintext"). With no peer, the handshake deadline discards the plaintext; the flush fails
    # but the shutdown succeeds, although it promises the preceding output crossed the transport.

    def test_handshake_timeout_does_not_report_undelivered_output_as_shutdown_success(self) -> None:
        client_ssl, _ = _ssl_handlers(client_config=SslIoPipelineHandler.Config(handshake_timeout_s=1.))
        app = _App(close_on_final_input=False)
        driver = _pure(client_ssl, app)
        flush = IoPipelineFlowMessages.FlushOutput()
        shutdown = IoPipelineMessages.ShutdownOutput()
        final = IoPipelineMessages.FinalOutput()
        try:
            driver.enqueue(_Emit(b'plaintext never sent to the peer', flush, shutdown, final))
            self.assertIsNone(driver.next(read=False))
            driver.drain_output()  # Only the ClientHello can cross the transport without a peer handshake.
            self.assertFalse(shutdown.is_done())

            driver.advance_time(1.)
            self.assertIsNone(driver.next(read=False))
            driver.drain_output()
            self.assertTrue(app.errors)
            self.assertTrue(flush.is_failed())
            self.assertTrue(shutdown.is_failed(), 'the plaintext was discarded, but ShutdownOutput succeeded')
        finally:
            driver.close()


class TestWritabilityAfterShutdown(unittest.TestCase):
    # O26 (reviewer 2's TLS-03, and TODO.md's "stop announcing ReadyForOutput after ShutdownOutput in the TLS
    # handler"). Plaintext and a shutdown queued before the handshake pause the application; once the handshake lets
    # them through, the handler announces ReadyForOutput although the shutdown has reached the terminal.

    def test_handshake_does_not_resume_output_after_retained_shutdown(self) -> None:
        client_ssl, server_ssl = _ssl_handlers(client_config=SslIoPipelineHandler.Config(
            write_high_watermark=4,
            write_low_watermark=2,
        ))
        app = _WritabilityApp()
        client = _pure(client_ssl, app)
        server = _pure(server_ssl, _App(close_on_final_input=False))
        link = _PureLink(client, server)
        try:
            client.enqueue(_Emit(b'hello', app.shutdown_output))
            client.next(read=False)
            self.assertIn((IoPipelineFlowMessages.PauseOutput, False), app.writability)
            link.pump()
            self.assertTrue(app.shutdown_output.is_succeeded())
            self.assertNotIn((IoPipelineFlowMessages.ReadyForOutput, True), app.writability)
        finally:
            client.close()
            server.close()


class TestStrictEofOnDefaultContexts(unittest.TestCase):
    # O7 (reviewer 2's TLS-04). Passes on Python 3.10+. On 3.8 the default SSL contexts carry
    # OP_IGNORE_UNEXPECTED_EOF, so the engine reports a truncated stream as a clean EOF and the handler's strict mode
    # cannot see it.

    def test_strict_eof_detects_truncation_with_default_ssl_contexts(self) -> None:
        client_ssl, server_ssl = _ssl_handlers(strict_eof=True)
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()
            server.enqueue(_Emit(b'partial response'))
            link.pump()
            self.assertEqual(bytes(client_app.received), b'partial response')

            server.close()  # Transport EOF without a TLS close_notify.
            link.pump()
            self.assertTrue(any(isinstance(exc, ssl.SSLError) for exc in client_app.errors))
            self.assertFalse(client_app.saw_final_input, 'truncation was exposed as a clean EOF')
        finally:
            client.close()
            server.close()


class TestAbortReleasesPlaintext(unittest.TestCase):
    # O27 (reviewer 2's TLS-05). Plaintext queued ahead of a handshake which never completes stays owned by the
    # handler after the driver aborts: its Removed notification cancels timers but does not release the queue.

    def test_abort_releases_plaintext_waiting_for_handshake(self) -> None:
        client_ssl, _ = _ssl_handlers()
        app = _App(close_on_final_input=False)
        driver = _pure(client_ssl, app)
        try:
            driver.enqueue(_Emit(b'pending' * 100_000))
            self.assertIsNone(driver.next(read=False))
            buffered = client_ssl.outbound_buffered_bytes()
            assert buffered is not None
            self.assertGreater(buffered, 0)
            driver.close()
            self.assertEqual(client_ssl.outbound_buffered_bytes(), 0)
        finally:
            driver.close()


class _CloseOnErrorApp(_App):
    """Synchronously feeds FinalOutput when an inbound Error arrives."""

    def __init__(self) -> None:
        super().__init__(close_on_final_input=False)

        self.error_final_output = IoPipelineMessages.FinalOutput()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            ctx.feed_out(self.error_final_output)
            return
        super().inbound(ctx, msg)


class _DestroyOrRemoveOnErrorApp(_App):
    """Synchronously destroys the pipeline or removes the SSL handler when an inbound Error arrives."""

    def __init__(self, *, action: str) -> None:
        super().__init__(close_on_final_input=False)

        self._action = action

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            if self._action == 'destroy':
                ctx.pipeline.destroy()
            elif self._action == 'remove':
                ssl_ref = check.not_none(msg.handler)
                ctx.pipeline.remove(ssl_ref)
            else:
                raise ValueError(self._action)
            return
        super().inbound(ctx, msg)


class _PartialWriteSslObject:
    """Thin wrapper around a real SSLObject exposing OpenSSL partial-write short return counts."""

    def __init__(self, obj: ssl.SSLObject, max_write: int) -> None:
        super().__init__()

        self._obj = obj
        self._max_write = max_write
        self.partial_writes = 0

    def write(self, data: ta.Any) -> int:
        mv = memoryview(data)
        if mv.nbytes > self._max_write:
            self.partial_writes += 1
            return self._obj.write(mv[:self._max_write])
        return self._obj.write(mv)

    def __getattr__(self, name: str) -> ta.Any:
        return getattr(self._obj, name)


class _WantReadThenErrorWriteSslObject:
    """
    Wraps a real SSLObject so writes raise SSLWantReadError until a real read() decrypts application data in the same
    _pump() call, after which the next write retry in iteration 2 raises a real SSLError.
    """

    def __init__(self, obj: ssl.SSLObject, exc: ssl.SSLError) -> None:
        super().__init__()

        self._obj = obj
        self._exc = exc
        self._saw_read = False

    def read(self, size: int) -> bytes:
        data = self._obj.read(size)
        if data:
            self._saw_read = True
        return data

    def write(self, data: ta.Any) -> int:
        if not self._saw_read:
            raise ssl.SSLWantReadError
        raise self._exc

    def __getattr__(self, name: str) -> ta.Any:
        return getattr(self._obj, name)


class TestStateTimeoutReentrancyAndTeardown(unittest.TestCase):
    # When a handshake timeout fires, _on_state_timeout previously cleared _write_q and emitted Error before calling
    # _abandon_output(exc). An application error handler that synchronously feeds FinalOutput triggers a reentrant
    # _turn() / _emit() which saw _write_q empty and _state == CLOSED, forwarding the discarded FlushOutput and
    # ShutdownOutput fences downstream to succeed instead of failing them.

    def test_handshake_timeout_reentrant_final_output_still_fails_fences(self) -> None:
        client_ssl, _ = _ssl_handlers(client_config=SslIoPipelineHandler.Config(handshake_timeout_s=1.))
        app = _CloseOnErrorApp()
        driver = _pure(client_ssl, app)
        flush = IoPipelineFlowMessages.FlushOutput()
        shutdown = IoPipelineMessages.ShutdownOutput()
        try:
            driver.enqueue(_Emit(b'undelivered plaintext', flush, shutdown))
            self.assertIsNone(driver.next(read=False))
            driver.drain_output()
            self.assertFalse(flush.is_done())
            self.assertFalse(shutdown.is_done())

            driver.advance_time(1.)
            self.assertIsNone(driver.next(read=False))
            driver.drain_output()

            self.assertEqual(len(app.errors), 1)
            self.assertIsInstance(app.errors[0], TimeoutIoPipelineError)
            self.assertTrue(flush.is_failed(), 'FlushOutput for discarded handshake plaintext succeeded')
            self.assertTrue(shutdown.is_failed(), 'ShutdownOutput for failed handshake succeeded')
            self.assertTrue(app.error_final_output.is_succeeded())
            self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
        finally:
            driver.close()

    # When a handshake or shutdown timeout delivers Error, an application error handler may synchronously destroy the
    # pipeline or remove the SSL handler. Previously _on_state_timeout's finally block unconditionally called
    # _send_shutdown_output / _send_final_output on the invalidated context, raising ContextInvalidatedIoPipelineError.

    def test_handshake_timeout_destroy_or_remove_in_error_handler_does_not_crash(self) -> None:
        for action in ('destroy', 'remove'):
            with self.subTest(action=action):
                client_ssl, _ = _ssl_handlers(client_config=SslIoPipelineHandler.Config(handshake_timeout_s=1.))
                app = _DestroyOrRemoveOnErrorApp(action=action)
                driver = _pure(client_ssl, app)
                try:
                    driver.enqueue(_Emit(b'pending', IoPipelineFlowMessages.FlushOutput()))
                    self.assertIsNone(driver.next(read=False))
                    driver.drain_output()

                    driver.advance_time(1.)
                    self.assertIsNone(driver.next(read=False))
                    self.assertEqual(len(app.errors), 1)
                    self.assertIsInstance(app.errors[0], TimeoutIoPipelineError)
                    self.assertIs(client_ssl.state, SslIoPipelineHandler.State.CLOSED)
                finally:
                    driver.close()

    def test_shutdown_timeout_destroy_or_remove_in_error_handler_does_not_crash(self) -> None:
        for action in ('destroy', 'remove'):
            with self.subTest(action=action):
                client_ssl, server_ssl = _ssl_handlers(
                    client_config=SslIoPipelineHandler.Config(shutdown_timeout_s=1.),
                )
                client_app = _DestroyOrRemoveOnErrorApp(action=action)
                server_app = _App(close_on_final_input=False)
                client = _pure(client_ssl, client_app)
                server = _pure(server_ssl, server_app)
                link = _PureLink(client, server)
                try:
                    link.pump()
                    self.assertIs(client_ssl.state, SslIoPipelineHandler.State.ESTABLISHED)

                    client.enqueue(_Emit(IoPipelineMessages.FinalOutput()))
                    link.pump()
                    self.assertIs(client_ssl.state, SslIoPipelineHandler.State.SHUTTING_DOWN)

                    client.advance_time(1.)
                    self.assertIsNone(client.next(read=False))
                    self.assertEqual(len(client_app.errors), 1)
                    self.assertIsInstance(client_app.errors[0], TimeoutIoPipelineError)
                    self.assertIs(client_ssl.state, SslIoPipelineHandler.State.CLOSED)
                finally:
                    client.close()
                    server.close()


class TestPumpSslErrorCleanup(unittest.TestCase):
    # When _pump() raises ssl.SSLError during handshake or writes, _turn() previously transitioned to CLOSED and
    # abandoned output fences without releasing an already-retained _pending_final_output. Because _close_requested
    # remained True, even a subsequent FinalOutput from the app's error policy was swallowed as a duplicate, permanently
    # wedging the close.

    def test_handshake_failure_releases_already_queued_final_output(self) -> None:
        _, server_ssl = _ssl_handlers()
        client_ssl = SslIoPipelineHandler(
            ssl.create_default_context(),
            server_side=False,
            server_hostname='localhost',
        )
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        flush = IoPipelineFlowMessages.FlushOutput()
        shutdown = IoPipelineMessages.ShutdownOutput()
        final = IoPipelineMessages.FinalOutput()
        try:
            client.enqueue(_Emit(b'undelivered', flush, shutdown, final))
            link.pump()

            self.assertTrue(any(isinstance(exc, ssl.SSLCertVerificationError) for exc in client_app.errors))
            self.assertTrue(flush.is_failed())
            self.assertTrue(shutdown.is_failed())
            self.assertTrue(final.is_succeeded(), 'retained FinalOutput was stranded on handshake SSLError')
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
        finally:
            client.close()
            server.close()

    # If _step_reads decrypts authenticated plaintext into in_chunks on one pump iteration and a later iteration's
    # _step_writes raises ssl.SSLError, _turn() previously dropped in_chunks, left _staged_plaintext_bytes permanently
    # inflated in inbound_buffered_bytes(), and stranded any retained FinalOutput.

    def test_pump_write_ssl_error_preserves_decrypted_in_chunks_and_releases_final_output(self) -> None:
        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.ESTABLISHED)

            # Produce a real encrypted TLS record from the server without feeding it to the client yet.
            server.enqueue(_Emit(b'authenticated server data'))
            self.assertIsNone(server.next(read=False))
            server_wire = server.drain_output()
            self.assertTrue(server_wire)

            # Wrap the client's real SSLObject so iteration 1 write yields WANT_READ, iteration 1 read decrypts the
            # real server record into in_chunks, and iteration 2 write raises a real SSLError.
            write_err = ssl.SSLError('simulated write failure after read')
            client_ssl._ssl_obj = _WantReadThenErrorWriteSslObject(  # type: ignore[assignment]
                check.not_none(client_ssl.ssl_object),
                write_err,
            )

            flush = IoPipelineFlowMessages.FlushOutput()
            final = IoPipelineMessages.FinalOutput()
            client.enqueue(_Emit(b'outbound payload', flush, final))
            client.feed_input(server_wire)
            self.assertIsNone(client.next(read=True, raise_on_stall=False))
            client.drain_output()

            self.assertEqual(bytes(client_app.received), b'authenticated server data')
            self.assertEqual(client_ssl.inbound_buffered_bytes(), 0)
            self.assertTrue(flush.is_failed())
            self.assertTrue(final.is_succeeded())
            self.assertIn(write_err, client_app.errors)
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
        finally:
            client.close()
            server.close()


class TestManualReadShutdownBacklogTimeout(unittest.TestCase):
    # In manual-read mode, if the peer sends application data followed by close_notify and the local side sends
    # FinalOutput without reading, _step_close drains the unread data into _plaintext_backlog and transitions _state
    # from SHUTTING_DOWN to CLOSED while still retaining FinalOutput until the backlog drains. Previously
    # _shutdown_timeout_active() only checked _state == SHUTTING_DOWN, which cancelled (or never armed)
    # shutdown_timeout_s and deadlocked FinalOutput indefinitely when the app stopped reading.

    def test_shutdown_timeout_fires_when_peer_closes_before_final_output_with_unread_backlog(self) -> None:
        payload = _payload(b'backlog', 32 * 1024)
        client_ssl, server_ssl = _ssl_handlers(
            client_config=SslIoPipelineHandler.Config(
                shutdown_timeout_s=5.,
                read_batch_max_bytes=4096,
            ),
        )
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app, manual_read=True)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.ESTABLISHED)

            server.enqueue(_Emit(payload, IoPipelineMessages.ShutdownOutput()))
            link.pump()

            final = IoPipelineMessages.FinalOutput()
            client.enqueue(_Emit(final))
            link.pump()

            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.CLOSED)
            self.assertGreater(check.not_none(client_ssl.inbound_buffered_bytes()), 0)
            self.assertFalse(final.is_done())
            self.assertEqual(client.next_deadline(), 5.)

            client.advance_time(5.)
            link.pump()

            self.assertEqual(len(client_app.errors), 1)
            self.assertIsInstance(client_app.errors[0], TimeoutIoPipelineError)
            self.assertTrue(final.is_succeeded())
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
        finally:
            client.close()
            server.close()

    def test_shutdown_timeout_survives_peer_close_notify_with_unread_backlog(self) -> None:
        payload = _payload(b'backlog2', 32 * 1024)
        client_ssl, server_ssl = _ssl_handlers(
            client_config=SslIoPipelineHandler.Config(
                shutdown_timeout_s=5.,
                read_batch_max_bytes=4096,
            ),
        )
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app, manual_read=True)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()

            # Client initiates close first (arms shutdown timer in SHUTTING_DOWN).
            final = IoPipelineMessages.FinalOutput()
            client.enqueue(_Emit(final))
            link.pump()
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.SHUTTING_DOWN)
            self.assertEqual(client.next_deadline(), 5.)

            # Peer sends unread data + close_notify while client does not issue ReadyForInput.
            server.enqueue(_Emit(payload, IoPipelineMessages.ShutdownOutput()))
            link.pump()

            # State is now CLOSED with a retained backlog holding FinalOutput; the shutdown timer must stay armed.
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.CLOSED)
            self.assertFalse(final.is_done())
            self.assertEqual(client.next_deadline(), 5.)

            client.advance_time(5.)
            link.pump()

            self.assertEqual(len(client_app.errors), 1)
            self.assertIsInstance(client_app.errors[0], TimeoutIoPipelineError)
            self.assertTrue(final.is_succeeded())
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
        finally:
            client.close()
            server.close()

    def test_draining_shutdown_backlog_before_timeout_cancels_timer_cleanly(self) -> None:
        payload = _payload(b'backlog3', 16 * 1024)
        client_ssl, server_ssl = _ssl_handlers(
            client_config=SslIoPipelineHandler.Config(
                shutdown_timeout_s=5.,
                read_batch_max_bytes=4096,
            ),
        )
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app, manual_read=True)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()
            server.enqueue(_Emit(payload, IoPipelineMessages.ShutdownOutput()))
            link.pump()

            final = IoPipelineMessages.FinalOutput()
            client.enqueue(_Emit(final))
            link.pump()
            self.assertEqual(client.next_deadline(), 5.)

            for _ in range(100):
                if final.is_done():
                    break
                client.enqueue(_Emit(IoPipelineFlowMessages.ReadyForInput()))
                link.pump()

            self.assertEqual(bytes(client_app.received), payload)
            self.assertTrue(client_app.saw_final_input)
            self.assertTrue(final.is_succeeded())
            self.assertIsNone(client.next_deadline())
            self.assertEqual(client_app.errors, [])
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
        finally:
            client.close()
            server.close()


class TestReadGeneratedControlRecordsFlush(unittest.TestCase):
    # OpenSSL's SSL_read() can write TLS control records (TLS 1.3 post-handshake authentication responses, KeyUpdate
    # replies, renegotiation flights, or alerts) directly into out_bio without raising SSLWantWriteError (MemoryBIO is
    # unbounded). Previously _read_engine never checked whether out_bio grew, leaving _control_activity False so
    # _emit() omitted the progress FlushOutput and trapped those control records inside an outbound byte buffer.

    def test_tls13_post_handshake_auth_flushes_through_outbound_buffer(self) -> None:
        cert = _cert()
        server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        server_ctx.maximum_version = ssl.TLSVersion.TLSv1_3
        server_ctx.load_cert_chain(cert.cert_file, cert.key_file)
        server_ctx.load_verify_locations(cafile=cert.cert_file)
        server_ctx.verify_mode = ssl.CERT_OPTIONAL
        server_ctx.post_handshake_auth = True

        client_ctx = ssl.create_default_context(cafile=cert.cert_file)
        client_ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        client_ctx.maximum_version = ssl.TLSVersion.TLSv1_3
        client_ctx.load_cert_chain(cert.cert_file, cert.key_file)
        client_ctx.post_handshake_auth = True

        client_buf = OutboundBytesBufferIoPipelineHandler()
        client_ssl = SslIoPipelineHandler(client_ctx, server_side=False, server_hostname='localhost')
        server_ssl = SslIoPipelineHandler(server_ctx, server_side=True)
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)

        client = _pure(client_buf, client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.ESTABLISHED)
            self.assertIs(server_ssl.state, SslIoPipelineHandler.State.ESTABLISHED)
            self.assertIsNone(check.not_none(server_ssl.ssl_object).getpeercert())

            # Server initiates real TLS 1.3 post-handshake authentication and sends application data so the client's
            # SSL_read processes the CertificateRequest and writes Certificate/CertificateVerify/Finished into out_bio.
            check.not_none(server_ssl.ssl_object).verify_client_post_handshake()
            server.enqueue(_Emit(b'challenge', IoPipelineFlowMessages.FlushOutput()))
            link.pump()

            # Without _control_activity set on out_bio growth during SSL_read, the client's auth response stays stuck
            # inside client_buf and the server never sees the client certificate.
            self.assertEqual(bytes(client_app.received), b'challenge')
            self.assertEqual(client_buf.outbound_buffered_bytes(), 0)
            peer_cert = check.not_none(server_ssl.ssl_object).getpeercert()
            self.assertTrue(peer_cert, 'client post-handshake auth record stayed trapped in outbound buffer')
            self.assertEqual(client_app.errors, [])
            self.assertEqual(server_app.errors, [])
        finally:
            client.close()
            server.close()


class TestClosedStateOutputFences(unittest.TestCase):
    # After a TLS session transitions to State.CLOSED due to a failure (e.g. certificate verification failure) before
    # FinalOutput/ShutdownOutput, subsequent plaintext writes were silently dropped while FlushOutput and
    # ShutdownOutput were forwarded to the transport and reported success.

    def test_writes_and_fences_after_failed_closed_state_fail_rather_than_succeed(self) -> None:
        _, server_ssl = _ssl_handlers()
        client_ssl = SslIoPipelineHandler(
            ssl.create_default_context(),
            server_side=False,
            server_hostname='localhost',
        )
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.CLOSED)
            self.assertTrue(any(isinstance(exc, ssl.SSLCertVerificationError) for exc in client_app.errors))

            flush = IoPipelineFlowMessages.FlushOutput()
            shutdown1 = IoPipelineMessages.ShutdownOutput()
            shutdown2 = IoPipelineMessages.ShutdownOutput()
            shutdown2_excs: ta.List[ta.Optional[BaseException]] = []
            shutdown2.add_listener(lambda m: shutdown2_excs.append(m.get_exception()))
            client.enqueue(_Emit(b'dropped plaintext', flush, shutdown1, shutdown2))
            link.pump()

            self.assertTrue(flush.is_failed(), 'FlushOutput succeeded after failed CLOSED TLS session dropped writes')
            self.assertTrue(shutdown1.is_failed(), 'ShutdownOutput succeeded on failed CLOSED TLS session')
            self.assertTrue(shutdown2.is_failed(), 'duplicate ShutdownOutput succeeded on failed CLOSED TLS session')
            self.assertEqual(len(shutdown2_excs), 1)
            self.assertIsInstance(shutdown2_excs[0], SawShutdownOutputIoPipelineError)
            self.assertFalse(client.output_shutdown)
            self.assertEqual(bytes(server_app.received), b'')
        finally:
            client.close()
            server.close()


class TestPartialSslWrite(unittest.TestCase):
    # _step_writes previously discarded the return value of SSLObject.write(mv) and unconditionally popped the whole
    # segment from _write_q, silently truncating outbound data if SSL_write returned a short count.

    def test_partial_ssl_write_retains_unwritten_suffix_and_delivers_all_bytes(self) -> None:
        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.ESTABLISHED)

            wrapped = _PartialWriteSslObject(check.not_none(client_ssl.ssl_object), max_write=13)
            client_ssl._ssl_obj = wrapped  # type: ignore[assignment]

            payload = _payload(b'partial-write', 5000)
            flush = IoPipelineFlowMessages.FlushOutput()
            shutdown = IoPipelineMessages.ShutdownOutput()
            client.enqueue(_Emit(payload, flush, shutdown))
            link.pump()

            self.assertGreater(wrapped.partial_writes, 100)
            self.assertEqual(bytes(server_app.received), payload)
            self.assertTrue(server_app.saw_final_input)
            self.assertTrue(flush.is_succeeded())
            self.assertTrue(shutdown.is_succeeded())
            self.assertEqual(client_ssl.outbound_buffered_bytes(), 0)
            self.assertEqual(client_app.errors, [])
            self.assertEqual(server_app.errors, [])
        finally:
            client.close()
            server.close()
