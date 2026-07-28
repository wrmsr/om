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
    import lzma
else:
    lzma = lang.proxy_import('lzma')


##


@dc.dataclass(frozen=True, kw_only=True)
class LzmaCompression(Compression, IncrementalCompression):
    format: int | None = None

    check: int = -1
    preset: int | None = None
    filters: dict | None = None

    mem_limit: int | None = None

    def compress(self, d: lang.Bytes) -> lang.Bytes:
        return lzma.compress(
            d,
            format=self.format if self.format is not None else lzma.FORMAT_XZ,
            check=self.check,
            preset=self.preset,
            filters=self.filters,  # type: ignore[arg-type]
        )

    def decompress(self, d: lang.Bytes) -> lang.Bytes:
        return lzma.decompress(
            d,
            format=self.format if self.format is not None else lzma.FORMAT_AUTO,
            memlimit=self.mem_limit,
            filters=self.filters,  # type: ignore[arg-type]
        )

    def compress_incremental(self) -> ByteStreamTransform[None]:
        return CompressorObjectByteStreamTransform(lzma.LZMACompressor(
            format=self.format if self.format is not None else lzma.FORMAT_XZ,
            check=self.check,
            preset=self.preset,
            filters=self.filters,  # type: ignore[arg-type]
        ))

    def decompress_incremental(self) -> ByteStreamTransform[None]:
        return DecompressorObjectByteStreamTransform(
            lambda: lzma.LZMADecompressor(  # type: ignore[arg-type, return-value]
                format=self.format if self.format is not None else lzma.FORMAT_AUTO,
                memlimit=self.mem_limit,
                filters=self.filters,  # type: ignore[arg-type]
            ),
            trailing_error=lzma.LZMAError,
        )


##


LZMA_CODEC = make_compression_codec('lzma', LzmaCompression)

# @om-manifest
_LZMA_LAZY_CODEC = make_compression_lazy_loaded_codec(__name__, 'LZMA_CODEC', LZMA_CODEC)
