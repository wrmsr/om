import abc
import gc
import sys

from ...testing import pytest as ptu
from ..dispatch import Dispatcher


def test_simple():
    disp: Dispatcher[str] = Dispatcher()

    class A:
        pass

    disp.register('object', [object])
    for _ in range(2):
        assert disp.dispatch(object) == 'object'
        assert disp.dispatch(A) == 'object'

    disp.register('A', [A])
    for _ in range(2):
        assert disp.dispatch(object) == 'object'
        assert disp.dispatch(A) == 'A'


def test_strong_cache_impl_reference_ownership():
    class A:
        pass

    impl = object()
    initial_refcount = sys.getrefcount(impl)

    disp: Dispatcher[object] = Dispatcher(strong_cache=True)
    disp.register(impl, [A])
    assert sys.getrefcount(impl) == initial_refcount + 1

    returned = disp.dispatch(A)
    assert returned is impl
    assert sys.getrefcount(impl) == initial_refcount + 3


def test_uncached_miss():
    for strong_cache in [False, True]:
        for uncached_miss in [False, True]:
            calls = 0

            def find_impl(cls, impls):
                nonlocal calls

                calls += 1

            disp: Dispatcher[str] = Dispatcher(
                find_impl,
                strong_cache=strong_cache,
                uncached_miss=uncached_miss,
            )

            class A:
                pass

            assert disp.dispatch(A) is None
            assert disp.dispatch(A) is None
            assert calls == (2 if uncached_miss else 1)
            assert disp.cache_size() == (0 if uncached_miss else 1)


@ptu.skip.if_nogil()
def test_weaks():
    disp: Dispatcher[str] = Dispatcher()

    class A:
        pass

    disp.register('object', [object])
    disp.register('A', [A])

    for _ in range(2):
        assert disp.dispatch(object) == 'object'
        assert disp.dispatch(A) == 'A'

    def inner():
        class B(A):
            pass

        for _ in range(2):
            assert disp.dispatch(B) == 'A'

    for _ in range(2):
        assert disp.cache_size() == 2
        inner()
        assert disp.cache_size() == 3
        gc.collect()
        assert disp.cache_size() == 2

    for _ in range(10):
        inner()
    gc.collect()


def test_abc():
    disp: Dispatcher[str] = Dispatcher()

    class A(abc.ABC):  # noqa
        pass

    class B:
        pass

    disp.register('object', [object])
    assert disp.dispatch(A) == 'object'
    assert disp.dispatch(B) == 'object'

    disp.register('A', [A])
    assert disp.dispatch(A) == 'A'
    assert disp.dispatch(B) == 'object'

    A.register(B)  # noqa
    assert disp.dispatch(A) == 'A'
    assert disp.dispatch(B) == 'A'


def test_abc_weaks():
    disp: Dispatcher[str] = Dispatcher()

    class A(abc.ABC):  # noqa
        pass

    disp.register('object', [object])
    disp.register('A', [A])

    def inner():
        class B:
            pass

        for _ in range(2):
            assert disp.dispatch(B) == 'object'
            assert disp.dispatch(C) == 'A'

        A.register(B)  # noqa

        for _ in range(2):
            assert disp.dispatch(B) == 'A'
            assert disp.dispatch(C) == 'A'

    class C:
        pass

    A.register(C)  # noqa

    for _ in range(10):
        inner()

    gc.collect()
