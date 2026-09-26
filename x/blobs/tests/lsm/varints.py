def encode_uvarint(n: int) -> bytes:
    """Unsigned LEB128."""

    if n < 0:
        raise ValueError(n)
    out = bytearray()
    while True:
        b = n & 0x7f
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def decode_uvarint(buf: bytes | memoryview, pos: int) -> tuple[int, int]:
    """Returns (value, next position)."""

    n = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise ValueError('truncated varint')
        b = buf[pos]
        pos += 1
        n |= (b & 0x7f) << shift
        if not b & 0x80:
            return n, pos
        shift += 7
        if shift > 63:
            raise ValueError('varint too long')
