"""The job contract, as the asyncio runner keeps it: off the loop, bounded, interruptible, and never waited for."""
import asyncio
import contextvars
import threading
import time

import pytest

from ..asyncio import AsyncioJobRunner
from ..base import AsyncJob
from ..base import AsyncJobRunnerClosedError
from ..base import AsyncJobTimeoutError


##


class _Waiter(AsyncJob[str]):
    """Blocks until released or - if it heeds interruption - interrupted, recording what it saw."""

    def __init__(self, name: str, *, heeds_interrupt: bool = True) -> None:
        super().__init__()

        self.name = name
        self._heeds_interrupt = heeds_interrupt

        self.started = threading.Event()
        self.release = threading.Event()
        self.interrupted = threading.Event()
        self.finished = threading.Event()
        self.thread: int | None = None

    def run(self) -> str:
        self.thread = threading.get_ident()
        self.started.set()
        try:
            while not self.release.wait(.01):
                if self._heeds_interrupt and self.interrupted.is_set():
                    raise InterruptedError(self.name)
            return self.name
        finally:
            self.finished.set()

    def interrupt(self) -> None:
        self.interrupted.set()


async def _poll(fn, timeout=5., interval=.005):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if fn():
            return True
        await asyncio.sleep(interval)
    return fn()


async def _started(w: _Waiter) -> None:
    assert await _poll(w.started.is_set)


async def _drained(runner: AsyncioJobRunner) -> None:
    assert await _poll(lambda: not runner.num_running)


##


@pytest.mark.asyncs('asyncio')
async def test_job_runs_off_the_loop_and_returns_its_result():
    async with AsyncioJobRunner() as runner:
        w = _Waiter('a')
        w.release.set()

        assert await runner.run(w) == 'a'
        assert w.thread is not None and w.thread != threading.get_ident()
        assert runner.num_running == 0


@pytest.mark.asyncs('asyncio')
async def test_job_exception_propagates():
    class Boom(AsyncJob[None]):
        def run(self) -> None:
            raise ValueError('boom')

    async with AsyncioJobRunner() as runner:
        with pytest.raises(ValueError, match='boom'):
            await runner.run(Boom())


@pytest.mark.asyncs('asyncio')
async def test_timeout_interrupts_the_job():
    async with AsyncioJobRunner() as runner:
        w = _Waiter('slow')

        with pytest.raises(AsyncJobTimeoutError):
            await runner.run(w, timeout=.05)

        # The thread was told, stopped on its own, and is no longer counted.
        assert w.interrupted.is_set()
        assert w.finished.wait(2.)
        await _drained(runner)


@pytest.mark.asyncs('asyncio')
async def test_cancellation_interrupts_the_job():
    async with AsyncioJobRunner() as runner:
        w = _Waiter('slow')
        task = asyncio.create_task(runner.run(w))
        await _started(w)

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert w.interrupted.is_set()
        assert w.finished.wait(2.)
        await _drained(runner)


@pytest.mark.asyncs('asyncio')
async def test_a_job_which_cannot_be_interrupted_runs_on_and_close_waits_within_bounds():
    runner = AsyncioJobRunner(close_timeout_s=.05)
    w = _Waiter('stubborn', heeds_interrupt=False)

    with pytest.raises(AsyncJobTimeoutError):
        await runner.run(w, timeout=.02)

    # Still going: the caller has moved on, the runner has not forgotten it.
    assert w.interrupted.is_set()
    assert not w.finished.is_set()
    assert runner.num_running == 1

    # Close gives it the bounded moment and then gives up on it; the thread itself is a daemon.
    await runner.aclose()
    assert runner.closed
    assert not w.finished.is_set()

    w.release.set()
    assert w.finished.wait(2.)


@pytest.mark.asyncs('asyncio')
async def test_max_workers_bounds_running_threads_not_waiting_callers():
    async with AsyncioJobRunner(max_workers=1) as runner:
        a, b = _Waiter('a'), _Waiter('b')
        ta_ = asyncio.create_task(runner.run(a))
        await _started(a)
        tb = asyncio.create_task(runner.run(b))
        await asyncio.sleep(.02)

        # b is queued behind a, on the loop - not on a thread.
        assert not b.started.is_set()
        assert runner.num_running == 1

        a.release.set()
        assert await ta_ == 'a'
        await _started(b)
        b.release.set()
        assert await tb == 'b'


@pytest.mark.asyncs('asyncio')
async def test_a_queued_job_cancels_without_a_thread():
    async with AsyncioJobRunner(max_workers=1) as runner:
        a, b = _Waiter('a'), _Waiter('b')
        ta_ = asyncio.create_task(runner.run(a))
        await _started(a)
        tb = asyncio.create_task(runner.run(b))
        await asyncio.sleep(.02)

        tb.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tb
        assert not b.started.is_set()

        a.release.set()
        assert await ta_ == 'a'


@pytest.mark.asyncs('asyncio')
async def test_closed_runner_refuses_jobs():
    runner = AsyncioJobRunner()
    await runner.aclose()
    await runner.aclose()

    with pytest.raises(AsyncJobRunnerClosedError):
        await runner.run(_Waiter('late'))


@pytest.mark.asyncs('asyncio')
async def test_context_variables_reach_the_job():
    var: contextvars.ContextVar[str] = contextvars.ContextVar('var')

    class Read(AsyncJob[str]):
        def run(self) -> str:
            return var.get()

    async with AsyncioJobRunner() as runner:
        var.set('carried')
        assert await runner.run(Read()) == 'carried'
