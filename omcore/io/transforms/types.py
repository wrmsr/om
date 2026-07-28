"""
Incremental, sans-IO stream transforms.

A `StreamTransform` is a stateful, push-driven processor of a stream: callers `feed` it input and receive any resultant
output eagerly, then `finish` it to declare end-of-input and collect any tail output. It is the consumer-facing shape
for anything 'incremental codec'-like - compression, framing, parsing - regardless of how it is implemented internally
(directly, wrapping a stdlib incremental object, or as a pumped coroutine - see `pump.py`).

Core semantics:
 - `feed` never signals in-band: an empty input chunk is a no-op, not EOF. EOF is only ever declared via `finish`.
 - `eof` may become true *spontaneously* (a transform can reach its own natural end mid-stream - e.g. a decompressor
   seeing its trailer), distinct from `finish` which is the caller-side declaration.
 - For byte transforms, input fed beyond the transform's natural end accumulates as `unused_data` rather than raising -
   mirroring `zlib.decompressobj` semantics and enabling stream-concatenation / container use.
 - Truncation and malformed input surface as exceptions from `feed` or `finish` (`EOFError` for truncation, by stdlib
   precedent), typed per-transform.
"""
import abc
import typing as ta

from ... import lang


I = ta.TypeVar('I')
O = ta.TypeVar('O')
R = ta.TypeVar('R')
U = ta.TypeVar('U')

I_contra = ta.TypeVar('I_contra', contravariant=True)
O_co = ta.TypeVar('O_co', covariant=True)


##


class StreamTransformError(Exception):
    pass


class StreamTransformStateError(StreamTransformError):
    pass


class ClosedStreamTransformError(StreamTransformStateError):
    pass


class FinishedStreamTransformError(StreamTransformStateError):
    pass


##


class StreamTransform(lang.Abstract, ta.Generic[I_contra, O_co, R]):
    @property
    @abc.abstractmethod
    def eof(self) -> bool:
        """True once the transform has reached its own natural end - possibly before `finish` is called."""

        raise NotImplementedError

    @property
    @abc.abstractmethod
    def result(self) -> lang.Maybe[R]:
        """The transform's terminal value, present once `eof` is true."""

        raise NotImplementedError

    @abc.abstractmethod
    def feed(self, i: I_contra, /) -> ta.Sequence[O_co]:
        raise NotImplementedError

    @abc.abstractmethod
    def finish(self) -> ta.Sequence[O_co]:
        """Declares end-of-input. May be called at most once; `feed` afterwards raises."""

        raise NotImplementedError

    def close(self) -> None:
        pass

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class UnusedDataStreamTransform(lang.Abstract, ta.Generic[U]):
    """
    A transform which reports residual unconsumed input - input it accepted but which lies beyond what it ultimately
    processed. Populated once the transform has ended: at its natural eof (with input fed afterwards continuing to
    accumulate), or at finish (such as a decoder's still-undecoded tail - readable even when finish raises).
    """

    @property
    @abc.abstractmethod
    def unused_data(self) -> U:
        raise NotImplementedError


class ByteStreamTransform(
    StreamTransform[lang.BytesLike, bytes, R],
    UnusedDataStreamTransform[bytes],
    lang.Abstract,
    ta.Generic[R],
):
    pass


##


class BaseStreamTransform(StreamTransform[I_contra, O_co, R], lang.Abstract):
    _closed = False
    _finished = False
    _eof = False

    _result: lang.Maybe[R] = lang.empty()

    @property
    def eof(self) -> bool:
        return self._eof

    @property
    def result(self) -> lang.Maybe[R]:
        return self._result

    def _complete(self, value: R) -> None:
        self._eof = True
        self._result = lang.just(value)

    #

    @abc.abstractmethod
    def _feed(self, i: I_contra, /) -> ta.Sequence[O_co]:
        raise NotImplementedError

    def _feed_eofed(self, i: I_contra, /) -> ta.Sequence[O_co]:
        raise StreamTransformStateError('feed after eof')

    @abc.abstractmethod
    def _finish(self) -> ta.Sequence[O_co]:
        raise NotImplementedError

    def _close(self) -> None:
        pass

    #

    def feed(self, i: I_contra, /) -> ta.Sequence[O_co]:
        if self._closed:
            raise ClosedStreamTransformError
        if self._finished:
            raise FinishedStreamTransformError
        if self._eof:
            return self._feed_eofed(i)
        return self._feed(i)

    def finish(self) -> ta.Sequence[O_co]:
        if self._closed:
            raise ClosedStreamTransformError
        if self._finished:
            raise FinishedStreamTransformError
        self._finished = True
        if self._eof:
            return ()
        return self._finish()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._close()


class BaseByteStreamTransform(BaseStreamTransform[lang.BytesLike, bytes, R], ByteStreamTransform[R], lang.Abstract):
    def __init__(self) -> None:
        super().__init__()

        self._unused = bytearray()

    @property
    def unused_data(self) -> bytes:
        return bytes(self._unused)

    def _stash_unused(self, d: lang.BytesLike, /) -> None:
        if d:
            self._unused += d

    def _feed_eofed(self, i: lang.BytesLike, /) -> ta.Sequence[bytes]:
        self._stash_unused(i)
        return ()
