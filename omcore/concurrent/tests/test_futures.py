import concurrent.futures
import time

import pytest

from ... import lang
from .. import futures as futs
from ..executors import ImmediateExecutor


def test_wait_futures():
    def fn() -> float:
        time.sleep(.2)
        return time.time()

    tp: concurrent.futures.Executor
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as tp:
        futures = [tp.submit(fn) for _ in range(10)]
        assert not futs.wait_futures(futures, tick_fn=iter([True, False]).__next__)
        assert futs.wait_futures(futures)

    def pairs(l):
        return [set(p) for p in lang.chunk(2, l)]

    idxs = [t[0] for t in sorted(enumerate(futures), key=lambda t: t[1].result())]
    assert pairs(idxs) == pairs(range(10))


def test_wait_futures_empty():
    ticked = False

    def tick():
        nonlocal ticked
        ticked = True
        return False

    assert futs.wait_futures([], tick_fn=tick)
    assert not ticked


def test_wait_futures_exception_cancels_pending():
    error = ValueError('bad')
    failed = concurrent.futures.Future[object]()
    failed.set_exception(error)
    pending = concurrent.futures.Future[object]()

    with pytest.raises(futs.FutureError) as exc_info:
        futs.wait_futures(
            [failed, pending],
            tick_interval_s=0,
            raise_exceptions=True,
            cancel_on_exception=True,
        )

    assert exc_info.value.future is failed
    assert exc_info.value.__cause__ is error
    assert pending.cancelled()


def test_wait_futures_cancelled():
    future = concurrent.futures.Future[object]()
    future.cancel()

    with pytest.raises(futs.FutureError) as exc_info:
        futs.wait_futures([future], raise_exceptions=True)

    assert exc_info.value.future is future
    assert isinstance(exc_info.value.__cause__, concurrent.futures.CancelledError)
    assert 'CancelledError' in repr(exc_info.value)


def test_future_error_repr_pending():
    future = concurrent.futures.Future[object]()

    assert 'exception=None' in repr(futs.FutureError(future))


def test_wait_futures_timeout():
    with pytest.raises(futs.FutureTimeoutError):
        futs.wait_futures(
            [concurrent.futures.Future()],
            timeout_s=0,
            tick_interval_s=0,
        )


def test_wait_all_futures_or_raise():
    success = concurrent.futures.Future[int]()
    success.set_result(1)
    futs.wait_all_futures_or_raise([success])

    first_error = ValueError('first')
    first_failure = concurrent.futures.Future[object]()
    first_failure.set_exception(first_error)
    with pytest.raises(ValueError, match='first') as exc_info:
        futs.wait_all_futures_or_raise([first_failure])
    assert exc_info.value is first_error

    second_error = TypeError('second')
    second_failure = concurrent.futures.Future[object]()
    second_failure.set_exception(second_error)
    with pytest.raises(ExceptionGroup) as group_exc_info:
        futs.wait_all_futures_or_raise([first_failure, second_failure])
    assert set(group_exc_info.value.exceptions) == {first_error, second_error}


def test_wait_dependent_futures():
    calls = []

    def first():
        calls.append('first')
        return 1

    def second():
        calls.append('second')
        return 2

    def third():
        calls.append('third')
        return 3

    futures_by_fn = futs.wait_dependent_futures(
        ImmediateExecutor(),
        {
            first: set(),
            second: {first},
            third: {second},
        },
        timeout_s=0,
        tick_interval_s=0,
    )

    assert calls == ['first', 'second', 'third']
    assert {fn: future.result() for fn, future in futures_by_fn.items()} == {
        first: 1,
        second: 2,
        third: 3,
    }


def test_wait_dependent_futures_error_target():
    error = ValueError('bad')

    def fail():
        raise error

    with pytest.raises(futs.FutureError) as exc_info:
        futs.wait_dependent_futures(
            ImmediateExecutor(),
            {fail: set()},
            tick_interval_s=0,
        )

    assert exc_info.value.target is fail
    assert exc_info.value.__cause__ is error


def test_wait_dependent_futures_rejects_incomplete_roots():
    class PendingExecutor(concurrent.futures.Executor):
        def submit(self, fn, /, *args, **kwargs):
            return concurrent.futures.Future()

    def fn():
        raise AssertionError

    with pytest.raises(Exception, match='Unfinished fns'):
        futs.wait_dependent_futures(
            PendingExecutor(),
            {fn: set()},
            tick_fn=lambda: False,
        )


def test_wait_dependent_futures_cancels_on_submit_error():
    class FailingExecutor(concurrent.futures.Executor):
        def __init__(self):
            super().__init__()

            self.future = concurrent.futures.Future[object]()
            self._submitted = False

        def submit(self, fn, /, *args, **kwargs):
            if self._submitted:
                raise RuntimeError('submit failed')
            self._submitted = True
            return self.future

    def first():
        raise AssertionError

    def second():
        raise AssertionError

    executor = FailingExecutor()
    with pytest.raises(RuntimeError, match='submit failed'):
        futs.wait_dependent_futures(
            executor,
            {
                first: set(),
                second: set(),
            },
        )

    assert executor.future.cancelled()
