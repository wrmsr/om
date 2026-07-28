import typing as ta

from .types import StreamTransform


I = ta.TypeVar('I')
O = ta.TypeVar('O')


##


def run_stream_transform(
        t: StreamTransform[I, O, ta.Any],
        it: ta.Iterable[I],
) -> ta.Iterator[O]:
    """Feeds each item of `it` through the transform, yielding outputs, finishing (and closing) it at the end."""

    with t:
        for i in it:
            yield from t.feed(i)
        yield from t.finish()
