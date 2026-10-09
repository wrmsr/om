# @om-lite
import ssl
import unittest

from ...core import IoPipelineMessages
from ...flow.types import IoPipelineFlowMessages
from ..handlers import SslIoPipelineHandler
from .test_halfclose import _App
from .test_halfclose import _Emit
from .test_halfclose import _pure
from .test_halfclose import _PureLink
from .test_halfclose import _ssl_handlers


##


class _WritabilityApp(_App):
    def __init__(self):
        super().__init__(close_on_final_input=False)

        self.writability = []

    def inbound(self, ctx, msg):
        if isinstance(msg, (IoPipelineFlowMessages.ReadyForOutput, IoPipelineFlowMessages.PauseOutput)):
            self.writability.append((type(msg), ctx.pipeline.saw_shutdown_output))
        super().inbound(ctx, msg)


class TestTlsAdversarial(unittest.TestCase):
    def test_failed_certificate_verification_fails_undelivered_output_fences(self):
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

    def test_handshake_does_not_resume_output_after_retained_shutdown(self):
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

    def test_handshake_timeout_does_not_report_undelivered_output_as_shutdown_success(self):
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

    def test_strict_eof_detects_truncation_with_default_ssl_contexts(self):
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

    def test_abort_releases_plaintext_waiting_for_handshake(self):
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
