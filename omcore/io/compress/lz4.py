import dataclasses as dc
import typing as ta

from ... import lang
from ..transforms.types import BaseByteStreamTransform
from ..transforms.types import ByteStreamTransform
from .base import Compression
from .base import IncrementalCompression
from .codecs import make_compression_codec
from .codecs import make_compression_lazy_loaded_codec


if ta.TYPE_CHECKING:
    import lz4.frame as lz4_frame
else:
    lz4_frame = lang.proxy_import('lz4.frame')


##


class _Lz4CompressorByteStreamTransform(BaseByteStreamTransform[None]):
    def __init__(self, compressor: ta.Any) -> None:
        super().__init__()

        self._compressor = compressor
        self._started = False

    def _begin(self) -> bytes:
        self._started = True
        return self._compressor.begin()

    def _feed(self, i: lang.BytesLike, /) -> ta.Sequence[bytes]:
        out: list[bytes] = []
        if not self._started:
            out.append(self._begin())
        if i and (o := self._compressor.compress(i)):
            out.append(o)
        return out

    def _finish(self) -> ta.Sequence[bytes]:
        out: list[bytes] = []
        if not self._started:
            out.append(self._begin())
        if (o := self._compressor.flush()):
            out.append(o)
        self._complete(None)
        return out


class _Lz4DecompressorByteStreamTransform(BaseByteStreamTransform[None]):
    def __init__(self, decompressor: ta.Any) -> None:
        super().__init__()

        self._decompressor = decompressor

    def _feed(self, i: lang.BytesLike, /) -> ta.Sequence[bytes]:
        if i and (o := self._decompressor.decompress(i)):
            return (o,)
        return ()

    def _finish(self) -> ta.Sequence[bytes]:
        self._complete(None)
        return ()


##


@dc.dataclass(frozen=True, kw_only=True)
class Lz4Compression(Compression, IncrementalCompression):
    level: int = 0

    block_size: int = 0
    block_linked: bool = True
    block_checksum: bool = False
    content_checksum: bool = False
    store_size: bool = True
    auto_flush: bool = False

    def compress(self, d: lang.Bytes) -> lang.Bytes:
        return lz4_frame.compress(
            d,
            compression_level=self.level,
            block_size=self.block_size,
            content_checksum=self.content_checksum,
            block_linked=self.block_linked,
            store_size=self.store_size,
        )

    def decompress(self, d: lang.Bytes) -> lang.Bytes:
        return lz4_frame.decompress(
            d,
        )

    def compress_incremental(self) -> ByteStreamTransform[None]:
        return _Lz4CompressorByteStreamTransform(lz4_frame.LZ4FrameCompressor(
            compression_level=self.level,
            block_size=self.block_size,
            block_linked=self.block_linked,
            block_checksum=self.block_checksum,
            content_checksum=self.content_checksum,
            auto_flush=self.auto_flush,
        ))

    def decompress_incremental(self) -> ByteStreamTransform[None]:
        return _Lz4DecompressorByteStreamTransform(lz4_frame.LZ4FrameDecompressor())


##


LZ4_CODEC = make_compression_codec('lz4', Lz4Compression)

# @om-manifest
_LZ4_LAZY_CODEC = make_compression_lazy_loaded_codec(__name__, 'LZ4_CODEC', LZ4_CODEC)
