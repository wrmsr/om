# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""
A tiny self-describing binary frame codec for the toy protocols: each frame is a length-prefixed type id followed by
its fields as tagged values. Real bytes on a real (pure) transport keep the multiplexer honest about partial reads,
batching, and ordering.
"""
import dataclasses as dc
import struct
import typing as ta

from ....streambufs.types import ByteStreamBuffer
from ....streambufs.utils import ByteStreamBuffers
from ...bytes.decoders import BufferedBytesToMessageDecoderIoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...errors import IncompleteDecodingIoPipelineError


##


def _encode_value(v: ta.Any, out: bytearray) -> None:
    if v is None:
        out += b'N'
    elif v is True:
        out += b'T'
    elif v is False:
        out += b'F'
    elif isinstance(v, int):
        out += b'I' + struct.pack('>q', v)
    elif isinstance(v, (bytes, bytearray, memoryview)):
        b = bytes(v)
        out += b'B' + struct.pack('>I', len(b)) + b
    elif isinstance(v, str):
        b = v.encode('utf-8')
        out += b'S' + struct.pack('>I', len(b)) + b
    elif isinstance(v, (list, tuple)):
        out += b'L' + struct.pack('>I', len(v))
        for x in v:
            _encode_value(x, out)
    else:
        raise TypeError(v)


def _decode_value(b: bytes, pos: int) -> ta.Tuple[ta.Any, int]:
    tag = b[pos:pos + 1]
    pos += 1
    if tag == b'N':
        return None, pos
    if tag == b'T':
        return True, pos
    if tag == b'F':
        return False, pos
    if tag == b'I':
        return struct.unpack_from('>q', b, pos)[0], pos + 8
    if tag in (b'B', b'S'):
        (n,) = struct.unpack_from('>I', b, pos)
        pos += 4
        raw = b[pos:pos + n]
        return (raw if tag == b'B' else raw.decode('utf-8')), pos + n
    if tag == b'L':
        (n,) = struct.unpack_from('>I', b, pos)
        pos += 4
        items = []
        for _ in range(n):
            x, pos = _decode_value(b, pos)
            items.append(x)
        return tuple(items), pos
    raise ValueError(tag)


class FrameCodec:
    def __init__(self, frame_types: ta.Sequence[type]) -> None:
        super().__init__()

        self._by_id = dict(enumerate(frame_types))
        self._ids = {ty: i for i, ty in self._by_id.items()}

    def encode(self, frame: ta.Any) -> bytes:
        body = bytearray(struct.pack('>H', self._ids[type(frame)]))
        _encode_value(tuple(getattr(frame, f.name) for f in dc.fields(frame)), body)
        return struct.pack('>I', len(body)) + bytes(body)

    def decode(self, body: bytes) -> ta.Any:
        (tid,) = struct.unpack_from('>H', body, 0)
        fields, pos = _decode_value(body, 2)
        if pos != len(body):
            raise ValueError('trailing bytes in frame')
        return self._by_id[tid](*fields)


class FrameCodecIoPipelineHandler(BufferedBytesToMessageDecoderIoPipelineHandler):
    """Decodes inbound bytes into frames; encodes outbound frames into bytes."""

    def __init__(self, codec: FrameCodec) -> None:
        super().__init__()

        self._codec = codec
        self._frame_types = tuple(codec._by_id.values())  # noqa

    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        while len(buf) >= 4:
            (n,) = struct.unpack('>I', bytes(buf.coalesce(4)))
            if len(buf) < 4 + n:
                break
            buf.advance(4)
            out.append(self._codec.decode(bytes(buf.coalesce(n)) if n else b''))
            buf.advance(n)

        if final and len(buf):
            raise IncompleteDecodingIoPipelineError

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, self._frame_types):
            ctx.feed_out(self._codec.encode(msg))
            return

        ctx.feed_out(msg)


def frame_bytes(data: ta.Any) -> bytes:
    return ByteStreamBuffers.to_bytes(data, strict=True)
