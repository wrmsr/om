# @om-lite
import unittest

from ...bytes.buffers import OutboundBytesBufferIoPipelineHandler
from ...bytes.decoders import DelimiterFrameDecoderIoPipelineHandler
from ...bytes.decoders import UnicodeDecoderIoPipelineHandler
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineMessages
from ...drivers.pure import PureIoPipelineDriver
from ...flow.stub import StubIoPipelineFlowService
from ..flatmap import FlatMapIoPipelineHandlerFns
from ..flatmap import FlatMapIoPipelineHandlers
from ..flatmap import InboundFlatMapIoPipelineHandler
from ..flatmap import OutboundFlatMapIoPipelineHandler
from ..fns import IoPipelineHandlerFns


##


class _CloseResponse(IoPipelineHandler):
    def __init__(self):
        super().__init__()

        self.shutdown = IoPipelineMessages.ShutdownOutput()
        self.final = IoPipelineMessages.FinalOutput()

    def inbound(self, ctx, msg):
        ctx.feed_in(msg)
        if isinstance(msg, IoPipelineMessages.FinalInput):
            ctx.feed_out(self.shutdown)
            ctx.feed_out(self.final)


class TestHandlerComposition(unittest.TestCase):
    def test_fragmented_line_request_through_filters_maps_and_half_close(self):
        close = _CloseResponse()
        discarded = []
        driver = PureIoPipelineDriver(IoPipeline.Spec(
            [
                OutboundBytesBufferIoPipelineHandler(OutboundBytesBufferIoPipelineHandler.Config(
                    flush_threshold=None,
                )),
                DelimiterFrameDecoderIoPipelineHandler([b'\r\n', b'\n']),
                UnicodeDecoderIoPipelineHandler(),
                InboundFlatMapIoPipelineHandler(FlatMapIoPipelineHandlerFns.filter_type(
                    str,
                    FlatMapIoPipelineHandlerFns.compose(
                        lambda ctx, msg: msg.split(','),
                        FlatMapIoPipelineHandlerFns.map(IoPipelineHandlerFns.no_context(str.upper)),
                    ),
                )),
                FlatMapIoPipelineHandlers.apply_and_drop(
                    'inbound',
                    lambda ctx, msg: discarded.append(msg),
                    filter_type=str,
                    filter=IoPipelineHandlerFns.no_context(lambda msg: msg.startswith('#')),
                ),
                OutboundFlatMapIoPipelineHandler(FlatMapIoPipelineHandlerFns.filter_type(
                    str,
                    FlatMapIoPipelineHandlerFns.map(lambda ctx, msg: (msg + '\n').encode('utf-8')),
                )),
                FlatMapIoPipelineHandlers.feed_out_and_drop(filter_type=str),
                close,
            ],
            services=[StubIoPipelineFlowService()],
        ), PureIoPipelineDriver.Config(read_chunk_size=1, read_batch_max_bytes=1))
        try:
            # Splits both CRLF and the multi-byte UTF-8 character across transport reads.
            driver.feed_input('one,two\r\n#skip\nsnowman ☃'.encode())
            driver.feed_eof()
            self.assertEqual(driver.loop_until_done(), 'ONE\nTWO\nSNOWMAN ☃\n'.encode())
            self.assertEqual(discarded, ['#SKIP'])
            self.assertTrue(close.shutdown.is_succeeded())
            self.assertTrue(close.final.is_succeeded())
        finally:
            driver.close()
