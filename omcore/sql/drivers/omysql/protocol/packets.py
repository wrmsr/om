# Copyright (c) 2010, 2013 PyMySQL contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""Framing and primitive encodings of the MySQL client/server protocol."""
import struct
import typing as ta

from ..... import dataclasses as dc
from ..errors import ProtocolError


##


# The payload size at which a packet must be continued in a following packet.
MAX_PACKET_LENGTH = 2**24 - 1

HEADER_SIZE = 4

_HEADER = struct.Struct('<HBB')  # payload length low 16 bits, payload length high 8 bits, sequence id

NULL_COLUMN = 0xFB


@dc.dataclass(frozen=True)
class Packet:
    """One wire packet: a sequence id and a payload of at most MAX_PACKET_LENGTH bytes."""

    seq: int
    payload: bytes


def pack_header(length: int, seq: int) -> bytes:
    return _HEADER.pack(length & 0xFFFF, (length >> 16) & 0xFF, seq & 0xFF)


def unpack_header(data: bytes | memoryview) -> tuple[int, int]:
    """Returns the payload length and sequence id of a packet header."""

    low, high, seq = _HEADER.unpack(data)
    return low + (high << 16), seq


def pack_packet(seq: int, payload: bytes) -> bytes:
    return pack_header(len(payload), seq) + payload


def split_payload(payload: bytes) -> list[bytes]:
    """
    Splits a command payload into the payloads of the packets needed to send it, including the empty terminating packet
    required when its size is a multiple of the maximum.
    """

    chunks = [payload[i:i + MAX_PACKET_LENGTH] for i in range(0, len(payload), MAX_PACKET_LENGTH)]
    if not chunks or len(chunks[-1]) == MAX_PACKET_LENGTH:
        chunks.append(b'')
    return chunks


##


def encode_lenenc_int(i: int) -> bytes:
    if i < 0:
        raise ValueError(f'Encoding {i} is less than 0 - no representation in LengthEncodedInteger')
    elif i < 0xFB:
        return bytes([i])
    elif i < (1 << 16):
        return b'\xfc' + struct.pack('<H', i)
    elif i < (1 << 24):
        return b'\xfd' + struct.pack('<I', i)[:3]
    elif i < (1 << 64):
        return b'\xfe' + struct.pack('<Q', i)
    else:
        raise ValueError(f'Encoding {i:x} is larger than {1 << 64:x} - no representation in LengthEncodedInteger')


def encode_lenenc_str(b: bytes) -> bytes:
    return encode_lenenc_int(len(b)) + b


class PacketReader:
    """A cursor over a packet payload."""

    def __init__(self, data: bytes) -> None:
        super().__init__()

        self._data = data
        self._pos = 0

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def position(self) -> int:
        return self._pos

    @property
    def remaining(self) -> int:
        return len(self._data) - self._pos

    def peek(self, n: int = 1) -> bytes:
        return self._data[self._pos:self._pos + n]

    def read(self, n: int) -> bytes:
        end = self._pos + n
        if end > len(self._data):
            raise ProtocolError(f'Packet too short: wanted {n} bytes at {self._pos}, have {len(self._data)}')
        result = self._data[self._pos:end]
        self._pos = end
        return result

    def read_all(self) -> bytes:
        result = self._data[self._pos:]
        self._pos = len(self._data)
        return result

    def skip(self, n: int) -> None:
        self.read(n)

    def read_uint8(self) -> int:
        return self.read(1)[0]

    def read_uint16(self) -> int:
        return struct.unpack('<H', self.read(2))[0]

    def read_uint24(self) -> int:
        low, high = struct.unpack('<HB', self.read(3))
        return low + (high << 16)

    def read_uint32(self) -> int:
        return struct.unpack('<I', self.read(4))[0]

    def read_uint64(self) -> int:
        return struct.unpack('<Q', self.read(8))[0]

    def read_struct(self, fmt: str) -> tuple[ta.Any, ...]:
        s = struct.Struct(fmt)
        return s.unpack(self.read(s.size))

    def read_cstring(self) -> bytes:
        end = self._data.find(b'\0', self._pos)
        if end < 0:
            raise ProtocolError('Unterminated string in packet')
        result = self._data[self._pos:end]
        self._pos = end + 1
        return result

    def read_lenenc_int(self) -> int | None:
        """Reads a length encoded integer, returning None for the NULL marker."""

        c = self.read_uint8()
        if c == NULL_COLUMN:
            return None
        if c < NULL_COLUMN:
            return c
        elif c == 0xFC:
            return self.read_uint16()
        elif c == 0xFD:
            return self.read_uint24()
        elif c == 0xFE:
            return self.read_uint64()
        else:
            raise ProtocolError(f'Invalid length encoded integer prefix: {c:#x}')

    def read_lenenc_str(self) -> bytes | None:
        length = self.read_lenenc_int()
        if length is None:
            return None
        return self.read(length)
