# ruff: noqa: UP006 UP007 UP045
# @om-lite
import unittest

from ....io.pipelines.core import IoPipeline
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.flow.stub import StubIoPipelineFlowService
from ....io.pipelines.flow.types import IoPipelineFlowMessages
from ....io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from ...headers import HttpHeaders
from ..responses import IoPipelineHttpResponseBodyData
from ..responses import IoPipelineHttpResponseHead
from ..servers.responses import IoPipelineHttpResponseChunker
from .test_chunking import CaptureOutputWritabilityIoPipelineHandler


##


class TestShutdownWritability(unittest.TestCase):
    def test_chunker_does_not_resume_output_after_shutdown(self):
        chunker = IoPipelineHttpResponseChunker(write_high_watermark=4, write_low_watermark=2)
        capture = CaptureOutputWritabilityIoPipelineHandler()
        feedback = FeedbackInboundIoPipelineHandler()
        with IoPipeline.new([chunker, capture, feedback], services=[StubIoPipelineFlowService()]) as pipeline:
            pipeline.feed_in(feedback.wrap(IoPipelineHttpResponseHead(
                status=200,
                reason='OK',
                headers=HttpHeaders([('Transfer-Encoding', 'chunked')]),
            )))
            pipeline.feed_in(feedback.wrap(IoPipelineHttpResponseBodyData(b'hello')))
            self.assertEqual([type(e) for e in capture.events], [IoPipelineFlowMessages.PauseOutput])

            shutdown = IoPipelineMessages.ShutdownOutput()
            pipeline.feed_in(feedback.wrap(shutdown))
            self.assertIn(shutdown, pipeline.output.drain())
            self.assertEqual([type(e) for e in capture.events], [IoPipelineFlowMessages.PauseOutput])
