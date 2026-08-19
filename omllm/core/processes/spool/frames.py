"""
Wire format of the spool: an append-only stream of frames, each a fixed 32-byte little-endian header followed by the
payload. Cursors are byte offsets into this stream and always land on frame boundaries when obtained from the spool.
"""
import struct
import typing as ta

from omcore import dataclasses as dc


##


# fd (u8), flags (u8), pad (u16), len (u32), t_mono_ns (i64), t_wall_ns (i64), seq (u64)
FRAME_HEADER: ta.Final = struct.Struct('<BBHIqqQ')
FRAME_HEADER_SIZE: ta.Final[int] = FRAME_HEADER.size

MAX_FRAME_PAYLOAD: ta.Final[int] = 0xFFFFFFFF


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True)
class SpoolRecord:
    fd: int
    data: bytes

    _: dc.KW_ONLY

    t_mono_ns: int
    t_wall_ns: int
    seq: int

    # Offset of the frame header in the framed stream.
    offset: int

    @property
    def end(self) -> int:
        return self.offset + FRAME_HEADER_SIZE + len(self.data)

    def __repr__(self) -> str:
        d = self.data if len(self.data) <= 40 else self.data[:37] + b'...'
        return (
            f'{self.__class__.__name__}('
            f'fd={self.fd}, '
            f'seq={self.seq}, '
            f'offset={self.offset}, '
            f'data={d!r}'
            f')'
        )


##


def encode_frame(
        fd: int,
        data: bytes,
        *,
        t_mono_ns: int,
        t_wall_ns: int,
        seq: int,
        flags: int = 0,
) -> bytes:
    if len(data) > MAX_FRAME_PAYLOAD:
        raise ValueError(len(data))
    return FRAME_HEADER.pack(fd, flags, 0, len(data), t_mono_ns, t_wall_ns, seq) + data


def peek_frame_size(buf: bytes | bytearray | memoryview) -> int | None:
    """The full size (header + payload) of the frame starting at `buf[0]`, or None if not even a header is present."""

    if len(buf) < FRAME_HEADER_SIZE:
        return None
    ln = FRAME_HEADER.unpack_from(buf, 0)[3]
    return FRAME_HEADER_SIZE + ln


class FrameDecodeResult(ta.NamedTuple):
    records: list[SpoolRecord]

    # Number of bytes of `buf` fully consumed - a trailing partial frame is left unconsumed, not an error.
    consumed: int


def decode_frames(
        buf: bytes | bytearray | memoryview,
        base_offset: int,
        *,
        max_payload: int | None = None,
        at_least_one: bool = True,
) -> FrameDecodeResult:
    """
    Decodes whole frames from `buf`, stopping before the frame that would push the decoded payload past `max_payload`.
    With `at_least_one` (the default) the first frame is taken regardless, so a caller with an empty result always
    makes progress; a caller that has already accumulated records elsewhere passes False to enforce the budget strictly.
    """

    mv = memoryview(buf)
    records: list[SpoolRecord] = []
    pos = 0
    payload = 0
    n = len(mv)
    while pos + FRAME_HEADER_SIZE <= n:
        fd, _flags, _pad, ln, t_mono_ns, t_wall_ns, seq = FRAME_HEADER.unpack_from(mv, pos)
        end = pos + FRAME_HEADER_SIZE + ln
        if end > n:
            break
        if max_payload is not None and (records or not at_least_one) and payload + ln > max_payload:
            break
        records.append(SpoolRecord(
            fd,
            bytes(mv[pos + FRAME_HEADER_SIZE:end]),
            t_mono_ns=t_mono_ns,
            t_wall_ns=t_wall_ns,
            seq=seq,
            offset=base_offset + pos,
        ))
        payload += ln
        pos = end
    return FrameDecodeResult(records, pos)
