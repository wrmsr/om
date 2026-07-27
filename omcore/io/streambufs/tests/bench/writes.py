# ruff: noqa: UP006 UP045
# @om-lite
"""
Accumulation cost: write a stream of chunks, then materialize the whole thing as contiguous bytes.

Compares the streambufs backends against the naive alternatives they exist to replace. `bytes +=` is the known-bad
quadratic baseline; `bytearray +=` / list-join / BytesIO are the 'good naive' anchors that lack bounds, views, and
consumption semantics.
"""
import functools
import io
import typing as ta

from ...linear import LinearByteStreamBuffer
from ...segmented import SegmentedByteStreamBuffer
from ...utils import ByteStreamBuffers
from .harness import bench
from .harness import report


##


def _bytes_concat(chunks: ta.Sequence[bytes]) -> bytes:
    b = b''
    for c in chunks:
        b += c
    return b


def _bytearray_extend(chunks: ta.Sequence[bytes]) -> bytes:
    ba = bytearray()
    for c in chunks:
        ba += c
    return bytes(ba)


def _list_join(chunks: ta.Sequence[bytes]) -> bytes:
    lst = []
    for c in chunks:
        lst.append(c)  # noqa: PERF402  # deliberately per-chunk appends, modeling streaming arrival
    return b''.join(lst)


def _bytesio(chunks: ta.Sequence[bytes]) -> bytes:
    bio = io.BytesIO()
    for c in chunks:
        bio.write(c)
    return bio.getvalue()


def _linear(chunks: ta.Sequence[bytes]) -> bytes:
    buf = LinearByteStreamBuffer()
    for c in chunks:
        buf.write(c)
    return ByteStreamBuffers.to_bytes(buf, strict=True)


def _segmented_plain(chunks: ta.Sequence[bytes]) -> bytes:
    buf = SegmentedByteStreamBuffer()
    for c in chunks:
        buf.write(c)
    return ByteStreamBuffers.to_bytes(buf, strict=True)


def _segmented_chunked(chunks: ta.Sequence[bytes]) -> bytes:
    buf = SegmentedByteStreamBuffer(chunk_size=64 * 1024)
    for c in chunks:
        buf.write(c)
    return ByteStreamBuffers.to_bytes(buf, strict=True)


_CANDIDATES: ta.Sequence[ta.Tuple[str, ta.Callable[[ta.Sequence[bytes]], bytes]]] = [
    ('bytes_concat', _bytes_concat),
    ('bytearray_extend', _bytearray_extend),
    ('list_join', _list_join),
    ('bytesio', _bytesio),
    ('linear', _linear),
    ('segmented_plain', _segmented_plain),
    ('segmented_chunked_64k', _segmented_chunked),
]

# (chunk_size, total_bytes) - totals sized so even the quadratic candidate finishes promptly.
_PATTERNS: ta.Sequence[ta.Tuple[int, int]] = [
    (1, 16 * 1024),
    (64, 256 * 1024),
    (4096, 1024 * 1024),
    (65536, 4 * 1024 * 1024),
]


def _main() -> None:
    for chunk_size, total in _PATTERNS:
        chunks = [bytes(chunk_size) for _ in range(total // chunk_size)]

        expected = b''.join(chunks)
        for name, fn in _CANDIDATES:
            if fn(chunks) != expected:
                raise RuntimeError(f'bad output: {name}')

        results = [
            bench(name, functools.partial(fn, chunks), bytes_per_op=total)
            for name, fn in _CANDIDATES
        ]
        report(
            f'accumulate + materialize: {len(chunks)} x {chunk_size}B chunks = {total // 1024} KB',
            results,
            baseline='bytearray_extend',
        )


if __name__ == '__main__':
    _main()
