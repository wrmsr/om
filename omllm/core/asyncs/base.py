"""
The concurrency the harness needs beyond what asynclite offers - which stops short of tasks on purpose. This is not a
general abstraction over a backend's tasks: it is the one shape of concurrent work the agent loop does, with the
cancellation semantics that work needs spelled out, so the loop itself can stay sans-io.
"""
import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


T = ta.TypeVar('T')


##


@dc.dataclass()
class AsyncGroupCancelledError(BaseException):
    """
    The calling task was cancelled while its group ran. By the time this is raised every member of the group has
    finished: those the cancellation reached in time were cancelled and are absent from `outcomes`, and the rest had
    completed and are present, in the order they were given. A backend raises this as a subclass of its own
    cancellation error, so that it propagates through the backend's tasks as the cancellation it is.
    """

    outcomes: ta.Sequence[lang.Maybe[ta.Any]]


@dc.dataclass()
class AsyncGroupMemberCancelledError(Exception):
    """
    A member of the group ended cancelled although the group did not cancel it: something it awaited was cancelled
    out from under it. That is a failure of the member, not a cancellation of the group, and is reported like any
    other.
    """

    index: int


##


class AsyncGroupRunner(lang.Abstract):
    """
    Runs a batch of awaitables as one unit. Every one of them is started, and none is left running when `run` returns
    or raises, however it does so:

     - All complete: their results, in the order given.
     - One raises: the rest are cancelled and waited for, then an ExceptionGroup of what was raised - a
       BaseExceptionGroup if any of it is not an Exception.
     - The calling task is cancelled: all of them are cancelled and waited for, then AsyncGroupCancelledError, carrying
       what had completed by then.
     - One ends cancelled without the group having cancelled it: that is its failure, reported as above with an
       AsyncGroupMemberCancelledError standing in for it.

    Members run concurrently where the backend can, but need not: only the above is promised.
    """

    @abc.abstractmethod
    def run(self, fns: ta.Sequence[ta.Callable[[], ta.Awaitable[T]]]) -> ta.Awaitable[ta.Sequence[T]]:
        raise NotImplementedError
