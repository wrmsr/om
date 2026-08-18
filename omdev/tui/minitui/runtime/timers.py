# ruff: noqa: SLF001
"""One-shot and repeating timers on an injectable clock, for deterministic tests and spinner-grade scheduling."""
import heapq
import itertools
import time
import typing as ta


##


class Timer:
    """A handle for a scheduled callback. Cancel via `cancel()`; repeating timers reschedule until cancelled."""

    def __init__(
            self,
            fn: ta.Callable[[], None],
            *,
            fire_at: float,
            interval_s: float | None = None,
    ) -> None:
        super().__init__()

        self._fn = fn
        self._fire_at = fire_at
        self._interval_s = interval_s
        self._cancelled = False

    @property
    def fire_at(self) -> float:
        return self._fire_at

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True


class Timers:
    def __init__(
            self,
            clock: ta.Callable[[], float] = time.monotonic,
    ) -> None:
        super().__init__()

        self._clock = clock
        self._heap: list[tuple[float, int, Timer]] = []
        self._seq = itertools.count()

    @property
    def clock(self) -> ta.Callable[[], float]:
        return self._clock

    def _schedule(self, timer: Timer) -> None:
        heapq.heappush(self._heap, (timer.fire_at, next(self._seq), timer))

    def call_later(self, delay_s: float, fn: ta.Callable[[], None]) -> Timer:
        timer = Timer(fn, fire_at=self._clock() + delay_s)
        self._schedule(timer)
        return timer

    def call_every(self, interval_s: float, fn: ta.Callable[[], None]) -> Timer:
        timer = Timer(fn, fire_at=self._clock() + interval_s, interval_s=interval_s)
        self._schedule(timer)
        return timer

    def next_fire_at(self) -> float | None:
        while self._heap and self._heap[0][2].cancelled:
            heapq.heappop(self._heap)
        if not self._heap:
            return None
        return self._heap[0][0]

    def fire_due(self) -> int:
        """Fire all due timers (rescheduling repeating ones), returning how many fired."""

        now = self._clock()
        fired = 0
        while self._heap and self._heap[0][0] <= now:
            _, _, timer = heapq.heappop(self._heap)
            if timer.cancelled:
                continue
            fired += 1
            if timer._interval_s is not None:
                # Reschedule from 'now' rather than the nominal time - no catch-up bursts after a stall.
                timer._fire_at = now + timer._interval_s
                self._schedule(timer)
            timer._fn()
        return fired
