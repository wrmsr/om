# ruff: noqa: PT009 PT027 UP006 UP045
# @om-lite
"""
Executable, tutorial-style examples of real-world streambufs usage.

Unlike the other test modules - which map one-to-one to impl modules and hold their pedantically simple unit tests,
rare edge cases, and regressions - this module walks through the high-level usecases the package exists to serve, in
roughly increasing sophistication. Read it top to bottom; comments are intentionally chattier than usual because this
file doubles as a tutorial.

The single most important lesson lives in chapter 02: `peek()` / `segments()` / `coalesce()` return *live views* of
buffer internals, valid only until the next buffer mutation. `split_to()` returns *stable* views, valid forever. Mixing
those two lifetimes up is the classic landmine of every zero-copy buffer API, and this package is designed to make the
mistake loud (BufferError) or harmless (internal copy fallbacks) rather than silently corrupting - but it cannot make
it free.
"""
import typing as ta
import unittest

from ..direct import DirectByteStreamBuffer
from ..errors import BufferTooLargeByteStreamBufferError
from ..errors import FrameTooLargeByteStreamBufferError
from ..errors import NeedMoreDataByteStreamBufferError
from ..errors import OutstandingReserveByteStreamBufferError
from ..framing import LengthFieldByteStreamFrameDecoder
from ..framing import LongestMatchDelimiterByteStreamFrameDecoder
from ..linear import LinearByteStreamBuffer
from ..reading import ByteStreamBufferReader
from ..scanning import ScanningByteStreamBuffer
from ..segmented import SegmentedByteStreamBuffer
from ..utils import ByteStreamBuffers


def _drain(buf) -> bytes:
    """Tutorial helper: the readable contents as bytes, without consuming (segments() copies happen here, in test)."""

    return b''.join(bytes(mv) for mv in buf.segments())


class TestExamples01Basics(unittest.TestCase):
    """Write bytes in, search, split a frame off the front - the core consumption loop."""

    def test_basics(self) -> None:
        buf = SegmentedByteStreamBuffer(chunk_size=4096)
        buf.write(b'GET / HTTP/1.1\r\n')

        # Emptiness is always asked via len() - bool() is deliberately forbidden, because `if buf:` reads as
        # ambiguous ("non-empty? not-None? writable?") in I/O code and has caused real bugs elsewhere.
        self.assertEqual(len(buf), 16)
        with self.assertRaises(TypeError):
            bool(buf)

        # find() is 'stream-correct': it behaves like bytes.find over the logical concatenation of everything
        # buffered, no matter how the bytes were chunked on the way in.
        i = buf.find(b'\r\n')
        self.assertEqual(i, 14)

        # split_to(n) consumes the first n bytes and hands back a *stable* view of them; advance(n) consumes and
        # discards. Split the line off, then discard its delimiter.
        line = buf.split_to(i)
        buf.advance(2)

        self.assertEqual(line.tobytes(), b'GET / HTTP/1.1')
        self.assertEqual(len(buf), 0)
        self.assertEqual(_drain(buf), b'')


class TestExamples02EphemeralViews(unittest.TestCase):
    """
    THE landmine chapter: peek()/segments()/coalesce() views are live and ephemeral.

    They alias the buffer's internal storage - that is their entire point - so they are only valid until the next
    mutating call. Copy what you need (`bytes(mv)`) before mutating, or use split_to() for anything long-lived.
    """

    def test_holding_a_peek_across_a_write_is_loud(self) -> None:
        # LinearByteStreamBuffer stores everything in one bytearray. An exported memoryview *pins* a bytearray:
        # python itself refuses to resize pinned storage. So writing while a peek() view is alive doesn't corrupt
        # anything - it blows up, which is the best available failure mode.
        buf = LinearByteStreamBuffer()
        buf.write(b'hello')

        mv = buf.peek()
        self.assertEqual(bytes(mv), b'hello')

        with self.assertRaises(BufferError):
            buf.write(b' world')

        # The remedy: materialize a copy at the moment you need one, and release the view before mutating again.
        # (Dropping the last reference - `del mv` - works too; release() is just explicit.)
        copied = bytes(mv)
        mv.release()

        buf.write(b' world')
        self.assertEqual(buf.peek().tobytes(), b'hello world')
        self.assertEqual(copied, b'hello')

    def test_segmented_degrades_gracefully_but_pins_memory(self) -> None:
        # SegmentedByteStreamBuffer is built to avoid resizing storage that might be exported: chunked writes go into
        # fixed-capacity chunks via slice assignment, and internal reshaping falls back to copying when it finds
        # storage pinned. So the same mistake doesn't raise here - but the pinned chunk cannot be reclaimed or
        # shrunk while the view lives, so it is still a mistake, just a quieter one.
        buf = SegmentedByteStreamBuffer(chunk_size=8)
        buf.write(b'abc')

        mv = buf.peek()  # aliases the active chunk's bytearray

        buf.write(b'defghi')  # overflows the chunk: flush wants to shrink it, finds it pinned, copies instead

        self.assertEqual(_drain(buf), b'abcdefghi')
        self.assertEqual(bytes(mv), b'abc')  # old view intact - and holding a whole chunk hostage

    def test_writing_a_reused_scratch_bytearray_aliases_it(self) -> None:
        # The landmine also points the other way: in unchunked mode (chunk_size=0), write() stores bytes-like inputs
        # *by reference* - zero-copy by design. Feeding it a scratch bytearray you then overwrite (the classic
        # recv-into-scratch I/O loop) silently rewrites what you thought you had buffered:
        buf = SegmentedByteStreamBuffer()

        scratch = bytearray(4)
        scratch[:] = b'AAAA'
        buf.write(scratch)
        scratch[:] = b'BBBB'
        buf.write(scratch)

        # Both segments are the *same object* - the first write's bytes are gone:
        self.assertEqual(_drain(buf), b'BBBBBBBB')

        # Remedy 1: copy at the ownership boundary.
        buf2 = SegmentedByteStreamBuffer()
        scratch[:] = b'AAAA'
        buf2.write(bytes(scratch))
        scratch[:] = b'BBBB'
        buf2.write(bytes(scratch))
        self.assertEqual(_drain(buf2), b'AAAABBBB')

        # Remedy 2: chunked mode copies small writes into its own chunk storage anyway.
        buf3 = SegmentedByteStreamBuffer(chunk_size=64)
        scratch[:] = b'AAAA'
        buf3.write(scratch)
        scratch[:] = b'BBBB'
        buf3.write(scratch)
        self.assertEqual(_drain(buf3), b'AAAABBBB')

        # (Remedy 3, the real one: don't reuse the scratch buffer - or better, use reserve()/commit() and skip the
        # scratch buffer entirely. See chapter 06.)


class TestExamples03StableViews(unittest.TestCase):
    """split_to() views are the durable counterpart: valid forever, no matter what the buffer does next."""

    def test_split_views_survive_everything(self) -> None:
        buf = SegmentedByteStreamBuffer(chunk_size=8)
        buf.write(b'frame-1|frame-2|')

        f1 = buf.split_to(7)
        buf.advance(1)  # the '|'
        f2 = buf.split_to(7)
        buf.advance(1)

        # Now abuse the buffer: write, coalesce (which reshapes internal segments), split, drain.
        buf.write(b'x' * 100)
        buf.coalesce(50)
        buf.split_to(60)
        buf.advance(len(buf))

        # The earlier views are untouched - hold them as long as you like, hand them to other components, etc.
        self.assertEqual(f1.tobytes(), b'frame-1')
        self.assertEqual(f2.tobytes(), b'frame-2')


class TestExamples04ConnectionBufferReuse(unittest.TestCase):
    """
    One long-lived buffer per connection, reused across messages - the keepalive pattern.

    Leftover bytes after one message are simply the prefix of the next; nothing is ever re-buffered or shifted. The
    key discipline: *size-check before consuming*. Only start split_to()/advance() calls for a message once the whole
    message is known to be buffered, so a partial message is never half-consumed.
    """

    @staticmethod
    def _try_read_message(buf) -> ta.Optional[ta.Tuple[bytes, bytes]]:
        # Toy protocol: head, b'\r\n\r\n', fixed 4-byte body.
        if (i := buf.find(b'\r\n\r\n')) < 0:
            return None
        if len(buf) < i + 4 + 4:
            return None  # head complete but body still in flight - consume nothing, retry after the next read

        head = buf.split_to(i)
        buf.advance(4)
        body = buf.split_to(4)
        return (bytes(head.tobytes()), bytes(body.tobytes()))

    def test_pipelined_messages_one_buffer(self) -> None:
        req1 = b'GET /a\r\n\r\n0001'
        req2 = b'GET /b\r\n\r\n0002'
        req3 = b'GET /c\r\n\r\n0003'

        buf = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(chunk_size=4096))

        # One network read delivers two full pipelined messages plus a torn third (its head is complete, two bytes
        # of its body are still in flight).
        buf.write(req1 + req2 + req3[:12])

        msgs = []
        while (m := self._try_read_message(buf)) is not None:
            msgs.append(m)
        self.assertEqual(msgs, [(b'GET /a', b'0001'), (b'GET /b', b'0002')])
        self.assertEqual(len(buf), 12)  # the torn message waits, unconsumed

        # The next read completes it - same buffer, no copying or resetting between messages.
        buf.write(req3[12:])
        self.assertEqual(self._try_read_message(buf), (b'GET /c', b'0003'))
        self.assertEqual(len(buf), 0)


class TestExamples05TrickleFraming(unittest.TestCase):
    """
    Delimiter framing under adversarial arrival: one byte at a time, with overlapping delimiters.

    ScanningByteStreamBuffer caches negative search progress so the repeated write-then-look loop stays linear, and
    the longest-match framer refuses to emit a frame while a longer delimiter is still possible.
    """

    def test_byte_at_a_time_with_overlapping_delims(self) -> None:
        buf = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(chunk_size=1024))
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\r', b'\r\n'])

        got: ta.List[ta.Any] = []

        data = b'PING\r'
        for i in range(len(data)):
            buf.write(data[i:i + 1])
            got.extend(f.decode(buf, include_delims=True))

        # b'\r' has matched - but b'\r\n' is still possible, so nothing is emitted yet.
        self.assertEqual(got, [])

        buf.write(b'\n')
        got.extend(f.decode(buf, include_delims=True))
        self.assertEqual([(v.tobytes(), d) for v, d in got], [(b'PING', b'\r\n')])

        # A following byte that *disproves* the longer delimiter releases the frame with the short one.
        buf.write(b'PONG\rX')
        out = f.decode(buf, include_delims=True)
        self.assertEqual([(v.tobytes(), d) for v, d in out], [(b'PONG', b'\r')])
        self.assertEqual(_drain(buf), b'X')

        # At EOF, final=True flushes deferral - but an undelimited tail is the caller's decision to take or reject.
        self.assertEqual(f.decode(buf, final=True), [])
        self.assertEqual(buf.split_to(len(buf)).tobytes(), b'X')


class _ChunkSocket:
    """Tutorial stand-in for a socket: serves queued bytes through recv_into()."""

    def __init__(self, chunks: ta.Sequence[bytes]) -> None:
        super().__init__()

        self._chunks: ta.List[bytes] = list(chunks)

    def recv_into(self, mv: memoryview) -> int:
        if not self._chunks:
            return 0
        c = self._chunks.pop(0)
        n = min(len(c), len(mv))
        mv[:n] = c[:n]
        if n < len(c):
            self._chunks.insert(0, c[n:])
        return n


class TestExamples06ReserveCommitIo(unittest.TestCase):
    """
    Zero-copy reads: reserve() writable space, let the driver fill it, commit() what actually arrived.

    This replaces the scratch-bytearray pattern from chapter 02 entirely - the bytes land in buffer-owned storage. A
    reservation is exclusive: until commit(), anything that would reshape or consume the buffer raises, so the
    discipline is a strict reserve -> fill -> commit -> decode cycle.
    """

    def test_recv_into_decode_loop(self) -> None:
        buf = SegmentedByteStreamBuffer(chunk_size=16)

        # The exclusivity, demonstrated once up front (commit(0) abandons a reservation):
        _ = buf.reserve(4)
        with self.assertRaises(OutstandingReserveByteStreamBufferError):
            buf.write(b'nope')
        buf.commit(0)

        # Two u16be-length-prefixed messages, arriving in awkward 4-byte reads that tear both headers and payloads.
        sock = _ChunkSocket([b'\x00\x05he', b'llo\x00', b'\x03hey'])
        dec = LengthFieldByteStreamFrameDecoder(length_field_length=2, initial_bytes_to_strip=2)

        frames = []
        while True:
            mv = buf.reserve(8)
            n = sock.recv_into(mv)
            buf.commit(n)  # commit exactly what arrived; over-reservation is free
            if not n:
                break
            frames.extend(dec.decode(buf))

        self.assertEqual([v.tobytes() for v in frames], [b'hello', b'hey'])
        self.assertEqual(len(buf), 0)


class TestExamples07IncrementalBinaryParsing(unittest.TestCase):
    """
    A little TLV protocol parsed incrementally: u8 type, u16be length, payload.

    Two disciplines shown here: NeedMoreData means 'retry later, nothing consumed', and header bytes peeked via an
    ephemeral view are extracted to plain ints *before* any consuming call (chapter 02 again, in miniature).
    """

    @staticmethod
    def _try_parse_record(buf) -> ta.Optional[ta.Tuple[int, bytes]]:
        rdr = ByteStreamBufferReader(buf)

        try:
            hdr = rdr.peek_exact(3)  # coalesces a torn header across segments; view is ephemeral
        except NeedMoreDataByteStreamBufferError:
            return None

        ty = hdr[0]
        ln = int.from_bytes(hdr[1:3], 'big')
        # From here on hdr must not be touched - the consuming calls below may invalidate it.

        if len(buf) < 3 + ln:
            return None  # header parsed, but only into locals - nothing consumed, safe to retry

        buf.advance(3)
        payload = rdr.take(ln)
        return (ty, bytes(payload.tobytes()))

    def test_torn_records(self) -> None:
        # chunk_size=0: every write is its own segment, so these splits tear the header across segments and force
        # the coalesce path inside peek_exact.
        buf = SegmentedByteStreamBuffer()

        records = []

        def pump():
            while (r := self._try_parse_record(buf)) is not None:
                records.append(r)

        # Record 1: type 7, 5-byte payload. Record 2: type 200, *empty* payload.
        for chunk in (b'\x07', b'\x00\x05he', b'llo\xc8\x00', b'\x00'):
            buf.write(chunk)
            pump()

        self.assertEqual(records, [(7, b'hello'), (200, b'')])
        self.assertEqual(len(buf), 0)


class TestExamples08BoundsAndRecovery(unittest.TestCase):
    """
    Everything has a limit: buffers cap growth, framers cap frame size - and errors never eat decoded progress.

    A limit violation is a *signal*, not a corruption: buffered bytes stay intact, already-decoded frames are
    returned before the error raises, and the caller chooses the recovery (backpressure, close, or skip the frame).
    """

    def test_buffer_max_size_as_backpressure(self) -> None:
        buf = SegmentedByteStreamBuffer(max_size=16)
        buf.write(b'0123456789')

        with self.assertRaises(BufferTooLargeByteStreamBufferError):
            buf.write(b'0123456789')  # would exceed the cap - signal upstream to pause

        self.assertEqual(len(buf), 10)  # nothing was lost or partially written

        buf.advance(8)  # downstream drains...
        buf.write(b'0123456789')  # ...and writing resumes
        self.assertEqual(len(buf), 12)

    def test_oversized_frame_skip_recovery(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\n'], max_size=8)
        buf = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(chunk_size=1024))
        buf.write(b'ok\n' + b'X' * 32 + b'\nfine\n')

        # The frames decoded before the oversized one are returned, not lost to the exception...
        out = f.decode(buf)
        self.assertEqual([v.tobytes() for v in out], [b'ok'])

        # ...and the error raises on the next call, with the poison frame first in line and nothing consumed.
        with self.assertRaises(FrameTooLargeByteStreamBufferError):
            f.decode(buf)

        # One recovery option: skip past the poison frame's delimiter and carry on.
        i = buf.find(b'\n')
        buf.advance(i + 1)
        self.assertEqual([v.tobytes() for v in f.decode(buf)], [b'fine'])


class TestExamples09ZeroCopyOverExistingData(unittest.TestCase):
    """Parsing data already in memory: DirectByteStreamBuffer wraps it without copying, and views alias it."""

    def test_split_views_alias_the_source(self) -> None:
        blob = b'alpha,beta,gamma'

        buf = DirectByteStreamBuffer(blob)
        parts = ByteStreamBuffers.split(buf, b',', final=True)

        self.assertEqual([p.tobytes() for p in parts], [b'alpha,', b'beta,', b'gamma'])

        # Genuinely zero-copy: the views' storage *is* the original blob. tobytes() above was the explicit copy
        # boundary; peek()/segments() never left the source object.
        self.assertIs(parts[1].peek().obj, blob)
