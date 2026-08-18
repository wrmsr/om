# ruff: noqa: UP006 UP007 UP045
import typing as ta

from omcore.io.fdio.handlers import FdioHandler

from ..core.effects import SystevisorScheduleDeadlineEffect
from ..core.inputs import SystevisorDeadlineReachedFact
from .clocks import SystevisorClock


class SystevisorDeadlineFdioHandler(FdioHandler):
    def __init__(
            self,
            clock: SystevisorClock,
            callback: ta.Callable[[SystevisorDeadlineReachedFact], None],
    ) -> None:
        self._clock = clock
        self._callback = callback
        self._deadlines: ta.Dict[int, SystevisorScheduleDeadlineEffect] = {}
        self._closed = False

    def fd(self) -> int:
        return -1

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True
        self._deadlines.clear()

    def schedule(self, effect: SystevisorScheduleDeadlineEffect) -> None:
        if self._closed:
            raise RuntimeError('deadline handler is closed')
        self._deadlines[effect.deadline_id] = effect

    def next_deadline(self) -> ta.Optional[float]:
        if not self._deadlines:
            return None
        return min(effect.deadline_at for effect in self._deadlines.values())

    def on_timeout(self) -> None:
        now = self._clock.monotonic()
        due = sorted(
            (effect for effect in self._deadlines.values() if effect.deadline_at <= now),
            key=lambda effect: (effect.deadline_at, effect.deadline_id),
        )
        for effect in due:
            self._deadlines.pop(effect.deadline_id, None)
            self._callback(SystevisorDeadlineReachedFact(effect.deadline_id))


class SystevisorProcessExecFdioHandler(FdioHandler):
    def __init__(self, fd: int, callback: ta.Callable[[], bool]) -> None:
        self._fd = fd
        self._callback = callback
        self._closed = False

    def fd(self) -> int:
        return self._fd

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True

    def readable(self) -> bool:
        return not self._closed

    def on_readable(self) -> None:
        if self._callback():
            self._closed = True

    def on_error(self, exc: ta.Optional[BaseException] = None) -> None:
        self._closed = True


class SystevisorProcessPidfdFdioHandler(FdioHandler):
    def __init__(self, fd: int, callback: ta.Callable[[], None]) -> None:
        self._fd = fd
        self._callback = callback
        self._closed = False

    def fd(self) -> int:
        return self._fd

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True

    def readable(self) -> bool:
        return not self._closed

    def on_readable(self) -> None:
        self._closed = True
        self._callback()

    def on_error(self, exc: ta.Optional[BaseException] = None) -> None:
        self._closed = True
        self._callback()


class SystevisorProcessWaitFdioHandler(FdioHandler):
    def __init__(
            self,
            clock: SystevisorClock,
            callback: ta.Callable[[], None],
            active: ta.Callable[[], bool],
            interval_secs: float = .25,
    ) -> None:
        if interval_secs <= 0:
            raise ValueError(interval_secs)
        self._clock = clock
        self._callback = callback
        self._active = active
        self._interval_secs = interval_secs
        self._next_poll_at: ta.Optional[float] = None
        self._closed = False

    def fd(self) -> int:
        return -1

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True
        self._next_poll_at = None

    def poke(self) -> None:
        if not self._closed:
            self._next_poll_at = self._clock.monotonic()

    def next_deadline(self) -> ta.Optional[float]:
        return self._next_poll_at if self._active() else None

    def on_timeout(self) -> None:
        self._callback()
        self._next_poll_at = self._clock.monotonic() + self._interval_secs if self._active() else None
