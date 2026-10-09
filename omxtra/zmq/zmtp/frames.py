"""
ZMTP 3.0 frames: a flags byte, then the body length - one byte, or eight network-order bytes with LONG - then the body.
The length excludes the header.
"""
import typing as ta


##


FLAG_MORE = 0x01
FLAG_LONG = 0x02
FLAG_COMMAND = 0x04

RESERVED_FLAGS = 0xff & ~(FLAG_MORE | FLAG_LONG | FLAG_COMMAND)

SHORT_HEADER_SIZE = 2
LONG_HEADER_SIZE = 9

MAX_SHORT_SIZE = 0xff
MAX_LONG_SIZE = (1 << 63) - 1


def encode_frame_header(size: int, *, more: bool = False, command: bool = False) -> bytes:
    if size < 0 or size > MAX_LONG_SIZE:
        raise ValueError(size)
    if command and more:
        raise ValueError('command frames cannot have MORE')

    flags = (FLAG_MORE if more else 0) | (FLAG_COMMAND if command else 0)
    if size <= MAX_SHORT_SIZE:
        return bytes([flags, size])
    return bytes([flags | FLAG_LONG]) + size.to_bytes(8, 'big')


# Bodies at least this large are emitted as their own pieces rather than copied into a joined buffer.
_JOIN_MAX = 16 * 1024


def encode_message(frames: ta.Sequence[bytes]) -> list[bytes]:
    """Encode a whole multipart message as a list of byte pieces, coalescing small ones."""

    pieces: list[bytes] = []
    pending: list[bytes] = []
    last = len(frames) - 1
    for i, f in enumerate(frames):
        pending.append(encode_frame_header(len(f), more=i < last))
        if len(f) >= _JOIN_MAX:
            pieces.append(b''.join(pending))
            pending.clear()
            pieces.append(f)
        elif f:
            pending.append(f)

    if pending:
        pieces.append(b''.join(pending))
    return pieces


def encode_command_frame(name: bytes, data: bytes) -> bytes:
    if not (1 <= len(name) <= 0xff):
        raise ValueError(name)
    body = bytes([len(name)]) + name + data
    return encode_frame_header(len(body), command=True) + body
