# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
Regression tests for defects in the HTTP client found reviewing the io.pipelines half-close work. The ids in the
comments are those of the review findings recorded in FINDINGS.md at commit 323de87b3; each comment describes the defect
as it was found.
"""
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.drivers.pure.drivers import PureIoPipelineDriver
from .....io.pipelines.flow.stub import StubIoPipelineFlowService
from .....io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from .....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ...requests import FullIoPipelineHttpRequest
from ...responses import FullIoPipelineHttpResponse
from ...responses import IoPipelineHttpResponseAborted
from ..clients import IoPipelineHttpClientHandler
from ..clients import IoPipelineHttpClientMessages
from ..requests import IoPipelineHttpRequestEncoder
from ..responses import IoPipelineHttpClientResponseDecoder
from ..responses import IoPipelineHttpResponseAggregatorDecoder


##


class TestResponsesAfterOutputHalfClose(unittest.TestCase):
    # T1 (TODO.md: "mark host-facing messages AfterShutdownOutput - ... http client IoPipelineHttpClientMessages.Output
    # - which would otherwise be rejected after a half-close"). A client sends its request and half-closes its output,
    # as `curl` does for a one-shot request. The response then decodes normally, but the client handler's host-facing
    # Output wrapping it is rejected at the terminal, the handler reports the rejection as the error and closes, and
    # the host sees an exception instead of its response.

    def test_response_reaches_the_host_after_the_request_half_close(self) -> None:
        feedback = FeedbackInboundIoPipelineHandler()
        drv = PureIoPipelineDriver(IoPipeline.Spec(
            [
                IoPipelineHttpRequestEncoder(),
                IoPipelineHttpClientResponseDecoder(),
                IoPipelineHttpResponseAggregatorDecoder(),
                IoPipelineHttpClientHandler(),
                feedback,
            ],
            services=[StubIoPipelineFlowService(auto_read=False)],
        ))
        try:
            self.assertIsNone(drv.next(read=False))
            request = IoPipelineHttpClientMessages.Request(FullIoPipelineHttpRequest.simple('GET', '/'), aggregate=True)
            drv.enqueue(request)
            self.assertIsNone(drv.next(read=False))
            self.assertIn(b'GET / HTTP/1.1', drv.drain_output())

            shutdown = IoPipelineMessages.ShutdownOutput()
            drv.enqueue(feedback.wrap(shutdown))
            self.assertIsNone(drv.next(read=False))
            drv.drain_output()
            self.assertTrue(shutdown.is_succeeded())
            self.assertTrue(drv.output_shutdown)

            drv.feed_input(b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok')
            out = drv.next(read=True, raise_on_stall=False)
            self.assertIsInstance(out, IoPipelineHttpClientMessages.Output, out)
            assert out is not None
            self.assertIsInstance(out.msg, FullIoPipelineHttpResponse)
            self.assertEqual(out.msg.head.status, 200)
            self.assertTrue(drv.pipeline.is_ready)
        finally:
            drv.close()


class TestHttpClientHandlerLifecycleRegressions(unittest.TestCase):
    def test_aborted_response_clears_inflight_request(self) -> None:
        # Regression: IoPipelineHttpClientHandler.inbound did not clear self._request when receiving
        # IoPipelineHttpResponseAborted. In a streaming/non-aggregating or malformed-response path, FlushInput then
        # kept requesting more input for the dead request and self._request remained permanently non-None.
        client = IoPipelineHttpClientHandler()
        drv = PureIoPipelineDriver(IoPipeline.Spec(
            [
                IoPipelineHttpRequestEncoder(),
                IoPipelineHttpClientResponseDecoder(),
                IoPipelineHttpResponseAggregatorDecoder(),
                client,
            ],
            services=[StubIoPipelineFlowService(auto_read=False)],
        ))
        try:
            self.assertIsNone(drv.next(read=False))
            request = IoPipelineHttpClientMessages.Request(FullIoPipelineHttpRequest.simple('example.com', '/'), aggregate=True)  # noqa
            drv.enqueue(request)
            self.assertIsNone(drv.next(read=False))
            drv.drain_output()
            self.assertIs(client._request, request)  # noqa

            # Malformed chunk header triggers a real IoPipelineHttpResponseAborted from the decoder.
            drv.feed_input(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\nZZZ\r\n')
            out = drv.next(read=True, raise_on_stall=False)
            self.assertIsInstance(out, IoPipelineHttpClientMessages.Output)
            assert out is not None
            self.assertIsInstance(out.msg, IoPipelineHttpResponseAborted)
            self.assertIs(out.request, request)
            self.assertIsNone(client._request)  # noqa
        finally:
            drv.close()

    def test_final_input_after_error_does_not_raise_saw_final_output(self) -> None:
        # Regression: IoPipelineHttpClientHandler emitted FinalOutput upon receiving IoPipelineMessages.Error. If
        # FinalInput subsequently arrived during teardown, the handler unconditionally called ctx.feed_out(Output(...))
        # and ctx.feed_out(FinalOutput()), raising SawFinalOutputIoPipelineError and preventing FinalInput from
        # propagating.
        client = IoPipelineHttpClientHandler()
        ibq = InboundQueueIoPipelineHandler()
        channel = IoPipeline.new(
            [
                IoPipelineHttpRequestEncoder(),
                IoPipelineHttpClientResponseDecoder(),
                IoPipelineHttpResponseAggregatorDecoder(),
                client,
                ibq,
            ],
            services=[StubIoPipelineFlowService(auto_read=False)],
        )
        try:
            req = IoPipelineHttpClientMessages.Request(
                FullIoPipelineHttpRequest.simple('example.com', '/'),
                aggregate=True,
            )
            channel.feed_in(req)
            channel.output.drain()

            err = RuntimeError('transport failure')
            channel.feed_in(IoPipelineMessages.Error(err))
            out_err = channel.output.drain()
            self.assertIn(err, out_err)
            self.assertIsInstance(out_err[-1], IoPipelineMessages.FinalOutput)
            self.assertTrue(channel.saw_final_output)

            # Teardown FinalInput after Error must propagate cleanly without raising or emitting a second FinalOutput.
            channel.feed_final_input()
            self.assertEqual(channel.output.drain(), [])
            self.assertEqual([type(m) for m in ibq.drain()], [IoPipelineMessages.FinalInput])
        finally:
            channel.destroy()
