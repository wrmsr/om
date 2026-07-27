# ruff: noqa: UP006 UP045
# @om-lite
"""
Search cost: stream-correct find/rfind vs flat `bytes.find`, across segmentations - and the trickle-and-poll pattern
(`write a little, look for the delimiter, repeat`) that ScanningByteStreamBuffer exists for.
"""
import functools
import typing as ta

from ...direct import DirectByteStreamBuffer
from ...linear import LinearByteStreamBuffer
from ...scanning import ScanningByteStreamBuffer
from ...segmented import SegmentedByteStreamBuffer
from .harness import bench
from .harness import report


##


_DELIM = b'\r\n\r\n'


def _make_segmented(data: bytes, seg_size: int) -> SegmentedByteStreamBuffer:
    buf = SegmentedByteStreamBuffer()
    for i in range(0, len(data), seg_size):
        buf.write(data[i:i + seg_size])
    return buf


def _bench_finds(total: int, delim_at: int, title: str) -> None:
    data = b'a' * delim_at + _DELIM + b'a' * (total - delim_at - len(_DELIM))

    direct = DirectByteStreamBuffer(data)

    linear = LinearByteStreamBuffer()
    linear.write(data)

    segs = {seg_size: _make_segmented(data, seg_size) for seg_size in (256, 4096, 65536)}

    chunks_4k = [data[i:i + 4096] for i in range(0, len(data), 4096)]

    expected = data.find(_DELIM)
    for name, i in [
        ('direct', direct.find(_DELIM)),
        ('linear', linear.find(_DELIM)),
        *[(f'segmented_{k}', v.find(_DELIM)) for k, v in segs.items()],
    ]:
        if i != expected:
            raise RuntimeError(f'bad find: {name}: {i} != {expected}')

    results = [
        bench('flat_bytes_find', lambda: data.find(_DELIM), bytes_per_op=total),
        bench('join_then_find', lambda: b''.join(chunks_4k).find(_DELIM), bytes_per_op=total),
        bench('direct_find', lambda: direct.find(_DELIM), bytes_per_op=total),
        bench('linear_find', lambda: linear.find(_DELIM), bytes_per_op=total),
        *[
            bench(f'segmented_{seg_size}_find', functools.partial(buf.find, _DELIM), bytes_per_op=total)
            for seg_size, buf in segs.items()
        ],
        bench('flat_bytes_rfind', lambda: data.rfind(_DELIM), bytes_per_op=total),
        bench('segmented_4096_rfind', lambda: segs[4096].rfind(_DELIM), bytes_per_op=total),
    ]
    report(title, results, baseline='flat_bytes_find')


##


def _trickle_bytearray(chunks: ta.Sequence[bytes]) -> int:
    ba = bytearray()
    i = -1
    for c in chunks:
        ba += c
        i = ba.find(_DELIM)
    return i


def _trickle_segmented(chunks: ta.Sequence[bytes]) -> int:
    buf = SegmentedByteStreamBuffer(chunk_size=64 * 1024)
    i = -1
    for c in chunks:
        buf.write(c)
        i = buf.find(_DELIM)
    return i


def _trickle_scanning(chunks: ta.Sequence[bytes]) -> int:
    buf = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(chunk_size=64 * 1024))
    i = -1
    for c in chunks:
        buf.write(c)
        i = buf.find(_DELIM)
    return i


def _bench_trickle_poll(total: int, chunk_size: int) -> None:
    data = b'a' * (total - len(_DELIM)) + _DELIM
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    expected = data.find(_DELIM)
    for name, fn in [
        ('bytearray', _trickle_bytearray),
        ('segmented', _trickle_segmented),
        ('scanning', _trickle_scanning),
    ]:
        if fn(chunks) != expected:
            raise RuntimeError(f'bad trickle find: {name}')

    results = [
        bench('bytearray_poll', lambda: _trickle_bytearray(chunks), bytes_per_op=total),
        bench('segmented_poll', lambda: _trickle_segmented(chunks), bytes_per_op=total),
        bench('scanning_poll', lambda: _trickle_scanning(chunks), bytes_per_op=total),
    ]
    report(
        f'trickle-and-poll: {chunk_size}B writes + find() to {total // 1024} KB, delim at end',
        results,
        baseline='bytearray_poll',
    )


##


def _main() -> None:
    _bench_finds(1024 * 1024, 1024 * 1024 - len(_DELIM), 'find: 1 MB, delim at end (full scan)')
    _bench_finds(1024 * 1024, 512, 'find: 1 MB, delim at 512 B (early exit)')
    _bench_trickle_poll(64 * 1024, 64)


if __name__ == '__main__':
    _main()
