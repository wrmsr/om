import struct
import zlib

from .errors import LsmCorruptionError
from .records import LsmRecord
from .records import decode_records
from .records import encode_record


##


_CRC = struct.Struct('<I')


def seal(payload: bytes) -> bytes:
    return payload + _CRC.pack(zlib.crc32(payload))


def unseal(buf: bytes) -> bytes:
    if len(buf) < _CRC.size:
        raise LsmCorruptionError('block too short')
    payload, (crc,) = buf[:-_CRC.size], _CRC.unpack(buf[-_CRC.size:])
    if zlib.crc32(payload) != crc:
        raise LsmCorruptionError('block checksum mismatch')
    return payload


class BlockBuilder:
    def __init__(self) -> None:
        super().__init__()

        self._parts: list[bytes] = []
        self._size = 0
        self._last_key: bytes | None = None

    @property
    def size(self) -> int:
        return self._size

    @property
    def last_key(self) -> bytes | None:
        return self._last_key

    def add(self, rec: LsmRecord) -> None:
        b = encode_record(rec)
        self._parts.append(b)
        self._size += len(b)
        self._last_key = rec.key

    def finish(self) -> bytes:
        return seal(b''.join(self._parts))


def parse_block(buf: bytes) -> list[LsmRecord]:
    try:
        return list(decode_records(unseal(buf)))
    except ValueError as e:
        raise LsmCorruptionError('malformed block') from e
