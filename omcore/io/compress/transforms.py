import typing as ta

from ... import lang
from ..transforms.types import BaseByteStreamTransform
from .abc import CompressorObject
from .abc import DecompressorObject


##


class CompressorObjectByteStreamTransform(BaseByteStreamTransform[None]):
    """Adapts a `compressobj`-shaped object (zlib/bz2/lzma) to a `ByteStreamTransform`."""

    def __init__(self, obj: CompressorObject) -> None:
        super().__init__()

        self._obj = obj

    def _feed(self, i: lang.BytesLike, /) -> ta.Sequence[bytes]:
        if not i:
            return ()
        if (c := self._obj.compress(i)):  # type: ignore[arg-type]  # accepts any buffer
            return (c,)
        return ()

    def _finish(self) -> ta.Sequence[bytes]:
        f = self._obj.flush()
        self._complete(None)
        if f:
            return (f,)
        return ()


##


class DecompressorObjectByteStreamTransform(BaseByteStreamTransform[None]):
    """
    Adapts a `decompressobj`-shaped object (zlib/bz2/lzma) to a `ByteStreamTransform`, decompressing a sequence of
    concatenated streams like the stdlib file wrappers do. Data after the end of a stream that does not begin a valid
    new stream ends the transform, with it and everything after it accumulating as `unused_data`.
    """

    def __init__(
            self,
            factory: ta.Callable[..., DecompressorObject],
            *,
            trailing_error: type[BaseException] | tuple[type[BaseException], ...] = (),
    ) -> None:
        super().__init__()

        self._factory = factory
        self._trailing_error = trailing_error

        self._obj = factory()

    def _feed(self, i: lang.BytesLike, /) -> ta.Sequence[bytes]:
        out: list[bytes] = []
        data: lang.BytesLike = i

        while True:
            if self._obj.eof:
                rest = self._obj.unused_data
                if rest and data:
                    data = rest + (bytes(data) if isinstance(data, memoryview) else data)
                elif rest:
                    data = rest
                if not data:
                    # Cleanly at a stream boundary - whether another stream follows is decided by later input.
                    return out

                nobj = self._factory()
                try:
                    d = nobj.decompress(data)  # type: ignore[arg-type]  # accepts any buffer
                except self._trailing_error:
                    self._complete(None)
                    self._stash_unused(data)
                    return out
                self._obj = nobj

            else:
                if not data:
                    return out
                d = self._obj.decompress(data)  # type: ignore[arg-type]  # accepts any buffer

            if d:
                out.append(d)
            data = b''

    def _finish(self) -> ta.Sequence[bytes]:
        if self._obj.eof:
            self._complete(None)
            return ()
        raise EOFError('Compressed file ended before the end-of-stream marker was reached')
