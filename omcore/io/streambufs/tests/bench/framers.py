# ruff: noqa: UP006 UP045
# @om-lite
"""
Framing cost: the delimiter and length-field frame decoders driven the way the pipeline drives them (streaming chunk
writes interleaved with decode calls), vs flat/naive equivalents.
"""
import typing as ta

from ...framing import LengthFieldByteStreamFrameDecoder
from ...framing import LongestMatchDelimiterByteStreamFrameDecoder
from ...scanning import ScanningByteStreamBuffer
from ...segmented import SegmentedByteStreamBuffer
from .harness import bench
from .harness import report


##


def _split_flat(data: bytes) -> int:
    return len(data.split(b'\r\n')) - 1  # trailing empty piece


def _handroll_bytearray(chunks: ta.Sequence[bytes]) -> int:
    ba = bytearray()
    n = 0
    for c in chunks:
        ba += c
        start = 0
        while (i := ba.find(b'\r\n', start)) >= 0:
            n += 1
            start = i + 2
        if start:
            del ba[:start]
    return n


def _framer_lines(chunks: ta.Sequence[bytes], delims: ta.Sequence[bytes]) -> int:
    buf = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(chunk_size=64 * 1024))
    fr = LongestMatchDelimiterByteStreamFrameDecoder(delims)
    n = 0
    for c in chunks:
        buf.write(c)
        n += len(fr.decode(buf))
    return n


def _bench_lines(num_lines: int, line_len: int) -> None:
    data = (b'x' * (line_len - 2) + b'\r\n') * num_lines
    chunks = [data[i:i + 4096] for i in range(0, len(data), 4096)]

    for name, n in [
        ('split_flat', _split_flat(data)),
        ('handroll_bytearray', _handroll_bytearray(chunks)),
        ('framer', _framer_lines(chunks, [b'\r\n'])),
        ('framer_two_delims', _framer_lines(chunks, [b'\r\n', b'\n'])),
    ]:
        if n != num_lines:
            raise RuntimeError(f'bad frame count: {name}: {n} != {num_lines}')

    total = len(data)
    results = [
        bench('split_flat', lambda: _split_flat(data), bytes_per_op=total),
        bench('handroll_bytearray', lambda: _handroll_bytearray(chunks), bytes_per_op=total),
        bench('framer', lambda: _framer_lines(chunks, [b'\r\n']), bytes_per_op=total),
        bench('framer_two_delims', lambda: _framer_lines(chunks, [b'\r\n', b'\n']), bytes_per_op=total),
    ]
    report(
        f'line framing: {num_lines} x {line_len}B lines = {total // 1024} KB, 4 KB feed chunks',
        results,
        baseline='handroll_bytearray',
    )


##


def _trickle_framer(chunks: ta.Sequence[bytes], *, scanning: bool) -> int:
    inner = SegmentedByteStreamBuffer(chunk_size=64 * 1024)
    buf = ScanningByteStreamBuffer(inner) if scanning else inner
    fr = LongestMatchDelimiterByteStreamFrameDecoder([b'\r\n'])
    n = 0
    for c in chunks:
        buf.write(c)
        n += len(fr.decode(buf))
    return n


def _bench_trickle_framing(total: int, chunk_size: int) -> None:
    data = b'x' * (total - 2) + b'\r\n'
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    for scanning in (False, True):
        if _trickle_framer(chunks, scanning=scanning) != 1:
            raise RuntimeError('bad trickle frame count')

    results = [
        bench('framer_plain', lambda: _trickle_framer(chunks, scanning=False), bytes_per_op=total),
        bench('framer_scanning', lambda: _trickle_framer(chunks, scanning=True), bytes_per_op=total),
    ]
    report(
        f'trickle framing: {chunk_size}B writes + decode() to {total // 1024} KB, delim at end',
        results,
        baseline='framer_plain',
    )


##


def _naive_flat_lengths(data: bytes) -> int:
    mv = memoryview(data)
    n = 0
    off = 0
    end = len(data)
    while off + 4 <= end:
        ln = int.from_bytes(mv[off:off + 4], 'big')
        if off + 4 + ln > end:
            break
        _ = mv[off + 4:off + 4 + ln]
        off += 4 + ln
        n += 1
    return n


def _framer_lengths(chunks: ta.Sequence[bytes]) -> int:
    buf = SegmentedByteStreamBuffer(chunk_size=64 * 1024)
    fr = LengthFieldByteStreamFrameDecoder(
        length_field_length=4,
        initial_bytes_to_strip=4,
    )
    n = 0
    for c in chunks:
        buf.write(c)
        n += len(fr.decode(buf))
    return n


def _bench_lengths(num_frames: int, payload_len: int) -> None:
    frame = payload_len.to_bytes(4, 'big') + b'p' * payload_len
    data = frame * num_frames
    chunks = [data[i:i + 4096] for i in range(0, len(data), 4096)]

    for name, n in [
        ('naive_flat', _naive_flat_lengths(data)),
        ('framer', _framer_lengths(chunks)),
    ]:
        if n != num_frames:
            raise RuntimeError(f'bad frame count: {name}: {n} != {num_frames}')

    total = len(data)
    results = [
        bench('naive_flat', lambda: _naive_flat_lengths(data), bytes_per_op=total),
        bench('framer', lambda: _framer_lengths(chunks), bytes_per_op=total),
    ]
    report(
        f'length-field framing: {num_frames} x (4B hdr + {payload_len}B) = {total // 1024} KB, 4 KB feed chunks',
        results,
        baseline='naive_flat',
    )


##


def _main() -> None:
    _bench_lines(4096, 62)
    _bench_trickle_framing(64 * 1024, 64)
    _bench_lengths(1024, 252)
    _bench_lengths(64, 16 * 1024 - 4)


if __name__ == '__main__':
    _main()
