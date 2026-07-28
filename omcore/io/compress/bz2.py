import dataclasses as dc
import typing as ta

from ... import lang
from ..transforms.types import ByteStreamTransform
from .base import Compression
from .base import IncrementalCompression
from .codecs import make_compression_codec
from .codecs import make_compression_lazy_loaded_codec
from .transforms import CompressorObjectByteStreamTransform
from .transforms import DecompressorObjectByteStreamTransform


if ta.TYPE_CHECKING:
    import bz2
else:
    bz2 = lang.proxy_import('bz2')


##


@dc.dataclass(frozen=True, kw_only=True)
class Bz2Compression(Compression, IncrementalCompression):
    level: int = 9

    def compress(self, d: lang.Bytes) -> lang.Bytes:
        return bz2.compress(
            d,
            self.level,
        )

    def decompress(self, d: lang.Bytes) -> lang.Bytes:
        return bz2.decompress(
            d,
        )

    def compress_incremental(self) -> ByteStreamTransform[None]:
        return CompressorObjectByteStreamTransform(bz2.BZ2Compressor(  # type: ignore[arg-type]
            self.level,
        ))

    def decompress_incremental(self) -> ByteStreamTransform[None]:
        return DecompressorObjectByteStreamTransform(
            bz2.BZ2Decompressor,  # type: ignore[arg-type]
            trailing_error=OSError,
        )


##


BZ2_CODEC = make_compression_codec('bz2', Bz2Compression)

# @om-manifest
_BZ2_LAZY_CODEC = make_compression_lazy_loaded_codec(__name__, 'BZ2_CODEC', BZ2_CODEC)
