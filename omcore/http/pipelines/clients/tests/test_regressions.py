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
from .....io.pipelines.drivers.pure import PureIoPipelineDriver
from .....io.pipelines.flow.stub import StubIoPipelineFlowService
from .....io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from ...requests import FullIoPipelineHttpRequest
from ...responses import FullIoPipelineHttpResponse
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
