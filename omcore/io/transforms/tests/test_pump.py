import typing as ta

import pytest

from .... import lang
from ..funcs import run_stream_transform
from ..pump import ForeignYieldByteStreamTransformPumpError
from ..pump import PumpedByteStreamTransform
from ..types import ClosedStreamTransformError
from ..types import FinishedStreamTransformError


async def _echo(ctx):
    while (d := await ctx.read()):
        await ctx.emit(d)


def test_echo():
    t = PumpedByteStreamTransform(_echo)
    assert t.feed(b'abc') == [b'abc']
    assert t.feed(b'') == []
    assert t.feed(b'de') == [b'de']
    assert t.result == lang.empty()
    assert t.finish() == []
    assert t.eof
    assert t.result == lang.just(None)


def test_run_helper():
    assert list(run_stream_transform(PumpedByteStreamTransform(_echo), [b'ab', b'', b'c'])) == [b'ab', b'c']


def test_read_parking_across_feeds():
    async def f(ctx):
        d = await ctx.read_exact(4)
        await ctx.emit(d.upper())
        return len(d)

    t = PumpedByteStreamTransform(f)
    assert t.feed(b'ab') == []
    assert t.feed(b'c') == []
    assert t.feed(b'defg') == [b'ABCD']
    assert t.eof
    assert t.result == lang.just(4)

    # Input past the transform's natural end accumulates as unused_data.
    assert t.unused_data == b'efg'
    assert not t.feed(b'hi')
    assert t.unused_data == b'efghi'


def test_read_exact_eof():
    async def f(ctx):
        await ctx.read_exact(4)

    t = PumpedByteStreamTransform(f)
    assert t.feed(b'ab') == []
    with pytest.raises(EOFError):
        t.finish()


def test_eof_short_then_empty_reads():
    async def f(ctx):
        assert await ctx.read(4) == b'ab'
        assert await ctx.read(4) == b''
        assert await ctx.read() == b''
        return 'done'

    t = PumpedByteStreamTransform(f)
    assert t.feed(b'ab') == []
    assert t.finish() == []
    assert t.result == lang.just('done')


def test_unread():
    async def f(ctx):
        d = await ctx.read_exact(3)
        ctx.unread(d[1:])
        await ctx.emit(await ctx.read_exact(2))

    t = PumpedByteStreamTransform(f)
    assert t.feed(b'abc') == [b'bc']


def test_emit_empty_is_noop():
    async def f(ctx):
        await ctx.emit(b'')
        await ctx.emit(b'x')
        await ctx.read()

    t = PumpedByteStreamTransform(f)
    assert t.feed(b'y') == [b'x']


def test_state_guards():
    t = PumpedByteStreamTransform(_echo)
    t.finish()
    with pytest.raises(FinishedStreamTransformError):
        t.feed(b'x')
    t.close()
    with pytest.raises(ClosedStreamTransformError):
        t.finish()


def test_foreign_yield_rejected():
    class Foreign:
        def __await__(self) -> ta.Any:
            yield self

    async def f(ctx):
        await Foreign()

    t = PumpedByteStreamTransform(f)
    with pytest.raises(ForeignYieldByteStreamTransformPumpError):
        t.feed(b'x')
    with pytest.raises(ClosedStreamTransformError):
        t.feed(b'x')


def test_body_exception_propagates_and_closes():
    async def f(ctx):
        await ctx.read_exact(1)
        raise ValueError('nope')

    t = PumpedByteStreamTransform(f)
    with pytest.raises(ValueError, match='nope'):
        t.feed(b'x')
    with pytest.raises(ClosedStreamTransformError):
        t.feed(b'x')


def test_internal_async_generator():
    # Transform bodies are free to use async generators internally - traps propagate transparently through the
    # asend/__anext__ await chains, and the pump cannot (and need not) tell.
    async def chunks(ctx, n):
        while (d := await ctx.read(n)):
            yield d

    async def f(ctx):
        async for c in chunks(ctx, 2):
            await ctx.emit(bytes(reversed(c)))

    t = PumpedByteStreamTransform(f)
    assert t.feed(b'abcd') == [b'ba', b'dc']
    assert t.feed(b'e') == []
    assert t.finish() == [b'e']


def test_preamble_emitted_on_first_feed():
    async def f(ctx):
        await ctx.emit(b'hdr')
        while (d := await ctx.read()):
            await ctx.emit(d)

    t = PumpedByteStreamTransform(f)
    assert t.feed(b'x') == [b'hdr', b'x']


def test_finish_only():
    async def f(ctx):
        await ctx.emit(b'hdr')
        while (d := await ctx.read()):
            await ctx.emit(d)
        await ctx.emit(b'tail')

    t = PumpedByteStreamTransform(f)
    assert t.finish() == [b'hdr', b'tail']
