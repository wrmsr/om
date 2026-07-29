# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import gc
import unittest
import weakref

from ....io.pipelines.core import IoPipeline
from ....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ..servers.requests import IoPipelineHttpRequestDecoder
from ..servers.responses import IoPipelineHttpResponseEncoder


class TestHttpPipelineReferenceOwnership(unittest.TestCase):
    def test_request_pipeline_does_not_require_cyclic_gc(self) -> None:
        def make_refs():
            decoder = IoPipelineHttpRequestDecoder()
            encoder = IoPipelineHttpResponseEncoder()
            queue = InboundQueueIoPipelineHandler()
            pipeline = IoPipeline.new([decoder, encoder, queue])

            pipeline.feed_in(b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n')
            head, _ = queue.drain()
            single = head.headers.single
            lower = head.headers.lower

            return (
                weakref.ref(pipeline),
                weakref.ref(decoder),
                weakref.ref(encoder),
                weakref.ref(head.headers),
                weakref.ref(single),
                weakref.ref(lower),
            )

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            refs = make_refs()
            self.assertTrue(all(ref() is None for ref in refs))
        finally:
            if was_enabled:
                gc.enable()
