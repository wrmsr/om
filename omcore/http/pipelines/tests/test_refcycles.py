# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import gc
import ssl
import typing as ta
import unittest
import weakref
import zlib

from ....io.pipelines.core import IoPipeline
from ....io.pipelines.core import IoPipelineHandler
from ....io.pipelines.core import IoPipelineHandlerContext
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ....io.pipelines.ssl.handlers import SslIoPipelineHandler
from ...headers import HttpHeaders
from ...versions import HttpVersions
from ..requests import IoPipelineHttpRequestBodyData
from ..requests import IoPipelineHttpRequestHead
from ..responses import IoPipelineHttpResponseBodyData
from ..responses import IoPipelineHttpResponseHead
from ..servers.requests import IoPipelineHttpRequestDecoder
from ..servers.requests import IoPipelineHttpRequestDecompressor
from ..servers.responses import IoPipelineHttpResponseCompressor
from ..servers.responses import IoPipelineHttpResponseEncoder


_EMIT_COMPRESSED_RESPONSE = object()


class _CompressionEndpointIoPipelineHandler(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _EMIT_COMPRESSED_RESPONSE:
            ctx.feed_out(IoPipelineHttpResponseHead(
                status=200,
                reason='OK',
                version=HttpVersions.HTTP_1_1,
                headers=HttpHeaders([('Content-Encoding', 'gzip')]),
            ))
            ctx.feed_out(IoPipelineHttpResponseBodyData(b'response still in progress'))

        elif isinstance(msg, IoPipelineMessages.MustPropagate):
            ctx.feed_in(msg)


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

    def test_active_compression_pipeline_does_not_require_cyclic_gc(self) -> None:
        def make_refs():
            decompressor = IoPipelineHttpRequestDecompressor()
            compressor = IoPipelineHttpResponseCompressor()
            pipeline = IoPipeline.new([
                decompressor,
                compressor,
                _CompressionEndpointIoPipelineHandler(),
            ])

            z = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
            compressed = z.compress(b'request still in progress') + z.flush()
            pipeline.feed_in(
                IoPipelineHttpRequestHead(
                    method='POST',
                    target='/',
                    version=HttpVersions.HTTP_1_1,
                    headers=HttpHeaders([('Content-Encoding', 'gzip')]),
                ),
                IoPipelineHttpRequestBodyData(compressed),
                _EMIT_COMPRESSED_RESPONSE,
            )

            active_decompressor = decompressor._decompressor
            active_compressor = compressor._compressor
            self.assertIsNotNone(active_decompressor)
            self.assertIsNotNone(active_compressor)
            return (
                weakref.ref(pipeline),
                weakref.ref(decompressor),
                weakref.ref(compressor),
                weakref.ref(active_decompressor),
                weakref.ref(active_compressor),
            )

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            refs = make_refs()
            self.assertTrue(all(ref() is None for ref in refs))
        finally:
            if was_enabled:
                gc.enable()

    def test_active_tls_pipeline_does_not_require_cyclic_gc(self) -> None:
        def make_refs():
            ssl_context = ssl.create_default_context()
            tls = SslIoPipelineHandler(
                ssl_context,
                server_side=False,
                server_hostname='localhost',
            )
            pipeline = IoPipeline.new(
                [tls],
                IoPipeline.Config(inbound_terminal='drop'),
            )
            pipeline.feed_initial_input()

            self.assertIs(tls.state, SslIoPipelineHandler.State.HANDSHAKE)
            return (
                weakref.ref(pipeline),
                weakref.ref(tls),
                weakref.ref(ssl_context),
                weakref.ref(tls._ssl_obj),
            )

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            refs = make_refs()
            self.assertTrue(all(ref() is None for ref in refs))
        finally:
            if was_enabled:
                gc.enable()
