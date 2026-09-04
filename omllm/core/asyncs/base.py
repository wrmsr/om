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
    completed and are present, in the order they were given. A backend raises this as a subclass of its own cancellation
    error, so that it propagates through the backend's tasks as the cancellation it is.
    """

    outcomes: ta.Sequence[lang.Maybe[ta.Any]]


class AsyncGroupFailedError(ExceptionGroup):
    """
    One or more members of the group raised. By the time this is raised every member has finished: the ones which
    raised are its exceptions, the rest were cancelled or had completed - and those which completed are present in
    `outcomes`, in the order the members were given.
    """

    outcomes: ta.Sequence[lang.Maybe[ta.Any]]

    def __new__(
            cls,
            errors: ta.Sequence[Exception],
            outcomes: ta.Sequence[lang.Maybe[ta.Any]],
    ) -> ta.Self:
        self = super().__new__(cls, 'Failed members of an async group', list(errors))
        self.outcomes = tuple(outcomes)
        return self

    def __init__(
            self,
            errors: ta.Sequence[Exception],
            outcomes: ta.Sequence[lang.Maybe[ta.Any]],
    ) -> None:
        super().__init__('Failed members of an async group', list(errors))

    def derive(self, excs: ta.Sequence[Exception]) -> AsyncGroupFailedError:  # type: ignore[override]
        return AsyncGroupFailedError(excs, self.outcomes)


@dc.dataclass()
class AsyncGroupMemberCancelledError(Exception):
    """
    A member of the group ended cancelled although the group did not cancel it: something it awaited was cancelled out
    from under it. That is a failure of the member, not a cancellation of the group, and is reported like any other.
    """

    index: int


##


class AsyncGroupRunner(lang.Abstract):
    """
    Runs a batch of awaitables as one unit. Every one of them is started, and none is left running when `run` returns or
    raises, however it does so:

     - All complete: their results, in the order given.
     - One raises: the rest are cancelled and waited for, then AsyncGroupFailedError - an ExceptionGroup of what was
       raised, carrying what had completed by then. Should any of what was raised not be an Exception, a plain
       BaseExceptionGroup instead.
     - The calling task is cancelled: all of them are cancelled and waited for, then AsyncGroupCancelledError, carrying
       what had completed by then.
     - One ends cancelled without the group having cancelled it: that is its failure, reported as above with an
       AsyncGroupMemberCancelledError standing in for it.

    Members run concurrently where the backend can, but need not: only the above is promised.
    """

    @abc.abstractmethod
    def run(self, fns: ta.Sequence[ta.Callable[[], ta.Awaitable[T]]]) -> ta.Awaitable[ta.Sequence[T]]:
        raise NotImplementedError


##


class AsyncJob(lang.Abstract, ta.Generic[T]):
    """
    A unit of blocking work - CPU-bound, or IO with no async form - for an AsyncJobRunner to run off the event loop.
    `run` does the work, on whatever thread the runner gives it; `interrupt` asks a running `run` to stop, from another
    thread. It is best effort: a job which cannot be stopped leaves it as the no-op it is by default, and simply runs to
    its end.
    """

    @abc.abstractmethod
    def run(self) -> T:
        raise NotImplementedError

    def interrupt(self) -> None:
        """Thread-safe, and safe to call more than once or after `run` has returned."""


class AsyncJobError(Exception):
    pass


class AsyncJobTimeoutError(AsyncJobError, TimeoutError):
    """The job was interrupted for running past its timeout."""


class AsyncJobRunnerClosedError(AsyncJobError):
    pass


class AsyncJobRunner(lang.Abstract):
    """
    Runs jobs off the event loop, and gives up on them without waiting:

     - The job completes: its result, or its exception.
     - Its timeout is up first: the job is interrupted, and AsyncJobTimeoutError raised.
     - The calling task is cancelled first: the job is interrupted, and the cancellation propagates.

    In the latter two the job's thread may well still be running - it stops when it notices the interruption, or, if it
    cannot be interrupted, when it is done. From then on it is the runner's: it is tracked, and joined - for as long as
    the runner is willing to wait - when the runner closes. Nothing here knows which async runtime it runs under.
    """

    @abc.abstractmethod
    def run(self, job: AsyncJob[T], *, timeout: float | None = None) -> ta.Awaitable[T]:
        raise NotImplementedError

    @abc.abstractmethod
    def aclose(self) -> ta.Awaitable[None]:
        """Interrupts whatever is still running and waits for it, within bounds. Idempotent."""

        raise NotImplementedError

    async def __aenter__(self) -> ta.Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
