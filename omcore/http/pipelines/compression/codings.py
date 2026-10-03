# ruff: noqa: UP006 UP045
# @om-lite
import abc
import typing as ta
import zlib

from ....lite.abstract import Abstract
from ....lite.bytes import BytesLike
from ....lite.cached import cached_nullary
from ....lite.check import check
from ....lite.imports import can_import
from ....lite.namespaces import NamespaceClass


##


class IoPipelineHttpCompressionCodingUnavailableError(Exception):
    """Raised constructing a coding whose backing library is not importable."""


class IoPipelineHttpDecompressionError(Exception):
    """
    Malformed compressed input. Decompressor codings raise this in place of their backing library's own error, after
    which they are spent.
    """


##


class IoPiplineHttpCompressorCoding(Abstract):
    @classmethod
    def is_available(cls) -> bool:
        return True

    @abc.abstractmethod
    def compress(
            self,
            data: BytesLike,
            /,
    ) -> ta.Optional[BytesLike]:
        raise NotImplementedError

    def flush(self) -> ta.Optional[BytesLike]:
        return None

    @abc.abstractmethod
    def finish(self) -> ta.Optional[BytesLike]:
        raise NotImplementedError


IoPiplineHttpCompressorCodings = ta.Mapping[  # ta.TypeAlias  # om-amalg-typing-no-move
    str,
    ta.Callable[[], IoPiplineHttpCompressorCoding],
]


#


class IoPiplineHttpDecompressorCoding(Abstract):
    """
    An incremental decompressor for one content coding, shaped after the stdlib's bz2 / lzma / zstd decompressor
    objects rather than zlib's.

    `decompress` returns at most `max_bytes` of output. When more was ready than fit, `needs_input` is False and
    `decompress` must be called with empty data to drain it before being given any further input. There is no separate
    finishing step: once `eof` all output has been returned, and a stream which never reaches `eof` was truncated.
    """

    @classmethod
    def is_available(cls) -> bool:
        return True

    @abc.abstractmethod
    def decompress(
            self,
            data: BytesLike,
            max_bytes: ta.Optional[int] = None,
            /,
    ) -> ta.Optional[BytesLike]:
        """Raises IoPipelineHttpDecompressionError on malformed input."""

        raise NotImplementedError

    @abc.abstractmethod
    def needs_input(self) -> bool:
        """False while output is pending which the last `decompress` could not return within its `max_bytes`."""

        raise NotImplementedError

    @abc.abstractmethod
    def eof(self) -> bool:
        """Whether the end of the compressed stream has been reached and all of its output returned."""

        raise NotImplementedError

    @abc.abstractmethod
    def unused_data(self) -> ta.Optional[BytesLike]:
        """
        Bytes found past the end of the compressed stream. Only meaningful once `eof` - for codings whose streams are
        concatenable (notably gzip, per RFC 1952 §2.2) these are the start of the following member. None for codings
        which cannot separate them.
        """

        raise NotImplementedError


IoPiplineHttpDecompressorCodings = ta.Mapping[  # ta.TypeAlias  # om-amalg-typing-no-move
    str,
    ta.Callable[[], IoPiplineHttpDecompressorCoding],
]


##


class ZlibIoPiplineHttpCompressorCoding(IoPiplineHttpCompressorCoding):
    def __init__(self, wbits: int = 16 + zlib.MAX_WBITS) -> None:
        super().__init__()

        self._z = zlib.compressobj(wbits=wbits)

    def compress(
            self,
            data: BytesLike,
            /,
    ) -> ta.Optional[BytesLike]:
        return self._z.compress(data)

    def flush(self) -> ta.Optional[BytesLike]:
        return self._z.flush(zlib.Z_SYNC_FLUSH) or None

    def finish(self) -> ta.Optional[BytesLike]:
        return self._z.flush()


class ZlibIoPiplineHttpDecompressorCoding(IoPiplineHttpDecompressorCoding):
    def __init__(self, wbits: int = 16 + zlib.MAX_WBITS) -> None:
        super().__init__()

        self._z = zlib.decompressobj(wbits)

    def decompress(
            self,
            data: BytesLike,
            max_bytes: ta.Optional[int] = None,
            /,
    ) -> ta.Optional[BytesLike]:
        # Input zlib could not fit the output of within the limit is handed back as unconsumed_tail rather than kept,
        # so it is re-fed here - which is why no new input may be given until it has been drained.
        if (tail := self._z.unconsumed_tail):
            check.arg(not data)
            data = tail

        try:
            return self._z.decompress(data, max_bytes or 0)
        except zlib.error as e:
            raise IoPipelineHttpDecompressionError(str(e)) from e

    def needs_input(self) -> bool:
        return not self._z.unconsumed_tail

    def eof(self) -> bool:
        return self._z.eof

    def unused_data(self) -> ta.Optional[BytesLike]:
        return self._z.unused_data


##


@cached_nullary
def _can_import_brotli() -> bool:
    return can_import('brotli')


class BrotliIoPiplineHttpCompressorCoding(IoPiplineHttpCompressorCoding):
    @classmethod
    def is_available(cls) -> bool:
        return _can_import_brotli()

    def __init__(self, *, quality: ta.Optional[int] = None) -> None:
        super().__init__()

        if not self.is_available():
            raise IoPipelineHttpCompressionCodingUnavailableError('brotli')

        import brotli  # noqa

        self._c = brotli.Compressor(**(dict(quality=quality) if quality is not None else {}))

    def compress(
            self,
            data: BytesLike,
            /,
    ) -> ta.Optional[BytesLike]:
        return self._c.process(data)

    def flush(self) -> ta.Optional[BytesLike]:
        return self._c.flush() or None

    def finish(self) -> ta.Optional[BytesLike]:
        return self._c.finish()


class BrotliIoPiplineHttpDecompressorCoding(IoPiplineHttpDecompressorCoding):
    """
    Two of brotli's quirks are hidden here. Its output limit is soft - it stops growing its buffer only once at or past
    the limit, overshooting by up to an internal block - so the excess is withheld and returned by later drain calls.
    And `can_accept_more_data` reports only withheld *input*, saying nothing of pending output, so a call which reached
    its limit without finishing is taken to mean more is pending.

    Brotli has no notion of data past the end of a stream: trailing bytes are a decode error, lost output and all.
    """

    @classmethod
    def is_available(cls) -> bool:
        return _can_import_brotli()

    def __init__(self) -> None:
        super().__init__()

        if not self.is_available():
            raise IoPipelineHttpCompressionCodingUnavailableError('brotli')

        import brotli  # noqa

        self._brotli = brotli
        self._d = brotli.Decompressor()

        self._withheld: ta.Optional[memoryview] = None
        self._more = False

    def decompress(
            self,
            data: BytesLike,
            max_bytes: ta.Optional[int] = None,
            /,
    ) -> ta.Optional[BytesLike]:
        if (w := self._withheld) is not None:
            check.arg(not data)
            if max_bytes and len(w) > max_bytes:
                self._withheld = w[max_bytes:]
                return w[:max_bytes]
            self._withheld = None
            return w

        try:
            if max_bytes:
                out = self._d.process(data, output_buffer_limit=max_bytes)
            else:
                out = self._d.process(data)
        except self._brotli.error as e:
            raise IoPipelineHttpDecompressionError(str(e)) from e

        if not max_bytes:
            self._more = False
            return out

        self._more = len(out) >= max_bytes and not self._d.is_finished()
        if len(out) > max_bytes:
            mv = memoryview(out)
            self._withheld = mv[max_bytes:]
            return mv[:max_bytes]
        return out

    def needs_input(self) -> bool:
        return self._withheld is None and not self._more and self._d.can_accept_more_data()

    def eof(self) -> bool:
        return self._withheld is None and self._d.is_finished()

    def unused_data(self) -> ta.Optional[BytesLike]:
        return None


##


@cached_nullary
def _can_import_zstd() -> bool:
    return can_import('compression.zstd')


class ZstdIoPiplineHttpCompressorCoding(IoPiplineHttpCompressorCoding):
    """Via the stdlib `compression.zstd` module, present from python 3.14."""

    @classmethod
    def is_available(cls) -> bool:
        return _can_import_zstd()

    def __init__(self, *, level: ta.Optional[int] = None) -> None:
        super().__init__()

        if not self.is_available():
            raise IoPipelineHttpCompressionCodingUnavailableError('compression.zstd')

        from compression import zstd  # noqa

        self._c = zstd.ZstdCompressor(level=level)

    def compress(
            self,
            data: BytesLike,
            /,
    ) -> ta.Optional[BytesLike]:
        return self._c.compress(data)

    def flush(self) -> ta.Optional[BytesLike]:
        return self._c.flush(self._c.FLUSH_BLOCK) or None

    def finish(self) -> ta.Optional[BytesLike]:
        return self._c.flush(self._c.FLUSH_FRAME)


class ZstdIoPiplineHttpDecompressorCoding(IoPiplineHttpDecompressorCoding):
    """Via the stdlib `compression.zstd` module, present from python 3.14."""

    @classmethod
    def is_available(cls) -> bool:
        return _can_import_zstd()

    def __init__(self) -> None:
        super().__init__()

        if not self.is_available():
            raise IoPipelineHttpCompressionCodingUnavailableError('compression.zstd')

        from compression import zstd  # noqa

        self._zstd = zstd
        self._d = zstd.ZstdDecompressor()

    def decompress(
            self,
            data: BytesLike,
            max_bytes: ta.Optional[int] = None,
            /,
    ) -> ta.Optional[BytesLike]:
        try:
            # A max_length of 0 means zero bytes, not unlimited.
            return self._d.decompress(data, max_bytes or -1)
        except (self._zstd.ZstdError, EOFError) as e:
            raise IoPipelineHttpDecompressionError(str(e)) from e

    def needs_input(self) -> bool:
        # Past the end of a frame zstd keeps reporting needs_input False yet raises EOFError if drained.
        return self._d.eof or self._d.needs_input

    def eof(self) -> bool:
        return self._d.eof

    def unused_data(self) -> ta.Optional[BytesLike]:
        return self._d.unused_data


##


class DefaultIoPiplineHttpCompressionCodings(NamespaceClass):
    """
    Keyed by content-coding name. Codings whose backing library is absent raise
    IoPipelineHttpCompressionCodingUnavailableError on construction - `is_available` tells in advance.
    """

    COMPRESSOR: ta.Final[IoPiplineHttpCompressorCodings] = {
        'gzip': ZlibIoPiplineHttpCompressorCoding,
        'br': BrotliIoPiplineHttpCompressorCoding,
        'zstd': ZstdIoPiplineHttpCompressorCoding,
    }

    DECOMPRESSOR: ta.Final[IoPiplineHttpDecompressorCodings] = {
        'gzip': ZlibIoPiplineHttpDecompressorCoding,
        'br': BrotliIoPiplineHttpDecompressorCoding,
        'zstd': ZstdIoPiplineHttpDecompressorCoding,
    }
