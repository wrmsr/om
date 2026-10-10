# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
Regression tests for defects in the HTTP pipeline found reviewing the io.pipelines half-close work. The ids in the
comments are those of the review findings recorded in FINDINGS.md at commit 323de87b3; each comment describes the defect
as it was found.
"""
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


class TestChunkerWritabilityAfterShutdown(unittest.TestCase):
    # O31 (reviewer 2's HTTP-01, and TODO.md's "stop announcing ReadyForOutput after ShutdownOutput in ... http
    # chunking"). A chunked response buffers five body bytes against a four-byte high watermark, pausing its producer.
    # ShutdownOutput mid-message makes the chunker emit the abort representation and forward the fence, after which
    # `_update_writability` sees an empty buffer and announces ReadyForOutput - although ordinary output is no longer
    # legal.

    def test_chunker_does_not_resume_output_after_shutdown(self) -> None:
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
