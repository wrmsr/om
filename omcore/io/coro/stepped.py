import itertools
import typing as ta

from ... import check
from ... import lang
from ..streambufs.segmented import SegmentedByteStreamBuffer
from .direct import BytesDirectCoro
from .direct import StrDirectCoro


T = ta.TypeVar('T')

O = ta.TypeVar('O')
I = ta.TypeVar('I')
R = ta.TypeVar('R')

OF = ta.TypeVar('OF')
OT = ta.TypeVar('OT')


# Stepped coros accept a non-None input, then in response yield zero or more non-None outputs, until yielding None to
# signal they need more input again.
SteppedCoro: ta.TypeAlias = ta.Generator[O | None, I | None, R]

# Conventionally, these are sent and themselves yield an empty value to signify termination.
BytesSteppedCoro: ta.TypeAlias = SteppedCoro[lang.Bytes, lang.Bytes, R]
StrSteppedCoro: ta.TypeAlias = SteppedCoro[str, str, R]

BytesToStrSteppedCoro: ta.TypeAlias = SteppedCoro[str, lang.Bytes, R]
StrToBytesSteppedCoro: ta.TypeAlias = SteppedCoro[lang.Bytes, str, R]


# Stepped reader generators emit either an int or None to request input, or emit some other kind of output.
SteppedReaderCoro: ta.TypeAlias = ta.Generator[int | None | O, I | None, R]

BytesSteppedReaderCoro: ta.TypeAlias = SteppedReaderCoro[lang.Bytes, lang.Bytes, R]
StrSteppedReaderCoro: ta.TypeAlias = SteppedReaderCoro[str, str, R]


##


@lang.autostart
def flatmap_stepped_coro(
        fn: ta.Callable[[list[OF]], OT],
        g: SteppedCoro[OF, I, R],
        *,
        terminate: ta.Callable[[OF], bool] | None = None,
) -> ta.Generator[OT, I, lang.Maybe[R]]:
    """
    Given a stepped coro and a function taking a list, returns a direct (1:1) coro which accepts input, builds a list of
    yielded coro output, calls the given function with that list, and yields the result.

    An optional terminate function may be provided which will cause this function to return early if it returns true for
    an encountered yielded value. The encountered value causing termination will be included in the list sent to the
    given fn.

    Returns a Maybe of either the given coro's return value or empty if the terminator was encountered.
    """

    l: list[OF]
    i: I | None = yield  # type: ignore
    while True:
        l = []

        while True:
            try:
                o = g.send(i)
            except StopIteration as e:
                if l:
                    yield fn(l)
                return lang.just(e.value)

            i = None

            if o is None:
                break

            l.append(o)

            if terminate is not None and terminate(o):
                yield fn(l)
                return lang.empty()

        i = yield fn(l)


##


def _join_bytes(l: ta.Sequence[lang.Bytes]) -> lang.Bytes:
    if not l:
        return b''
    elif len(l) == 1:
        return l[0]
    else:
        return b''.join(l)


def _join_str(l: ta.Sequence[str]) -> str:
    if not l:
        return ''
    elif len(l) == 1:
        return l[0]
    else:
        return ''.join(l)


def _is_empty(o: T) -> bool:
    return len(o) < 1  # type: ignore


def joined_bytes_stepped_coro(g: BytesSteppedCoro[R]) -> BytesDirectCoro[R]:
    return flatmap_stepped_coro(_join_bytes, g, terminate=_is_empty)


def joined_str_stepped_coro(g: StrSteppedCoro[R]) -> StrDirectCoro[R]:
    return flatmap_stepped_coro(_join_str, g, terminate=_is_empty)


##


DEFAULT_BUFFER_SIZE = 4 * 0x1000


def read_into_bytes_stepped_coro(
        g: BytesSteppedCoro,
        f: ta.IO,
        *,
        read_size: int = DEFAULT_BUFFER_SIZE,
) -> ta.Iterator[lang.Bytes]:
    yield from lang.genmap(  # type: ignore[misc]
        joined_bytes_stepped_coro(g),
        # The trailing empty is the coro protocol's termination signal, prompting the final flush.
        itertools.chain(lang.readiter(f, read_size), [b'']),
    )


def read_into_str_stepped_coro(
        g: StrSteppedCoro,
        f: ta.TextIO,
        *,
        read_size: int = DEFAULT_BUFFER_SIZE,
) -> ta.Iterator[str]:
    yield from lang.genmap(
        joined_str_stepped_coro(g),
        # The trailing empty is the coro protocol's termination signal, prompting the final flush.
        itertools.chain(lang.readiter(f, read_size), ['']),
    )


##


@lang.autostart
def buffer_bytes_stepped_reader_coro(
        g: BytesSteppedReaderCoro,
        *,
        buffer_chunk_size: int = 16 * 1024,
) -> BytesSteppedCoro:
    """
    Adapts a reader coro to the stepped coro protocol, buffering input to satisfy the reader's sized requests. Once the
    terminal empty input has been received, requests beyond the buffered data are answered with short or empty reads -
    like a file at EOF - leaving it to the reader to decide whether that constitutes an error.
    """

    i: lang.Bytes | None
    o = g.send(None)
    buf = SegmentedByteStreamBuffer(chunk_size=buffer_chunk_size)
    eof = False

    while True:
        if o is None:
            if not len(buf) and not eof:
                if (more := check.isinstance((yield None), lang.BYTES_TYPES)):
                    buf.write(more)
                else:
                    eof = True

            i = buf.split_to(len(buf)).tobytes()

        elif isinstance(o, int):
            while len(buf) < o and not eof:
                if (more := check.isinstance((yield None), lang.BYTES_TYPES)):
                    buf.write(more)
                else:
                    eof = True

            i = buf.split_to(min(o, len(buf))).tobytes()

        else:
            raise TypeError(o)

        while True:
            o = g.send(i)
            i = None
            if isinstance(o, lang.BYTES_TYPES):
                check.none((yield o))
                if not o:
                    return
            else:
                break


##


@lang.autostart
def iterable_bytes_stepped_coro(g: BytesSteppedCoro) -> ta.Generator[ta.Iterator[lang.Bytes], lang.Bytes]:
    i: lang.Bytes | None = check.isinstance((yield None), lang.BYTES_TYPES)  # type: ignore[misc]
    eof = False

    def f() -> ta.Iterator[lang.Bytes]:
        nonlocal i
        while True:
            o = g.send(i)
            i = None

            if isinstance(o, lang.BYTES_TYPES):
                yield o
                if not o:
                    nonlocal eof
                    eof = True
                    return
            elif o is None:
                return
            else:
                raise TypeError(o)

    while True:
        if eof:
            return

        i = (yield f())  # noqa
