import typing as ta

from omcore import dataclasses as dc

from .varints import decode_uvarint
from .varints import encode_uvarint


##


PUT_KIND = 0
TOMBSTONE_KIND = 1


@dc.dataclass(frozen=True)
class LsmRecord:
    key: bytes
    value: bytes | None  # None is a tombstone

    @property
    def is_tombstone(self) -> bool:
        return self.value is None


def encode_record(rec: LsmRecord) -> bytes:
    parts = [encode_uvarint(len(rec.key)), rec.key]
    if rec.value is None:
        parts.append(bytes([TOMBSTONE_KIND]))
    else:
        parts.extend([bytes([PUT_KIND]), encode_uvarint(len(rec.value)), rec.value])
    return b''.join(parts)


def decode_records(buf: bytes) -> ta.Iterator[LsmRecord]:
    pos = 0
    n = len(buf)
    while pos < n:
        kl, pos = decode_uvarint(buf, pos)
        key = buf[pos:pos + kl]
        pos += kl
        if pos >= n:
            raise ValueError('truncated record')
        kind = buf[pos]
        pos += 1
        if kind == TOMBSTONE_KIND:
            yield LsmRecord(key, None)
        elif kind == PUT_KIND:
            vl, pos = decode_uvarint(buf, pos)
            if pos + vl > n:
                raise ValueError('truncated record value')
            yield LsmRecord(key, buf[pos:pos + vl])
            pos += vl
        else:
            raise ValueError(f'bad record kind: {kind}')
