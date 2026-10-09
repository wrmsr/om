# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import typing as ta
import unittest

from ...core import IoPipelineMessages
from ...drivers.types import IoPipelineDriverState
from ...flow.types import IoPipelineFlowMessages
from ..handlers import SslIoPipelineHandler
from .test_halfclose import _App
from .test_halfclose import _Emit
from .test_halfclose import _payload
from .test_halfclose import _pure
from .test_halfclose import _PureLink
from .test_halfclose import _ssl_handlers


class TestTlsHalfCloseEdges(unittest.TestCase):
    def test_manual_read_half_close_then_final_output_receives_whole_response(self) -> None:
        # test_final_output_after_half_close_waits_for_peer_close_notify, but the client reads manually and the
        # response spans several TLS records.
        response = _payload(b'response', 100_000)

        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(close_on_final_input=False, manual_read=True)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app, manual_read=True)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            link.pump()

            final_output = IoPipelineMessages.FinalOutput()
            client.enqueue(_Emit(b'request', IoPipelineMessages.ShutdownOutput(), final_output))
            link.pump()
            self.assertFalse(final_output.is_done())
            self.assertTrue(server_app.saw_final_input)

            server.enqueue(_Emit(response, IoPipelineMessages.ShutdownOutput()))
            link.pump()

            self.assertEqual(len(client_app.received), len(response))
            self.assertTrue(client_app.saw_final_input)
            self.assertTrue(final_output.is_succeeded())
            self.assertEqual(client_app.errors, [])

        finally:
            client.close()
            server.close()

    def test_half_close_with_unread_input_and_ragged_eof_still_delivers_input_and_eof(self) -> None:
        # Data the app has not read yet sits in the engine, followed by a transport EOF without close_notify (accepted:
        # suppress_ragged_eofs=True, the default). The app then half-closes its output and keeps reading.
        data = _payload(b'data', 60_000)

        client_ssl, server_ssl = _ssl_handlers(strict_eof=False)
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app, manual_read=True)
        server = _pure(server_ssl, server_app)
        link = _PureLink(client, server)
        try:
            client.enqueue(_Emit(IoPipelineFlowMessages.ReadyForInput()))
            link.pump()
            self.assertIs(client_ssl.state, SslIoPipelineHandler.State.ESTABLISHED)

            # One read token outstanding; the server's records and a bare transport EOF arrive in one read batch.
            client.enqueue(_Emit(IoPipelineFlowMessages.ReadyForInput()))
            self.assertIsNone(client.next(read=False))
            server.enqueue(_Emit(data))
            self.assertIsNone(server.next(read=False))
            client.feed_input(server.drain_output())
            client.feed_eof()
            self.assertIsNone(client.next(read=True, raise_on_stall=False))

            # One record's plaintext was delivered for the token; the rest is still undelivered.
            self.assertGreater(len(client_app.received), 0)
            self.assertLess(len(client_app.received), len(data))
            self.assertFalse(client_app.saw_final_input)

            client.enqueue(_Emit(IoPipelineMessages.ShutdownOutput()))
            self.assertIsNone(client.next(read=False))

            for _ in range(100):
                if client_app.saw_final_input:
                    break
                client.enqueue(_Emit(IoPipelineFlowMessages.ReadyForInput()))
                self.assertIsNone(client.next(read=True, raise_on_stall=False))

            self.assertEqual(len(client_app.received), len(data))
            self.assertTrue(client_app.saw_final_input)
            self.assertIs(client.state, IoPipelineDriverState.RUNNING)

        finally:
            client.close()
            server.close()

    def test_final_output_behind_half_close_during_handshake_does_not_drop_its_output(self) -> None:
        # "A half-close requested during the handshake waits for it to finish." A FinalOutput queued behind it must not
        # pre-empt it: the request precedes the ShutdownOutput, whose success means that request crossed the transport.
        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        try:
            shutdown_output = IoPipelineMessages.ShutdownOutput()
            final_output = IoPipelineMessages.FinalOutput()
            client.enqueue(_Emit(b'request', shutdown_output, final_output))
            _PureLink(client, server).pump()

            self.assertTrue(shutdown_output.is_succeeded())
            self.assertEqual(bytes(server_app.received), b'request')
            self.assertEqual(server_app.errors, [])

        finally:
            client.close()
            server.close()

    def test_final_output_does_not_complete_ahead_of_earlier_fences_during_handshake(self) -> None:
        client_ssl, server_ssl = _ssl_handlers()
        client_app = _App(close_on_final_input=False)
        server_app = _App(close_on_final_input=False)
        client = _pure(client_ssl, client_app)
        server = _pure(server_ssl, server_app)
        try:
            flush_output = IoPipelineFlowMessages.FlushOutput()
            shutdown_output = IoPipelineMessages.ShutdownOutput()
            final_output = IoPipelineMessages.FinalOutput()
            order: ta.List[str] = []
            flush_output.add_listener(lambda _: order.append('flush'))
            shutdown_output.add_listener(lambda _: order.append('shutdown'))
            final_output.add_listener(lambda _: order.append('final'))

            client.enqueue(_Emit(b'request', flush_output, shutdown_output, final_output))
            _PureLink(client, server).pump()
            client.close()

            self.assertEqual(order, ['flush', 'shutdown', 'final'])

        finally:
            client.close()
            server.close()
