import pytest

from ... import lang
from ..iterators import PeekIterator
from ..iterators import PrefetchIterator
from ..iterators import ProxyIterator
from ..iterators import RetainIterator


def test_peek_iterator():
    it = PeekIterator([1, 2, 3, 4, 5])

    assert it.peek() == 1
    assert it.peek() == 1
    assert next(it) == 1
    assert it.maybe_peek() == lang.just(2)
    assert list(it.take_until(lambda v: v >= 3)) == [2]
    assert next(it) == 3
    assert it.next_peek() == 5
    assert next(it) == 5
    assert it.done
    assert it.maybe_peek() == lang.nothing()


def test_peek_iterator_take_and_skip_through_exhaustion():
    assert list(PeekIterator([1, 2]).take_while(lambda _: True)) == [1, 2]

    it = PeekIterator([1, 2])
    it.skip_while(lambda _: True)
    assert it.done


def test_proxy_iterator():
    src = iter([1, 2])
    it = ProxyIterator(src.__next__)

    assert iter(it) is it
    assert list(it) == [1, 2]


def test_prefetch_iterator():
    src = iter([3, 4])
    it = PrefetchIterator(src.__next__)
    it.push(1)
    it.push(2)

    assert list(it) == [1, 2, 3, 4]

    empty: PrefetchIterator[int] = PrefetchIterator()
    with pytest.raises(StopIteration):
        next(empty)


def test_retain_iterator():
    src = iter([1, 2])
    it = RetainIterator(src.__next__)

    assert list(it) == [1, 2]
    it.pop()
    it.pop()
    with pytest.raises(IndexError):
        it.pop()
