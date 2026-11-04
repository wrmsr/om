# ruff: noqa: PT009 PT027 UP006 UP007 UP045
# @om-lite
import unittest

from ...io.pipelines.bytes.buffers import OutboundBytesBufferIoPipelineHandler
from ...io.pipelines.core import IoPipelineHandler
from ..configs import RpcConfig
from ..errors import RpcCancelledError
from ..errors import RpcConnectionClosedError
from ..errors import RpcErrorCodes
from ..errors import RpcMessageTooLargeError
from ..errors import RpcProtocolError
from ..errors import RpcTimeoutError
from ..errors import RpcTooManyRequestsError
from ..framing import RpcLengthPrefixedFramingIoPipelineHandler
from ..keepalive import RpcKeepaliveIoPipelineHandler
from ..messages import RpcCancelMessage
from ..messages import RpcErrorMessage
from ..messages import RpcNotificationMessage
from ..messages import RpcPingMessage
from ..messages import RpcPongMessage
from ..messages import RpcRequestMessage
from ..messages import RpcResultMessage
from ..messages import RpcSessionMessages as Rsm
from ..session import RpcSessionIoPipelineHandler
from ..specs import rpc_build_pipeline_spec
from .raw import RawRpcPeer


##


class TestSessionInbound(unittest.TestCase):
    def test_request_response(self):
        p = RawRpcPeer()
        req = RpcRequestMessage(1, 'm', {'a': 1})
        p.send(req)
        self.assertEqual(p.take_events(), [Rsm.RequestReceived(req)])

        p.cmd(Rsm.SendResponse(RpcResultMessage(1, 'ok')))
        self.assertEqual(p.recv(), [RpcResultMessage(1, 'ok')])
        self.assertEqual(p.take_events(), [])

    def test_ping_answered_without_host(self):
        p = RawRpcPeer()
        p.send(RpcPingMessage('x'))
        self.assertEqual(p.recv(), [RpcPongMessage('x')])
        self.assertEqual(p.take_events(), [])

    def test_notification(self):
        p = RawRpcPeer()
        p.send(RpcNotificationMessage('n', [1]))
        self.assertEqual(p.take_events(), [Rsm.NotificationReceived(RpcNotificationMessage('n', [1]))])

    def test_duplicate_inbound_id_is_fatal(self):
        p = RawRpcPeer()
        p.send(RpcRequestMessage(1, 'm'), RpcRequestMessage(1, 'm'))
        [closed] = p.take_events(Rsm.Closed)
        self.assertIsInstance(closed.exc, RpcProtocolError)

    def test_reused_id_after_answer_is_fine(self):
        p = RawRpcPeer()
        p.send(RpcRequestMessage(1, 'm'))
        p.cmd(Rsm.SendResponse(RpcResultMessage(1)))
        p.send(RpcRequestMessage(1, 'm'))
        self.assertEqual(len(p.take_events(Rsm.RequestReceived)), 2)
        self.assertEqual(p.take_events(Rsm.Closed), [])

    def test_busy(self):
        p = RawRpcPeer(RpcConfig(max_inflight_inbound=1))
        p.send(RpcRequestMessage(1, 'm'), RpcRequestMessage(2, 'm'))
        self.assertEqual(len(p.take_events(Rsm.RequestReceived)), 1)
        [busy] = p.recv()
        self.assertIsInstance(busy, RpcErrorMessage)
        self.assertEqual(busy.id, 2)
        self.assertEqual(busy.error.code, RpcErrorCodes.BUSY)

        p.cmd(Rsm.SendResponse(RpcResultMessage(1)))
        p.send(RpcRequestMessage(3, 'm'))
        self.assertEqual(len(p.take_events(Rsm.RequestReceived)), 1)

    def test_pause(self):
        p = RawRpcPeer(RpcConfig(max_inflight_inbound=1, inflight_limit_policy='pause'))
        p.send(RpcRequestMessage(1, 'm'))
        self.assertEqual([e.request.id for e in p.take_events(Rsm.RequestReceived)], [1])

        # At the limit the transport is no longer read, so this waits in the transport.
        p.send(RpcRequestMessage(2, 'm'))
        self.assertEqual(p.take_events(Rsm.RequestReceived), [])
        self.assertGreater(p.driver.pending_input_bytes, 0)
        self.assertEqual(p.recv(), [])

        p.cmd(Rsm.SendResponse(RpcResultMessage(1)))
        self.assertEqual([e.request.id for e in p.take_events(Rsm.RequestReceived)], [2])
        self.assertEqual(p.recv(), [RpcResultMessage(1)])

    def test_peer_cancel(self):
        p = RawRpcPeer()
        p.send(RpcRequestMessage(1, 'm'), RpcCancelMessage(1))
        [_, aborted] = p.take_events()
        self.assertIsInstance(aborted, Rsm.RequestHandlingAborted)
        self.assertIsInstance(aborted.exc, RpcCancelledError)

        # The peer has given up: nothing is sent, and a late response is dropped.
        p.cmd(Rsm.SendResponse(RpcResultMessage(1)))
        self.assertEqual(p.recv(), [])

        # Cancelling an unknown or finished request is harmless.
        p.send(RpcCancelMessage(99))
        self.assertEqual(p.take_events(), [])

    def test_handling_timeout(self):
        p = RawRpcPeer(RpcConfig(inbound_handling_timeout_s=5.))
        p.send(RpcRequestMessage(1, 'm'))
        p.take_events()
        p.advance(4.9)
        self.assertEqual(p.recv(), [])
        p.advance(.1)
        [err] = p.recv()
        self.assertIsInstance(err, RpcErrorMessage)
        self.assertEqual(err.error.code, RpcErrorCodes.HANDLING_TIMEOUT)
        [aborted] = p.take_events(Rsm.RequestHandlingAborted)
        self.assertIsInstance(aborted.exc, RpcTimeoutError)

    def test_pause_admits_a_read_batch(self):
        # Pausing stops further reads; frames already read in the same batch are still admitted.
        p = RawRpcPeer(RpcConfig(max_inflight_inbound=1, inflight_limit_policy='pause'))
        p.send(RpcRequestMessage(1, 'm'), RpcRequestMessage(2, 'm'))
        self.assertEqual([e.request.id for e in p.take_events(Rsm.RequestReceived)], [1, 2])

    def test_unencodable_response_substituted(self):
        p = RawRpcPeer()
        p.send(RpcRequestMessage(1, 'm'), RpcRequestMessage(2, 'm'))
        p.cmd(Rsm.SendResponse(RpcResultMessage(1, object())))
        p.cmd(Rsm.SendResponse(RpcResultMessage(2, 'fine')))
        [r1, r2] = p.recv()
        self.assertEqual(r1.error.code, RpcErrorCodes.RESULT_ENCODING)
        self.assertEqual(r2, RpcResultMessage(2, 'fine'))

        p2 = RawRpcPeer(RpcConfig(max_frame_bytes=200))
        p2.send(RpcRequestMessage(2, 'm'))
        p2.cmd(Rsm.SendResponse(RpcResultMessage(2, 'x' * 1000)))
        [r3] = p2.recv()
        self.assertEqual(r3.error.code, RpcErrorCodes.RESULT_TOO_LARGE)


class TestSessionOutbound(unittest.TestCase):
    def test_request_sent_and_answered(self):
        p = RawRpcPeer()
        req = RpcRequestMessage(1, 'm', 'p')
        cmd = Rsm.SendRequest(req)
        p.cmd(cmd)
        self.assertEqual(p.take_events(), [])
        self.assertEqual(p.recv(), [req])
        self.assertEqual(p.take_events(), [Rsm.Sent(cmd)])

        p.send(RpcResultMessage(1, 'r'))
        self.assertEqual(p.take_events(), [Rsm.ResponseReceived(req, RpcResultMessage(1, 'r'))])

    def test_duplicate_and_limit(self):
        p = RawRpcPeer(RpcConfig(max_pending_outbound=1))
        p.cmd(Rsm.SendRequest(RpcRequestMessage(1, 'm')))
        p.cmd(Rsm.SendRequest(RpcRequestMessage(1, 'm')))
        p.cmd(Rsm.SendRequest(RpcRequestMessage(2, 'm')))
        fails = p.take_events(Rsm.RequestFailed)
        self.assertIsInstance(fails[0].exc, ValueError)
        self.assertIsInstance(fails[1].exc, RpcTooManyRequestsError)

    def test_request_timeout_cancels_peer(self):
        p = RawRpcPeer(RpcConfig(default_request_timeout_s=3.))
        p.cmd(Rsm.SendRequest(RpcRequestMessage(1, 'm')))
        p.cmd(Rsm.SendRequest(RpcRequestMessage(2, 'm'), timeout_s=None))
        p.recv()
        p.advance(3.)
        [failed] = p.take_events(Rsm.RequestFailed)
        self.assertEqual(failed.request.id, 1)
        self.assertIsInstance(failed.exc, RpcTimeoutError)
        self.assertEqual(p.recv(), [RpcCancelMessage(1)])

        # A late response is dropped quietly.
        p.send(RpcResultMessage(1))
        self.assertEqual(p.take_events(Rsm.ResponseReceived, Rsm.Closed), [])

        p.advance(1000.)
        self.assertEqual(p.take_events(Rsm.RequestFailed), [])

    def test_request_timeout_no_cancel(self):
        p = RawRpcPeer(RpcConfig(default_request_timeout_s=3., cancel_abandoned_requests=False))
        p.cmd(Rsm.SendRequest(RpcRequestMessage(1, 'm')))
        p.recv()
        p.advance(3.)
        self.assertEqual(len(p.take_events(Rsm.RequestFailed)), 1)
        self.assertEqual(p.recv(), [])

    def test_cancel_request(self):
        p = RawRpcPeer()
        p.cmd(Rsm.SendRequest(RpcRequestMessage(1, 'm')), Rsm.SendRequest(RpcRequestMessage(2, 'm')))
        p.recv()
        p.cmd(Rsm.CancelRequest(1), Rsm.CancelRequest(2, notify_peer=False))
        self.assertEqual(p.recv(), [RpcCancelMessage(1)])
        p.send(RpcResultMessage(1), RpcResultMessage(2))
        self.assertEqual(p.take_events(Rsm.ResponseReceived, Rsm.RequestFailed), [])

    def test_unmatched_response(self):
        p = RawRpcPeer()
        p.send(RpcResultMessage(7))
        self.assertEqual(p.take_events(), [])

        p = RawRpcPeer(RpcConfig(on_unmatched_response='close'))
        p.send(RpcResultMessage(7))
        [closed] = p.take_events(Rsm.Closed)
        self.assertIsInstance(closed.exc, RpcProtocolError)

    def test_unencodable_request(self):
        p = RawRpcPeer()
        req = RpcRequestMessage(1, 'm', object())
        cmd = Rsm.SendRequest(req)
        p.cmd(cmd)
        [failed] = p.take_events(Rsm.RequestFailed)
        self.assertIsInstance(failed.exc, ValueError)

        p.recv()
        self.assertEqual(p.take_events(), [Rsm.Sent(cmd)])

        # Still usable.
        p.cmd(Rsm.SendRequest(RpcRequestMessage(2, 'm')))
        self.assertEqual(p.recv(), [RpcRequestMessage(2, 'm')])

    def test_oversized_request(self):
        p = RawRpcPeer(RpcConfig(max_frame_bytes=100))
        p.cmd(Rsm.SendRequest(RpcRequestMessage(1, 'm', 'x' * 200)))
        [failed] = p.take_events(Rsm.RequestFailed)
        self.assertIsInstance(failed.exc, RpcMessageTooLargeError)

    def test_ping(self):
        p = RawRpcPeer(RpcConfig(default_ping_timeout_s=2.))
        p.cmd(Rsm.SendPing(RpcPingMessage('a')), Rsm.SendPing(RpcPingMessage('b')))
        self.assertEqual(p.recv(), [RpcPingMessage('a'), RpcPingMessage('b')])
        p.take_events(Rsm.Sent)
        p.send(RpcPongMessage('a'))
        self.assertEqual(p.take_events(), [Rsm.PongReceived(RpcPingMessage('a'), RpcPongMessage('a'))])
        p.advance(2.)
        [failed] = p.take_events()
        self.assertIsInstance(failed, Rsm.PingFailed)
        self.assertIsInstance(failed.exc, RpcTimeoutError)


class TestSessionLifecycle(unittest.TestCase):
    def test_graceful_close_idle(self):
        p = RawRpcPeer()
        p.cmd(Rsm.Close())
        self.assertEqual(p.take_events(), [Rsm.Closed(None)])
        p.recv()
        self.assertFalse(p.is_live)

    def test_graceful_close_drains(self):
        p = RawRpcPeer()
        p.send(RpcRequestMessage(1, 'm'))
        p.cmd(Rsm.SendRequest(RpcRequestMessage(9, 'm')))
        p.recv()
        p.take_events()

        p.cmd(Rsm.Close())
        self.assertEqual(p.take_events(Rsm.Closed), [])

        # New requests are refused while closing, from both sides.
        p.cmd(Rsm.SendRequest(RpcRequestMessage(10, 'm')))
        [failed] = p.take_events(Rsm.RequestFailed)
        self.assertIsInstance(failed.exc, RpcConnectionClosedError)
        p.send(RpcRequestMessage(2, 'm'))
        [refused] = p.recv()
        self.assertEqual(refused.error.code, RpcErrorCodes.SHUTTING_DOWN)

        p.cmd(Rsm.SendResponse(RpcResultMessage(1)))
        self.assertEqual(p.take_events(Rsm.Closed), [])
        p.send(RpcResultMessage(9))
        self.assertEqual(p.take_events(Rsm.Closed), [Rsm.Closed(None)])
        self.assertEqual(p.recv(), [RpcResultMessage(1)])
        self.assertFalse(p.is_live)

    def test_graceful_close_drain_timeout(self):
        p = RawRpcPeer(RpcConfig(close_drain_timeout_s=5.))
        p.send(RpcRequestMessage(1, 'm'))
        p.take_events()
        p.cmd(Rsm.Close())
        p.advance(5.)
        [aborted] = p.take_events(Rsm.RequestHandlingAborted)
        self.assertIsInstance(aborted.exc, RpcConnectionClosedError)
        [closed] = p.take_events(Rsm.Closed)
        self.assertIsInstance(closed.exc, RpcTimeoutError)
        [resp] = p.recv()
        self.assertEqual(resp.error.code, RpcErrorCodes.SHUTTING_DOWN)

    def test_abortive_close(self):
        p = RawRpcPeer()
        p.send(RpcRequestMessage(1, 'm'))
        p.cmd(Rsm.SendRequest(RpcRequestMessage(2, 'm')))
        p.recv()
        p.take_events()
        p.cmd(Rsm.Close(graceful=False))
        evs = p.take_events()
        self.assertEqual(
            [type(e) for e in evs],
            [Rsm.RequestFailed, Rsm.RequestHandlingAborted, Rsm.Closed],
        )

    def test_peer_eof_close(self):
        p = RawRpcPeer()
        p.send(RpcRequestMessage(1, 'm'))
        p.cmd(Rsm.SendRequest(RpcRequestMessage(2, 'm')))
        p.recv()
        p.take_events()
        p.eof()
        evs = p.take_events()
        self.assertEqual(
            [type(e) for e in evs],
            [Rsm.RequestFailed, Rsm.RequestHandlingAborted, Rsm.Closed],
        )
        self.assertIsNone(evs[-1].exc)

    def test_peer_eof_drain(self):
        p = RawRpcPeer(RpcConfig(on_peer_eof='drain'))
        p.send(RpcRequestMessage(1, 'm'))
        p.take_events()
        p.eof()
        self.assertEqual(p.take_events(), [])
        p.cmd(Rsm.SendResponse(RpcResultMessage(1, 'late')))
        self.assertEqual(p.take_events(), [Rsm.Closed(None)])
        self.assertEqual(p.recv(), [RpcResultMessage(1, 'late')])

    def test_malformed_input_fatal(self):
        p = RawRpcPeer()
        p.send_bytes(b'\x00\x00\x00\x03abc')
        [closed] = p.take_events(Rsm.Closed)
        self.assertIsInstance(closed.exc, RpcProtocolError)

    def test_oversized_input_fatal(self):
        p = RawRpcPeer(RpcConfig(max_frame_bytes=10))
        p.send_bytes(b'\x00\x00\x01\x00')
        [closed] = p.take_events(Rsm.Closed)
        self.assertIsInstance(closed.exc, RpcMessageTooLargeError)

    def test_failure_surfaced_raw_only_for_unhealthy_transport(self):
        # A healthy-transport failure flushes normally: no raw exception output.
        p = RawRpcPeer(RpcConfig(close_drain_timeout_s=1.))
        p.send(RpcRequestMessage(1, 'm'))
        p.cmd(Rsm.Close())
        p.advance(1.)
        self.assertFalse([e for e in p.events if isinstance(e, BaseException)])
        [resp] = p.recv()
        self.assertEqual(resp.error.code, RpcErrorCodes.SHUTTING_DOWN)

        # A transport-level failure surfaces it raw, so the host aborts rather than waiting on the final flush.
        p = RawRpcPeer()
        p.send_bytes(b'\x00\x00\x00\x03abc')
        raws = [e for e in p.events if isinstance(e, BaseException)]
        self.assertEqual(len(raws), 1)
        self.assertIsInstance(raws[0], RpcProtocolError)

    def test_stalled_final_flush_fails_driver(self):
        # The final flush after a close is bounded by the write timeout: the late error escapes the session and fails
        # the driver, which is the abort.
        p = RawRpcPeer(RpcConfig(write_timeout_s=2.))
        p.send(RpcRequestMessage(1, 'm'))
        p.cmd(Rsm.Close(graceful=False))
        self.assertTrue(p.take_events(Rsm.Closed))
        self.assertTrue(p.is_live)
        p.driver.advance_time(2.)
        with self.assertRaises(Exception):  # noqa
            p.step()
        self.assertFalse(p.is_live)

    def test_commands_after_close(self):
        p = RawRpcPeer()
        p.cmd(Rsm.Close(graceful=False))
        self.assertEqual(p.take_events(), [Rsm.Closed(None)])

    def test_idle_timeout(self):
        p = RawRpcPeer(RpcConfig(idle_timeout_s=10.))
        p.send(RpcRequestMessage(1, 'm'))
        p.advance(30.)
        self.assertEqual(p.take_events(Rsm.Closed), [])

        p.cmd(Rsm.SendResponse(RpcResultMessage(1)))
        p.recv()
        p.advance(9.)
        self.assertEqual(p.take_events(Rsm.Closed), [])
        p.advance(1.)
        [closed] = p.take_events(Rsm.Closed)
        self.assertIsInstance(closed.exc, RpcTimeoutError)


class TestKeepalive(unittest.TestCase):
    def _config(self) -> RpcConfig:
        return RpcConfig(keepalive_interval_s=10., keepalive_timeout_s=3.)

    def test_installed_only_when_configured(self):
        self.assertEqual(
            RawRpcPeer().driver.pipeline.find_handlers_of_type(RpcKeepaliveIoPipelineHandler),
            [],
        )
        self.assertEqual(
            len(RawRpcPeer(self._config()).driver.pipeline.find_handlers_of_type(RpcKeepaliveIoPipelineHandler)),
            1,
        )

    def test_pings_when_quiet_and_survives_answers(self):
        p = RawRpcPeer(self._config())
        for _ in range(3):
            p.advance(10.)
            [ping] = p.recv()
            self.assertIsInstance(ping, RpcPingMessage)
            self.assertTrue(str(ping.id).startswith(RpcKeepaliveIoPipelineHandler.ID_PREFIX))
            p.advance(2.)
            p.send(RpcPongMessage(ping.id))
            # Consumed by the keepalive handler: the session never hears of it.
            self.assertEqual(p.take_events(), [])
        self.assertTrue(p.is_live)

    def test_traffic_suppresses_pings(self):
        p = RawRpcPeer(self._config())
        for _ in range(5):
            p.advance(9.)
            p.send(RpcNotificationMessage('n'))
        self.assertEqual(p.recv(), [])

    def test_fails_when_unanswered(self):
        p = RawRpcPeer(self._config())
        p.advance(10.)
        p.recv()
        p.advance(2.9)
        self.assertEqual(p.take_events(Rsm.Closed), [])
        p.advance(.1)
        [closed] = p.take_events(Rsm.Closed)
        self.assertIsInstance(closed.exc, RpcTimeoutError)


class TestSpecs(unittest.TestCase):
    def test_handler_placement(self):
        class Marker(IoPipelineHandler):
            pass

        outer, transport, between, inner = Marker(), Marker(), Marker(), Marker()
        spec = rpc_build_pipeline_spec(
            RpcConfig(keepalive_interval_s=1., keepalive_timeout_s=1.),
            outermost_handlers=[outer],
            transport_handlers=[transport],
            between_handlers=[between],
            innermost_handlers=[inner],
        )
        hs = list(spec.handlers)
        self.assertIs(hs[0], outer)
        self.assertIsInstance(hs[1], OutboundBytesBufferIoPipelineHandler)
        self.assertIs(hs[2], transport)
        framing = next(i for i, h in enumerate(hs) if isinstance(h, RpcLengthPrefixedFramingIoPipelineHandler))
        keepalive = next(i for i, h in enumerate(hs) if isinstance(h, RpcKeepaliveIoPipelineHandler))
        session = next(i for i, h in enumerate(hs) if isinstance(h, RpcSessionIoPipelineHandler))
        self.assertLess(2, framing)
        self.assertLess(framing, keepalive)
        self.assertLess(keepalive, hs.index(between))
        self.assertEqual(hs.index(between) + 1, session)
        self.assertIs(hs[-1], inner)

    def test_minimal(self):
        spec = rpc_build_pipeline_spec(RpcConfig(write_timeout_s=None), without_flow=True)
        self.assertEqual(
            [type(h) for h in spec.handlers][:1],
            [RpcLengthPrefixedFramingIoPipelineHandler],
        )
        self.assertEqual(len(spec.handlers), 3)
