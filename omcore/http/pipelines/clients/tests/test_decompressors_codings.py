# ruff: noqa: PT009 UP006 UP007 UP045
# @om-lite
import dataclasses as dc
import typing as ta
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from .....io.streambufs.utils import ByteStreamBuffers
from .....lite.check import check
from ....headers import HttpHeaders
from ...compression.codings import BrotliIoPiplineHttpCompressorCoding
from ...compression.codings import BrotliIoPiplineHttpDecompressorCoding
from ...compression.codings import IoPipelineHttpDecompressionError
from ...compression.codings import ZlibIoPiplineHttpCompressorCoding
from ...compression.codings import ZlibIoPiplineHttpDecompressorCoding
from ...compression.codings import ZstdIoPiplineHttpCompressorCoding
from ...compression.codings import ZstdIoPiplineHttpDecompressorCoding
from ...compression.decompressors import IoPipelineHttpDecompressionConfig
from ...responses import IoPipelineHttpResponseAborted
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..responses import IoPipelineHttpResponseDecompressor


RAW = b''.join(b'%d:' % i for i in range(6000))


def run_deferred_work(channel: IoPipeline, max_steps: int = 10000) -> None:
    count = 0
    while (out := channel.output.poll()) is not None:
        count += 1
        if count > max_steps:
            raise AssertionError('Infinite defer loop')
        channel.run_deferred(check.isinstance(out, IoPipelineMessages.Defer))


class _CodingDecompressorTests:
    """Run identically against every coding: the handler's behavior must not depend on which one is behind it."""

    coding_name: ta.Any
    compressor: ta.Any
    decompressor: ta.Any

    def _compress(self, data: bytes) -> bytes:
        c = self.compressor()
        return bytes(c.compress(data) or b'') + bytes(c.finish() or b'')

    def _head(self) -> IoPipelineHttpResponseHead:
        return IoPipelineHttpResponseHead(
            status=200,
            reason='OK',
            headers=HttpHeaders({'content-encoding': self.coding_name}),
        )

    def _new(self, config=IoPipelineHttpDecompressionConfig.DEFAULT):
        channel = IoPipeline.new([
            IoPipelineHttpResponseDecompressor(config=config),
            ibq := InboundQueueIoPipelineHandler(),
        ])
        return channel, ibq

    def _run(self, channel, ibq, *chunks: bytes) -> ta.Tuple[IoPipelineHttpResponseHead, IoPipelineHttpResponseEnd, ta.List[ta.Any]]:  # noqa
        head = self._head()
        end = IoPipelineHttpResponseEnd()

        channel.feed_in(head)
        for chunk in chunks:
            channel.feed_in(IoPipelineHttpResponseBodyData(chunk))
            run_deferred_work(channel)
        channel.feed_in(end)
        run_deferred_work(channel)

        return head, end, ibq.drain()

    def _body(self, messages) -> bytes:
        return b''.join(
            ByteStreamBuffers.to_bytes(m.data, strict=True)
            for m in messages
            if isinstance(m, IoPipelineHttpResponseBodyData)
        )

    def _assert_complete(self, head, end, messages, raw: bytes) -> None:
        assert messages[0] is head
        assert messages[-1] is end
        assert self._body(messages) == raw
        assert not any(isinstance(m, IoPipelineMessages.Error) for m in messages)

    def _assert_aborted(self, head, end, messages) -> IoPipelineHttpResponseAborted:
        assert messages[0] is head
        assert end not in messages
        assert not any(isinstance(m, IoPipelineMessages.Error) for m in messages)
        return check.isinstance(messages[-1], IoPipelineHttpResponseAborted)

    def test_roundtrip(self):
        channel, ibq = self._new()
        head, end, messages = self._run(channel, ibq, self._compress(RAW))
        self._assert_complete(head, end, messages, RAW)

    def test_roundtrip_small_chunks_with_deferral(self):
        config = dc.replace(
            IoPipelineHttpDecompressionConfig.DEFAULT,
            max_decomp_chunk=100,
            max_steps_per_call=3,
        )
        data = self._compress(RAW)
        channel, ibq = self._new(config)
        head, end, messages = self._run(channel, ibq, *(data[i:i + 7] for i in range(0, len(data), 7)))
        self._assert_complete(head, end, messages, RAW)

        # Every coding must honor the chunk limit exactly, soft limits of its own notwithstanding.
        assert all(len(m.data) <= 100 for m in messages if isinstance(m, IoPipelineHttpResponseBodyData))

    def test_empty_body(self):
        channel, ibq = self._new()
        head, end, messages = self._run(channel, ibq)
        assert messages == [head, end]

    def test_consecutive_messages(self):
        channel, ibq = self._new()
        for raw in (b'first', b'second', RAW):
            head, end, messages = self._run(channel, ibq, self._compress(raw))
            self._assert_complete(head, end, messages, raw)

    def test_truncated_aborts(self):
        data = self._compress(RAW)
        channel, ibq = self._new()
        head, end, messages = self._run(channel, ibq, data[:len(data) // 2])
        aborted = self._assert_aborted(head, end, messages)
        assert 'truncated' in aborted.reason_str

    def test_junk_aborts(self):
        channel, ibq = self._new()
        head, end, messages = self._run(channel, ibq, b'JUNK' * 8)
        aborted = self._assert_aborted(head, end, messages)
        assert isinstance(aborted.reason, IoPipelineHttpDecompressionError)

        # And the stage is clean afterwards.
        head, end, messages = self._run(channel, ibq, self._compress(b'again'))
        self._assert_complete(head, end, messages, b'again')

    def test_trailing_junk_aborts(self):
        channel, ibq = self._new()
        head, end, messages = self._run(channel, ibq, self._compress(b'x' * 100) + b'JUNK' * 8)
        self._assert_aborted(head, end, messages)

    def test_trailing_junk_in_later_chunk_aborts(self):
        channel, ibq = self._new()
        head, end, messages = self._run(channel, ibq, self._compress(b'x' * 100), b'JUNK' * 8)
        aborted = self._assert_aborted(head, end, messages)
        assert 'after end of compressed stream' in aborted.reason_str


class TestGzipDecompressor(_CodingDecompressorTests, unittest.TestCase):
    coding_name = 'gzip'
    compressor = ZlibIoPiplineHttpCompressorCoding
    decompressor = ZlibIoPiplineHttpDecompressorCoding

    def test_concatenated_members(self):
        channel, ibq = self._new()
        head, end, messages = self._run(channel, ibq, self._compress(b'first-') + self._compress(b'second'))
        self._assert_complete(head, end, messages, b'first-second')


@unittest.skipUnless(BrotliIoPiplineHttpDecompressorCoding.is_available(), 'brotli not available')
class TestBrotliDecompressor(_CodingDecompressorTests, unittest.TestCase):
    coding_name = 'br'
    compressor = BrotliIoPiplineHttpCompressorCoding
    decompressor = BrotliIoPiplineHttpDecompressorCoding


@unittest.skipUnless(ZstdIoPiplineHttpDecompressorCoding.is_available(), 'compression.zstd not available')
class TestZstdDecompressor(_CodingDecompressorTests, unittest.TestCase):
    coding_name = 'zstd'
    compressor = ZstdIoPiplineHttpCompressorCoding
    decompressor = ZstdIoPiplineHttpDecompressorCoding

    def test_concatenated_frames(self):
        channel, ibq = self._new()
        head, end, messages = self._run(channel, ibq, self._compress(b'first-') + self._compress(b'second'))
        self._assert_complete(head, end, messages, b'first-second')
