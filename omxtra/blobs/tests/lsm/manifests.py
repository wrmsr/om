import base64
import json
import typing as ta

from omcore import dataclasses as dc

from .errors import LsmCorruptionError
from .ssts import SstRef


##


MANIFEST_FORMAT = 1


@dc.dataclass(frozen=True, kw_only=True)
class LsmManifest:
    writer_id: str  # uuid7 hex, one per LsmDb instance
    epoch: int  # bumped when a writer takes over
    nonce: str  # uuid7 hex per commit: makes every body unique, as ManifestStore's read-back requires
    l0: ta.Sequence[SstRef]  # newest first
    l1: ta.Sequence[SstRef]  # sorted by key, non-overlapping

    def all_ssts(self) -> list[SstRef]:
        return [*self.l0, *self.l1]


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode('ascii')


def _ref_to_dict(r: SstRef) -> dict[str, ta.Any]:
    return {
        'key': r.key,
        'min_key': _b64(r.min_key),
        'max_key': _b64(r.max_key),
        'size': r.size,
        'entries': r.entries,
    }


def _ref_from_dict(d: ta.Mapping[str, ta.Any]) -> SstRef:
    return SstRef(
        key=d['key'],
        min_key=base64.b64decode(d['min_key']),
        max_key=base64.b64decode(d['max_key']),
        size=d['size'],
        entries=d['entries'],
    )


def encode_manifest(m: LsmManifest) -> bytes:
    return json.dumps({
        'format': MANIFEST_FORMAT,
        'writer_id': m.writer_id,
        'epoch': m.epoch,
        'nonce': m.nonce,
        'l0': [_ref_to_dict(r) for r in m.l0],
        'l1': [_ref_to_dict(r) for r in m.l1],
    }, separators=(',', ':')).encode('utf-8')


def decode_manifest(buf: bytes) -> LsmManifest:
    try:
        d = json.loads(buf.decode('utf-8'))
        if d['format'] != MANIFEST_FORMAT:
            raise LsmCorruptionError(f'unsupported manifest format: {d["format"]!r}')
        return LsmManifest(
            writer_id=d['writer_id'],
            epoch=d['epoch'],
            nonce=d['nonce'],
            l0=[_ref_from_dict(r) for r in d['l0']],
            l1=[_ref_from_dict(r) for r in d['l1']],
        )
    except (ValueError, KeyError, TypeError) as e:
        raise LsmCorruptionError('malformed manifest') from e
