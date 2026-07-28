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
    import zlib
else:
    zlib = lang.proxy_import('zlib')


##


@dc.dataclass(frozen=True, kw_only=True)
class ZlibCompression(Compression, IncrementalCompression):
    level: int = 9

    wbits: int | None = None
    strategy: int | None = None
    zdict: lang.Bytes | None = None

    def compress(self, d: lang.Bytes) -> lang.Bytes:
        return zlib.compress(
            d,
            self.level,
            **(dict(wbits=self.wbits) if self.wbits is not None else {}),
        )

    def decompress(self, d: lang.Bytes) -> lang.Bytes:
        return zlib.decompress(
            d,
            **(dict(wbits=self.wbits) if self.wbits is not None else {}),
        )

    def compress_incremental(self) -> ByteStreamTransform[None]:
        return CompressorObjectByteStreamTransform(zlib.compressobj(
            self.level,
            **(dict(wbits=self.wbits) if self.wbits is not None else {}),  # type: ignore[arg-type]
            **(dict(strategy=self.strategy) if self.strategy is not None else {}),  # type: ignore[arg-type]
            **(dict(zdict=self.zdict) if self.zdict is not None else {}),  # type: ignore[arg-type]
        ))

    def decompress_incremental(self) -> ByteStreamTransform[None]:
        return DecompressorObjectByteStreamTransform(
            lambda: zlib.decompressobj(  # type: ignore[arg-type, return-value]
                **(dict(wbits=self.wbits) if self.wbits is not None else {}),  # type: ignore[arg-type]
                **(dict(zdict=self.zdict) if self.zdict is not None else {}),  # type: ignore[arg-type]
            ),
            trailing_error=zlib.error,  # zlib.error subclasses Exception, not OSError like bz2's errors
        )


##


ZLIB_CODEC = make_compression_codec('zlib', ZlibCompression)

# @om-manifest
_ZLIB_LAZY_CODEC = make_compression_lazy_loaded_codec(__name__, 'ZLIB_CODEC', ZLIB_CODEC)
