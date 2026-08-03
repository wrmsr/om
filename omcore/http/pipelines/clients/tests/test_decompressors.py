# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import dataclasses as dc
import typing as ta
import unittest
import zlib

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.flow.stub import StubIoPipelineFlowService
from .....io.pipelines.flow.types import IoPipelineFlowMessages
from .....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from .....io.pipelines.yielding import CountingIoPipelineYieldPolicy
from .....io.pipelines.yielding import NeverIoPipelineYieldPolicy
from .....io.streambufs.utils import ByteStreamBuffers
from .....lite.check import check
from ....headers import HttpHeaders
from ...compression.decompressors import IoPipelineHttpDecompressionConfig
from ...responses import IoPipelineHttpResponseAborted
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..responses import IoPipelineHttpResponseDecompressor


class CaptureReadsIoPipelineHandler(IoPipelineHandler):
    def __init__(self):
        super().__init__()

        self.messages = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        self.messages.append(msg)
        if isinstance(msg, IoPipelineMessages.FinalInput):
            ctx.feed_in(msg)


def request_read(channel: IoPipeline, capture: CaptureReadsIoPipelineHandler) -> None:
    ref = channel.find_handler(capture)
    if ref is None:
        raise AssertionError('Capture handler not in pipeline')

    with channel.enter():
        ref._context.feed_out(IoPipelineFlowMessages.ReadyForInput())  # noqa


def gzip_bytes(data: bytes) -> bytes:
    compressor = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
    return compressor.compress(data) + compressor.flush()


def run_deferred_work(channel: IoPipeline, max_steps: int = 100) -> None:
    count = 0
    while (out := channel.output.poll()) is not None:
        count += 1
        if count > max_steps:
            raise AssertionError('Infinite defer loop')
        channel.run_deferred(check.isinstance(out, IoPipelineMessages.Defer))


class TestGzipDecompressorSimple(unittest.TestCase):
    """Simple decompression tests without flow control complexity."""

    def test_passthrough_no_encoding(self):
        """Test that data passes through unchanged when no content-encoding is present."""

        handler = IoPipelineHttpResponseDecompressor()

        channel = IoPipeline.new([
            handler,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        # Head without content-encoding
        head = IoPipelineHttpResponseHead(
            status=200,
            reason='OK',
            headers=HttpHeaders({}),
        )

        # Feed messages
        channel.feed_in(head)
        channel.feed_in(IoPipelineHttpResponseBodyData(b'Hello, World!'))
        channel.feed_in(IoPipelineHttpResponseEnd())

        # Verify passthrough
        results = ibq.drain()
        self.assertEqual(len(results), 3)
        self.assertIs(results[0], head)
        self.assertEqual(check.isinstance(results[1], IoPipelineHttpResponseBodyData).data, b'Hello, World!')
        self.assertIsInstance(results[2], IoPipelineHttpResponseEnd)

    def test_simple_gzip_decompression(self):
        """Test basic gzip decompression with default config."""

        handler = IoPipelineHttpResponseDecompressor()

        channel = IoPipeline.new([
            handler,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        # Create gzipped data
        raw_data = b'Hello, World!'
        compressor = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
        compressed_data = compressor.compress(raw_data) + compressor.flush()

        # Head with gzip encoding
        head = IoPipelineHttpResponseHead(
            status=200,
            reason='OK',
            headers=HttpHeaders({'content-encoding': 'gzip'}),
        )

        # Feed messages
        channel.feed_in(head)
        channel.feed_in(IoPipelineHttpResponseBodyData(compressed_data))
        channel.feed_in(IoPipelineHttpResponseEnd())

        # Verify decompression
        results = ibq.drain()
        self.assertEqual(len(results), 3)
        self.assertIs(results[0], head)
        self.assertEqual(
            ByteStreamBuffers.to_bytes(check.isinstance(results[1], IoPipelineHttpResponseBodyData).data),
            raw_data,
        )
        self.assertIsInstance(results[2], IoPipelineHttpResponseEnd)

    def test_gzip_multiple_chunks(self):
        """Test gzip decompression with multiple body data chunks."""

        handler = IoPipelineHttpResponseDecompressor()

        channel = IoPipeline.new([
            handler,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        # Create gzipped data
        raw_data = b'This is a longer message that will be split into chunks during compression.'
        compressor = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
        compressed_data = compressor.compress(raw_data) + compressor.flush()

        # Split compressed data into chunks
        chunk_size = len(compressed_data) // 3
        chunk1 = compressed_data[:chunk_size]
        chunk2 = compressed_data[chunk_size:2 * chunk_size]
        chunk3 = compressed_data[2 * chunk_size:]

        # Head with gzip encoding
        head = IoPipelineHttpResponseHead(
            status=200,
            reason='OK',
            headers=HttpHeaders({'content-encoding': 'gzip'}),
        )

        # Feed messages
        channel.feed_in(head)
        channel.feed_in(IoPipelineHttpResponseBodyData(chunk1))
        channel.feed_in(IoPipelineHttpResponseBodyData(chunk2))
        channel.feed_in(IoPipelineHttpResponseBodyData(chunk3))
        channel.feed_in(IoPipelineHttpResponseEnd())

        # Verify decompression - collect all body data
        results = ibq.drain()
        self.assertIs(results[0], head)

        body_data_msgs = [m for m in results[1:-1] if isinstance(m, IoPipelineHttpResponseBodyData)]
        decompressed = b''.join(ByteStreamBuffers.to_bytes(m.data, strict=True) for m in body_data_msgs)

        self.assertEqual(decompressed, raw_data)
        self.assertIsInstance(results[-1], IoPipelineHttpResponseEnd)

    def test_consecutive_gzip_messages(self):
        handler = IoPipelineHttpResponseDecompressor()
        channel = IoPipeline.new([
            handler,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        expected = []
        for raw_data in (b'first', b'second'):
            compressor = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
            compressed_data = compressor.compress(raw_data) + compressor.flush()
            head = IoPipelineHttpResponseHead(
                status=200,
                reason='OK',
                headers=HttpHeaders({'content-encoding': 'gzip'}),
            )
            end = IoPipelineHttpResponseEnd()

            channel.feed_in(head)
            channel.feed_in(IoPipelineHttpResponseBodyData(compressed_data))
            channel.feed_in(end)
            expected.append((head, raw_data, end))

        messages = ibq.drain()
        for head, raw_data, end in expected:
            self.assertIs(messages.pop(0), head)
            self.assertEqual(
                ByteStreamBuffers.to_bytes(
                    check.isinstance(messages.pop(0), IoPipelineHttpResponseBodyData).data,
                ),
                raw_data,
            )
            self.assertIs(messages.pop(0), end)
        self.assertEqual(messages, [])


class TestGzipDecompressorFlow(unittest.TestCase):
    config = IoPipelineHttpDecompressionConfig(
        max_steps_per_call=2,      # Very low for testing
        max_decomp_chunk=10,       # Tiny chunks to force multiple steps
        max_out_pending=100,
        max_expansion_ratio=1000,   # High for zip bomb testing
    )

    # Enable Gzip
    head = IoPipelineHttpResponseHead(
        status=200,
        reason='OK',
        headers=HttpHeaders({'content-encoding': 'gzip'}),
    )

    def test_deferral(self):
        # Create some gzip data
        compressor = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
        # Create enough data to exceed 2 steps (2 * 10 bytes)
        raw_data = b'This is a reasonably long string that should exceed the tiny chunk limit.'
        data = compressor.compress(raw_data) + compressor.flush()

        handler = IoPipelineHttpResponseDecompressor(config=self.config)

        channel = IoPipeline.new(
            [
                handler,
                ibq := InboundQueueIoPipelineHandler(),
            ],
        )

        # 1. Feed data and FinalInput
        channel.feed_in(self.head)
        assert channel.output.drain() == []
        assert ibq.drain() == [self.head]

        channel.feed_in(IoPipelineHttpResponseBodyData(data))
        # Should have deferred because max_steps is 2 (20 bytes out max)
        dfl = check.isinstance(check.single(channel.output.drain()), IoPipelineMessages.Defer)
        # Verify FinalInput is pinned and NOT yet fed inbound
        self.assertIsNone(dfl.pinned)

        # 2. Run the deferred tasks until completion
        count = 0
        channel.run_deferred(dfl)
        while (out := channel.output.poll()) is not None:
            count += 1
            if count > 100:
                self.fail('Infinite defer loop')
            dfl = check.isinstance(out, IoPipelineMessages.Defer)
            channel.run_deferred(dfl)

        fi = IoPipelineHttpResponseEnd()
        channel.feed_in(fi)
        assert channel.output.drain() == []
        [*out_data, out_fi] = ibq.drain()

        # 3. Final Verification
        full_output = b''.join(
            ByteStreamBuffers.to_bytes(check.isinstance(m, IoPipelineHttpResponseBodyData).data, strict=True)
            for m in out_data
        )
        self.assertEqual(full_output, raw_data)
        self.assertIs(fi, out_fi)

    def test_manual_read_backpressure(self):
        raw_data = b'This response expands into several deliberately tiny output chunks.'
        compressor = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
        compressed_data = compressor.compress(raw_data) + compressor.flush()
        handler = IoPipelineHttpResponseDecompressor(
            config=dc.replace(self.config, max_steps_per_call=None),
        )
        capture = CaptureReadsIoPipelineHandler()
        channel = IoPipeline.new(
            [
                handler,
                capture,
            ],
            services=[StubIoPipelineFlowService(auto_read=False)],
        )
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(compressed_data))
        channel.feed_in(end)
        self.assertEqual(capture.messages, [self.head])

        body_parts = []
        for _ in range(100):
            start = len(capture.messages)
            request_read(channel, capture)
            delivered = capture.messages[start:]
            self.assertEqual(len(delivered), 2)
            self.assertIsInstance(delivered[1], IoPipelineFlowMessages.FlushInput)

            if isinstance(delivered[0], IoPipelineHttpResponseBodyData):
                body_parts.append(ByteStreamBuffers.to_bytes(delivered[0].data, strict=True))
            else:
                self.assertIs(delivered[0], end)
                break
        else:
            self.fail('Decompressor did not deliver End')

        self.assertEqual(b''.join(body_parts), raw_data)
        self.assertEqual(channel.output.drain(), [])

        request_read(channel, capture)
        output = channel.output.drain()
        self.assertEqual(len(output), 1)
        self.assertIsInstance(output[0], IoPipelineFlowMessages.ReadyForInput)

    def test_manual_read_preserves_final_input_order(self):
        raw_data = b'Decompressed output remains readable after the transport reaches EOF.'
        compressor = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
        compressed_data = compressor.compress(raw_data) + compressor.flush()
        handler = IoPipelineHttpResponseDecompressor(
            config=dc.replace(self.config, max_steps_per_call=None),
        )
        capture = CaptureReadsIoPipelineHandler()
        channel = IoPipeline.new(
            [
                handler,
                capture,
            ],
            services=[StubIoPipelineFlowService(auto_read=False)],
        )
        end = IoPipelineHttpResponseEnd()
        final_input = IoPipelineMessages.FinalInput()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(compressed_data))
        channel.feed_in(end)
        channel.feed_in(final_input)
        self.assertEqual(capture.messages, [self.head])

        body_parts = []
        for _ in range(100):
            start = len(capture.messages)
            request_read(channel, capture)
            delivered = capture.messages[start:]

            if isinstance(delivered[0], IoPipelineHttpResponseBodyData):
                self.assertEqual(len(delivered), 2)
                self.assertIsInstance(delivered[1], IoPipelineFlowMessages.FlushInput)
                body_parts.append(ByteStreamBuffers.to_bytes(delivered[0].data, strict=True))
            else:
                self.assertEqual(delivered, [end, IoPipelineFlowMessages.FlushInput(), final_input])
                break
        else:
            self.fail('Decompressor did not deliver End and FinalInput')

        self.assertEqual(b''.join(body_parts), raw_data)

    def test_output_writability_passthrough(self):
        capture = CaptureReadsIoPipelineHandler()
        channel = IoPipeline.new(
            [
                IoPipelineHttpResponseDecompressor(),
                capture,
            ],
            services=[StubIoPipelineFlowService(auto_read=False)],
        )
        pause = IoPipelineFlowMessages.PauseOutput()
        ready = IoPipelineFlowMessages.ReadyForOutput()

        channel.feed_in(pause, ready)

        self.assertEqual(capture.messages, [pause, ready])

    def test_zip_bomb_prevention(self):
        """Test that budget checks trigger even during deferred steps."""

        config = dc.replace(self.config, max_expansion_ratio=2)
        handler = IoPipelineHttpResponseDecompressor(config=config)

        # 10 bytes compressed -> 1000 bytes uncompressed (ratio 100)
        compressor = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
        bomb_data = compressor.compress(b'A' * 1000) + compressor.flush()

        channel = IoPipeline.new(
            [
                handler,
                ibq := InboundQueueIoPipelineHandler(),  # noqa
            ],
        )
        channel.feed_in(self.head)

        # Feeding this should eventually raise ValueError due to expansion ratio
        channel.feed_in(IoPipelineHttpResponseBodyData(bomb_data))
        count = 0
        while (out := channel.output.poll()) is not None:
            count += 1
            if count > 100:
                self.fail('Infinite defer loop')
            dfl = check.isinstance(out, IoPipelineMessages.Defer)
            channel.run_deferred(dfl)

        [out_head, *out_data, out_err] = ibq.drain()
        self.assertIs(self.head, out_head)
        err = check.isinstance(out_err, IoPipelineMessages.Error)
        self.assertIsInstance(err.exc, ValueError)
        self.assertIn('expansion ratio exceeds limit', repr(err.exc))

    # def test_manual_read_backpressure_with_defer(self):
    #     """Test that manual read (auto_read=False) correctly stalls the defer loop."""
    #
    #     self.ctx.services[IoPipelineFlow] = StubIoPipelineFlow(auto_read=False)
    #
    #     compressor = zlib.compressobj(wbits=16+zlib.MAX_WBITS)
    #     data = compressor.compress(b"Some data that will be buffered") + compressor.flush()
    #
    #     # 1. Feed data - should decompress one chunk and stop because _read_requested is False
    #     self.handler.inbound(self.ctx, data)
    #
    #     # No data should have been fed in yet because no ReadyForInput was received
    #     self.assertEqual(len([m for m in self.ctx.inbound_results if isinstance(m, bytes)]), 0)
    #
    #     # 2. Send ReadyForInput
    #     self.handler.outbound(self.ctx, IoPipelineFlowMessages.ReadyForInput())
    #
    #     # Now one chunk should be present
    #     self.assertGreater(len(self.ctx.inbound_results), 0)


class TestGzipDecompressorStreamIntegrity(unittest.TestCase):
    head = IoPipelineHttpResponseHead(
        status=200,
        reason='OK',
        headers=HttpHeaders({'content-encoding': 'gzip'}),
    )

    def _new(self, config=IoPipelineHttpDecompressionConfig.DEFAULT):
        channel = IoPipeline.new([
            IoPipelineHttpResponseDecompressor(config=config),
            ibq := InboundQueueIoPipelineHandler(),
        ])
        return channel, ibq

    def _body_bytes(self, msgs) -> bytes:
        return b''.join(
            ByteStreamBuffers.to_bytes(m.data, strict=True)
            for m in msgs
            if isinstance(m, IoPipelineHttpResponseBodyData)
        )

    def test_multi_member_gzip(self):
        # Concatenated gzip members are valid (RFC 1952 §2.2) and are what urllib3 and browsers accept.
        channel, ibq = self._new()
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(gzip_bytes(b'first-member-') + gzip_bytes(b'second-member')))
        channel.feed_in(end)

        messages = ibq.drain()
        self.assertIs(messages[0], self.head)
        self.assertIs(messages[-1], end)
        self.assertEqual(self._body_bytes(messages), b'first-member-second-member')

    def test_multi_member_gzip_split_across_body_data(self):
        channel, ibq = self._new()
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(gzip_bytes(b'first-member-')))
        channel.feed_in(IoPipelineHttpResponseBodyData(gzip_bytes(b'second-member')))
        channel.feed_in(end)

        messages = ibq.drain()
        self.assertIs(messages[0], self.head)
        self.assertIs(messages[-1], end)
        self.assertEqual(self._body_bytes(messages), b'first-member-second-member')

    def test_multi_member_gzip_with_deferral(self):
        config = dc.replace(
            IoPipelineHttpDecompressionConfig.DEFAULT,
            max_steps_per_call=2,
            max_decomp_chunk=8,
        )
        channel, ibq = self._new(config)
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(gzip_bytes(b'first-member-') + gzip_bytes(b'second-member')))
        run_deferred_work(channel)
        channel.feed_in(end)
        run_deferred_work(channel)

        messages = ibq.drain()
        self.assertIs(messages[0], self.head)
        self.assertIs(messages[-1], end)
        self.assertEqual(self._body_bytes(messages), b'first-member-second-member')

    def test_truncated_gzip_aborts(self):
        # zlib's flush() does not fail on an incomplete stream, and gzip's crc/length check lives in the trailer that
        # was never received - nothing else would notice.
        raw_data = b'a truncated body must not look like a complete one' * 8
        compressed_data = gzip_bytes(raw_data)
        channel, ibq = self._new()
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(compressed_data[:len(compressed_data) // 2]))
        channel.feed_in(end)

        messages = ibq.drain()
        self.assertIs(messages[0], self.head)
        self.assertNotIn(end, messages)
        aborted = check.isinstance(messages[-1], IoPipelineHttpResponseAborted)
        self.assertIn('truncated', aborted.reason_str)

    def test_truncated_gzip_aborts_with_deferral(self):
        raw_data = b'a truncated body must not look like a complete one' * 8
        compressed_data = gzip_bytes(raw_data)
        config = dc.replace(
            IoPipelineHttpDecompressionConfig.DEFAULT,
            max_steps_per_call=2,
            max_decomp_chunk=8,
        )
        channel, ibq = self._new(config)
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(compressed_data[:len(compressed_data) // 2]))
        run_deferred_work(channel)
        channel.feed_in(end)
        run_deferred_work(channel)

        messages = ibq.drain()
        self.assertNotIn(end, messages)
        aborted = check.isinstance(messages[-1], IoPipelineHttpResponseAborted)
        self.assertIn('truncated', aborted.reason_str)

    def test_empty_body_is_not_truncated(self):
        # An encoded message with no body at all (304, HEAD, ...) is not a truncated stream.
        channel, ibq = self._new()
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(end)

        self.assertEqual(ibq.drain(), [self.head, end])

    def test_non_positive_max_steps_per_call_rejected(self):
        # A zero step budget defers before ever taking a step - an infinite defer loop.
        with self.assertRaises(ValueError):
            IoPipelineHttpDecompressionConfig(max_steps_per_call=0)
        with self.assertRaises(ValueError):
            IoPipelineHttpDecompressionConfig(max_steps_per_call=-1)

    def test_unknown_trailing_data_mode_rejected(self):
        with self.assertRaises(ValueError):
            IoPipelineHttpDecompressionConfig(trailing_data='barf')  # type: ignore[arg-type]

    def test_trailing_junk_surfaces_by_default(self):
        # Default 'member' cannot tell a following member from junk, and says so rather than silently truncating.
        channel, ibq = self._new()
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(gzip_bytes(b'first-member-') + b'JUNKJUNKJUNK'))
        channel.feed_in(end)

        messages = ibq.drain()
        self.assertNotIn(end, messages)
        check.isinstance(messages[-1], IoPipelineHttpResponseAborted)

    _IGNORE_TRAILING: ta.ClassVar[IoPipelineHttpDecompressionConfig] = dc.replace(
        IoPipelineHttpDecompressionConfig.DEFAULT,
        trailing_data='ignore',
    )

    def test_ignore_trailing_data_stops_at_first_member(self):
        # urllib3's behavior: stop at the first complete member and drop whatever follows.
        channel, ibq = self._new(self._IGNORE_TRAILING)
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(gzip_bytes(b'first-member-') + gzip_bytes(b'second-member')))
        channel.feed_in(end)

        messages = ibq.drain()
        self.assertIs(messages[-1], end)
        self.assertEqual(self._body_bytes(messages), b'first-member-')

    def test_ignore_trailing_data_tolerates_junk(self):
        channel, ibq = self._new(self._IGNORE_TRAILING)
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(gzip_bytes(b'first-member-') + b'JUNKJUNKJUNK'))
        channel.feed_in(end)

        messages = ibq.drain()
        self.assertIs(messages[-1], end)
        self.assertEqual(self._body_bytes(messages), b'first-member-')

    def test_ignore_trailing_data_still_detects_truncation(self):
        # Leniency about what follows a *complete* stream must not extend to an incomplete one.
        compressed_data = gzip_bytes(b'a truncated body must not look like a complete one' * 8)
        channel, ibq = self._new(self._IGNORE_TRAILING)
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(compressed_data[:len(compressed_data) // 2]))
        channel.feed_in(end)

        messages = ibq.drain()
        self.assertNotIn(end, messages)
        aborted = check.isinstance(messages[-1], IoPipelineHttpResponseAborted)
        self.assertIn('truncated', aborted.reason_str)


class TestGzipDecompressorAutoReadFinalInput(unittest.TestCase):
    head = IoPipelineHttpResponseHead(
        status=200,
        reason='OK',
        headers=HttpHeaders({'content-encoding': 'gzip'}),
    )

    def test_auto_read_releases_parked_final_input(self):
        # In auto-read the parked FinalInput has had its must-propagate tracking disarmed, so losing it is silent -
        # and anything keyed on connection-inactive then hangs.
        raw_data = b'the connection eof must survive a cpu-bounded deferred decompression'
        config = IoPipelineHttpDecompressionConfig(
            max_steps_per_call=2,
            max_decomp_chunk=10,
            max_expansion_ratio=1000,
        )
        handler = IoPipelineHttpResponseDecompressor(config=config)
        channel = IoPipeline.new([
            handler,
            ibq := InboundQueueIoPipelineHandler(),
        ])
        end = IoPipelineHttpResponseEnd()
        final_input = IoPipelineMessages.FinalInput()

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(gzip_bytes(raw_data)))
        channel.feed_in(end)
        channel.feed_in(final_input)
        run_deferred_work(channel)

        messages = ibq.drain()
        self.assertIs(messages[0], self.head)
        self.assertIn(end, messages)
        self.assertIn(final_input, messages)
        self.assertIs(messages[-1], final_input)
        self.assertIsNone(handler._pending_final_input)

        body = b''.join(
            ByteStreamBuffers.to_bytes(m.data, strict=True)
            for m in messages
            if isinstance(m, IoPipelineHttpResponseBodyData)
        )
        self.assertEqual(body, raw_data)


##


class TestGzipDecompressorYieldPolicy(unittest.TestCase):
    head = IoPipelineHttpResponseHead(
        status=200,
        reason='OK',
        headers=HttpHeaders({'content-encoding': 'gzip'}),
    )

    def _run(self, config) -> ta.Tuple[bytes, int]:
        """Returns the decompressed body and the number of driver turns it took."""

        channel = IoPipeline.new([
            IoPipelineHttpResponseDecompressor(config=config),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        channel.feed_in(self.head)
        channel.feed_in(IoPipelineHttpResponseBodyData(gzip_bytes(b'x' * 4096)))
        channel.feed_in(IoPipelineHttpResponseEnd())

        turns = 0
        while True:
            deferred = [m for m in channel.output.drain() if isinstance(m, IoPipelineMessages.Defer)]
            if not deferred:
                break
            turns += 1
            for dfl in deferred:
                channel.run_deferred(dfl)

        body = b''.join(
            ByteStreamBuffers.to_bytes(m.data, strict=True)
            for m in ibq.drain()
            if isinstance(m, IoPipelineHttpResponseBodyData)
        )
        return body, turns

    _CONFIG: ta.ClassVar[IoPipelineHttpDecompressionConfig] = dc.replace(
        IoPipelineHttpDecompressionConfig.DEFAULT,
        max_decomp_chunk=64,
    )

    def test_step_count_and_policy_forms_are_equivalent(self) -> None:
        # max_steps_per_call is sugar for a counting policy - the two must behave identically.
        sugar = self._run(dc.replace(self._CONFIG, max_steps_per_call=2))
        policy = self._run(dc.replace(self._CONFIG, yield_policy=CountingIoPipelineYieldPolicy(2)))

        self.assertEqual(sugar, policy)
        self.assertEqual(sugar[0], b'x' * 4096)
        self.assertGreater(sugar[1], 0)

    def test_default_is_unbounded(self) -> None:
        body, turns = self._run(self._CONFIG)

        self.assertEqual(body, b'x' * 4096)
        self.assertEqual(turns, 0)

    def test_explicit_never_policy_matches_the_default(self) -> None:
        self.assertEqual(
            self._run(dc.replace(self._CONFIG, yield_policy=NeverIoPipelineYieldPolicy())),
            self._run(self._CONFIG),
        )

    def test_smaller_budget_takes_more_turns(self) -> None:
        _, few = self._run(dc.replace(self._CONFIG, max_steps_per_call=1))
        _, many = self._run(dc.replace(self._CONFIG, max_steps_per_call=4))

        self.assertGreater(few, many)

    def test_both_forms_together_rejected(self) -> None:
        with self.assertRaises(ValueError):
            IoPipelineHttpDecompressionConfig(
                max_steps_per_call=2,
                yield_policy=CountingIoPipelineYieldPolicy(2),
            )
