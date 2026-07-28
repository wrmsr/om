"""
A 'pump' backend for `ByteStreamTransform`, letting transforms be authored as straight-line `async def` functions
against a `ByteStreamTransformContext` rather than as hand-written sans-IO state machines.

The authored function suspends on `ctx.read*` when input is not yet buffered and resumes as more is fed; `ctx.emit`
surfaces output through the enclosing `feed`/`finish` call. Suspension is mediated by private, ownership-tagged trap
objects cranked exclusively by the owning pump - this is strictly sans-IO: any foreign awaitable reaching the pump is
rejected, as there is no runtime present to serve it. Transform bodies are free to use async generators *internally*
(traps propagate transparently through `asend`/`__anext__` await chains) - only the top-level callable must be a plain
coroutine function, which the signature already enforces. One caution: do not await traps inside an async generator's
`finally` block, as an abandoned generator finalizing via GC has no pump present to answer it.

EOF semantics are defined here, once: after `finish`, reads resolve short then empty - like a file at EOF - and
`ctx.read_exact` raises `EOFError` at the await site. The function's return value becomes the transform's `result`,
and any input remaining or subsequently fed becomes `unused_data`.
"""
import typing as ta

from ... import check
from ... import lang
from ..streambufs.segmented import SegmentedByteStreamBuffer
from .types import BaseByteStreamTransform
from .types import StreamTransformError


R = ta.TypeVar('R')

ByteStreamTransformPumpFn: ta.TypeAlias = ta.Callable[['ByteStreamTransformContext'], ta.Coroutine[ta.Any, ta.Any, R]]


##


class ByteStreamTransformPumpError(StreamTransformError):
    pass


class ForeignYieldByteStreamTransformPumpError(ByteStreamTransformPumpError):
    """A transform body awaited something other than its own context's operations - it is not sans-IO."""


class UnawaitedTrapByteStreamTransformPumpError(ByteStreamTransformPumpError):
    """A trap was resumed by something other than its owning pump."""


##


@ta.final
class _ReadPumpTrap:
    def __init__(self, pump: PumpedByteStreamTransform, n: int | None) -> None:
        self.pump = pump
        self.n = n

    done: bool = False
    value: bytes = b''

    def __await__(self) -> ta.Generator[_ReadPumpTrap, None, bytes]:
        if not self.done:
            yield self
        if not self.done:
            raise UnawaitedTrapByteStreamTransformPumpError
        return self.value


@ta.final
class _EmitPumpTrap:
    def __init__(self, pump: PumpedByteStreamTransform, data: bytes) -> None:
        self.pump = pump
        self.data = data

    done: bool = False

    def __await__(self) -> ta.Generator[_EmitPumpTrap]:
        if not self.done:
            yield self
        if not self.done:
            raise UnawaitedTrapByteStreamTransformPumpError


@ta.final
class ByteStreamTransformContext:
    def __init__(self, pump: PumpedByteStreamTransform) -> None:
        self._pump = pump

    async def read(self, n: int | None = None, /) -> bytes:
        """
        Reads up to `n` bytes - exactly `n` unless end-of-input has been declared, in which case possibly short and
        `b''` thereafter. `read(None)` reads any non-empty amount, or `b''` at end-of-input.
        """

        if n is not None and n < 0:
            raise ValueError(n)
        return await _ReadPumpTrap(self._pump, n)

    async def read_exact(self, n: int, /) -> bytes:
        d = await self.read(n)
        if len(d) != n:
            raise EOFError(f'Expected {n} bytes, got {len(d)}')
        return d

    def unread(self, d: lang.BytesLike, /) -> None:
        """Pushes bytes back to be seen by subsequent reads - the `unused_data` dance for stream containers."""

        self._pump._unread(d)  # noqa

    async def emit(self, o: lang.BytesLike, /) -> None:
        """Emits transform output. Emitting empty bytes is a no-op - output chunks are always non-empty."""

        if not o:
            return
        if not isinstance(o, bytes):
            o = bytes(o)
        await _EmitPumpTrap(self._pump, o)


##


class PumpedByteStreamTransform(BaseByteStreamTransform[R], ta.Generic[R]):
    def __init__(self, fn: ByteStreamTransformPumpFn[R]) -> None:
        super().__init__()

        self._buf = SegmentedByteStreamBuffer()
        self._parked: _ReadPumpTrap | None = None

        self._ctx = ByteStreamTransformContext(self)
        self._cr = fn(self._ctx)
        self._g = iter(self._cr.__await__())

    def _unread(self, d: lang.BytesLike) -> None:
        if d:
            self._buf.prepend(d)

    def _take(self, n: int | None, *, at_eof: bool) -> bytes | None:
        buf = self._buf
        if n is None:
            if len(buf):
                return bytes(buf.split_to(len(buf)).tobytes())
            return b'' if at_eof else None

        if len(buf) >= n:
            return bytes(buf.split_to(n).tobytes())
        if at_eof:
            return bytes(buf.split_to(len(buf)).tobytes())
        return None

    def _crank(self, out: list[bytes], *, at_eof: bool) -> None:
        while True:
            if (t := self._parked) is not None:
                if (v := self._take(t.n, at_eof=at_eof)) is None:
                    return

                t.value = v
                t.done = True
                self._parked = None

            try:
                x = self._g.send(None)

            except StopIteration as e:
                self._complete(e.value)
                if len(self._buf):
                    self._stash_unused(self._buf.split_to(len(self._buf)).tobytes())
                return

            except BaseException:
                self.close()
                raise

            if isinstance(x, _ReadPumpTrap) and x.pump is self:
                check.state(not x.done)
                self._parked = x

            elif isinstance(x, _EmitPumpTrap) and x.pump is self:
                check.state(not x.done)
                x.done = True
                out.append(x.data)

            else:
                self.close()
                raise ForeignYieldByteStreamTransformPumpError(x)

    #

    def _feed(self, i: lang.BytesLike, /) -> ta.Sequence[bytes]:
        if i:
            self._buf.write(i)
        out: list[bytes] = []
        self._crank(out, at_eof=False)
        return out

    def _finish(self) -> ta.Sequence[bytes]:
        out: list[bytes] = []
        self._crank(out, at_eof=True)
        check.state(self._eof)  # reads always resolve at eof, so the coroutine must have completed or raised
        return out

    def _close(self) -> None:
        self._cr.close()
