"""
The asyncio implementations: the group runner is a TaskGroup with the group's contract mapped onto its behavior, and
the job runner hands each job its own thread, with the loop told of the outcome from there.
"""
import asyncio
import contextvars
import threading
import typing as ta

from omcore import check
from omcore import lang
from omcore.logs import all as logs

from .base import AsyncGroupCancelledError
from .base import AsyncGroupFailedError
from .base import AsyncGroupMemberCancelledError
from .base import AsyncGroupRunner
from .base import AsyncJob
from .base import AsyncJobRunner
from .base import AsyncJobRunnerClosedError
from .base import AsyncJobTimeoutError


T = ta.TypeVar('T')


log = logs.get_module_logger(globals())


##


class AsyncioGroupCancelledError(AsyncGroupCancelledError, asyncio.CancelledError):
    """An asyncio.CancelledError too, so the task it unwinds through ends cancelled."""


class AsyncioGroupRunner(AsyncGroupRunner):
    async def run(self, fns: ta.Sequence[ta.Callable[[], ta.Awaitable[T]]]) -> list[T]:
        outcomes: list[lang.Maybe[T]] = [lang.nothing() for _ in fns]

        async def member(i: int, fn: ta.Callable[[], ta.Awaitable[T]]) -> None:
            outcomes[i] = lang.just(await fn())

        tasks: list[asyncio.Task] = []

        try:
            async with asyncio.TaskGroup() as tg:
                for i, fn in enumerate(fns):
                    tasks.append(tg.create_task(member(i, fn)))

        except asyncio.CancelledError as e:
            # The group re-raises the calling task's cancellation only once every member is done - and only when none of
            # them raised: a member's error takes precedence and comes out as a group, with the task re-cancelled to
            # keep its count.
            raise AsyncioGroupCancelledError(outcomes) from e

        except ExceptionGroup as eg:
            # Every member is done here too. The group's own is rewrapped to carry the outcomes; a BaseExceptionGroup
            # which is not an ExceptionGroup holds something no ExceptionGroup can, and passes as it is.
            raise AsyncGroupFailedError(eg.exceptions, outcomes) from eg

        # A member which ended cancelled is passed over by the group, so is found here. The group only cancels members
        # while aborting, after which it raises - so on this path any cancelled member was cancelled from under it.
        if strays := [i for i, t in enumerate(tasks) if t.cancelled()]:
            raise AsyncGroupFailedError(
                [AsyncGroupMemberCancelledError(i) for i in strays],
                outcomes,
            )

        return [o.must() for o in outcomes]


##


DEFAULT_JOB_RUNNER_CLOSE_TIMEOUT_S: ta.Final[float] = 10.


class _RunningJob:
    """A job on its thread: the future its caller awaits, and the one its runner waits on at close."""

    def __init__(self, job: AsyncJob, loop: asyncio.AbstractEventLoop) -> None:
        super().__init__()

        self.job = job

        # Cancelled along with the caller's wait; the thread's outcome then has nowhere to go and is dropped.
        self.result: asyncio.Future = loop.create_future()

        # Set once the thread is done, whatever became of the result - what the runner waits on at close.
        self.finished: asyncio.Future = loop.create_future()


class AsyncioJobRunner(AsyncJobRunner):
    """
    Each job gets a thread of its own - a daemon, so a job which never stops does not hold up the interpreter's exit
    either - and `max_workers` bounds how many run at once: a job past the bound waits its turn on the loop, where its
    wait is as cancellable as any. Threads are counted until they are done, not until their callers stop waiting.
    """

    def __init__(
            self,
            *,
            max_workers: int | None = None,
            close_timeout_s: float | None = DEFAULT_JOB_RUNNER_CLOSE_TIMEOUT_S,
    ) -> None:
        super().__init__()

        check.arg(max_workers is None or max_workers > 0)
        self._max_workers = max_workers
        self._close_timeout_s = close_timeout_s

        self._slots = asyncio.Semaphore(max_workers) if max_workers is not None else None
        self._running: set[_RunningJob] = set()
        self._closed = False

    @property
    def num_running(self) -> int:
        """How many job threads are running - their callers waiting or not."""

        return len(self._running)

    @property
    def closed(self) -> bool:
        return self._closed

    def _check_open(self) -> None:
        if self._closed:
            raise AsyncJobRunnerClosedError

    #

    def _work(self, running: _RunningJob, ctx: contextvars.Context, loop: asyncio.AbstractEventLoop) -> None:
        try:
            result = ctx.run(running.job.run)
        except BaseException as e:  # noqa
            outcome: tuple[ta.Any, BaseException | None] = (None, e)
        else:
            outcome = (result, None)

        try:
            loop.call_soon_threadsafe(self._deliver, running, outcome)
        except RuntimeError:
            # The loop is closed: there is nobody to tell.
            self._running.discard(running)

    def _deliver(self, running: _RunningJob, outcome: tuple[ta.Any, BaseException | None]) -> None:
        # On the loop thread: the runner's bookkeeping is only ever touched here and in `run` / `aclose`.
        self._running.discard(running)
        if (slots := self._slots) is not None:
            slots.release()

        result, error = outcome
        if not running.result.done():
            if error is not None:
                running.result.set_exception(error)
            else:
                running.result.set_result(result)
        running.finished.set_result(None)

    async def run(self, job: AsyncJob[T], *, timeout: float | None = None) -> T:
        self._check_open()

        loop = asyncio.get_running_loop()

        if (slots := self._slots) is not None:
            await slots.acquire()
            try:
                self._check_open()
            except AsyncJobRunnerClosedError:
                slots.release()
                raise

        running = _RunningJob(job, loop)
        self._running.add(running)
        threading.Thread(
            target=self._work,
            args=(running, contextvars.copy_context(), loop),
            name=f'om-job-{id(job):x}',
            daemon=True,
        ).start()

        try:
            if timeout is None:
                return await running.result

            try:
                return await asyncio.wait_for(running.result, timeout)
            except TimeoutError:
                job.interrupt()
                raise AsyncJobTimeoutError(f'Job {job!r} ran past its timeout of {timeout}s') from None

        except asyncio.CancelledError:
            job.interrupt()
            raise

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True

        if not (running := list(self._running)):
            return

        for r in running:
            r.job.interrupt()

        _, pending = await asyncio.wait([r.finished for r in running], timeout=self._close_timeout_s)
        if pending:
            log.warning('%d job thread(s) still running at close', len(pending))
