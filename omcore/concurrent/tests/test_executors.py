import concurrent.futures as cf

import pytest

from ..executors import ImmediateExecutor
from ..executors import new_executor


def test_immediate_executor():
    executor = ImmediateExecutor()

    future = executor.submit(lambda value: value + 1, 2)
    assert future.done()
    assert future.result() == 3

    error = ValueError('bad')
    future = executor.submit(lambda: (_ for _ in ()).throw(error))
    assert future.exception() is error

    future = executor.submit(lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        future.result()

    executor.shutdown()
    with pytest.raises(RuntimeError, match='shutdown'):
        executor.submit(lambda: None)


def test_immediate_executor_immediate_exceptions():
    error = ValueError('bad')
    with pytest.raises(ValueError, match='bad') as exc_info:
        ImmediateExecutor(immediate_exceptions=True).submit(lambda: (_ for _ in ()).throw(error))
    assert exc_info.value is error


def test_new_immediate_executor():
    executor: cf.Executor
    with new_executor(0) as executor:
        assert isinstance(executor, ImmediateExecutor)
        assert executor.submit(lambda: 1).result() == 1

    with pytest.raises(RuntimeError, match='shutdown'):
        executor.submit(lambda: None)
