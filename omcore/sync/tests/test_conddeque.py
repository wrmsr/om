import threading

import pytest

from ..conddeque import ConditionDeque


def test_pop_timeout() -> None:
    deque = ConditionDeque[int]()

    with pytest.raises(TimeoutError):
        deque.pop(timeout=0)


def test_pop_after_if_empty_push() -> None:
    deque = ConditionDeque[int]()

    deque.push(1)
    assert deque.pop(timeout=0) == 1

    assert deque.pop(timeout=0, if_empty=lambda: deque.push(2)) == 2


def test_pop_waits_for_push() -> None:
    deque = ConditionDeque[int]()

    def push() -> None:
        deque.push(1)

    thread = threading.Thread(target=push)
    assert deque.pop(timeout=1, if_empty=thread.start) == 1
    thread.join(1)
    assert not thread.is_alive()
