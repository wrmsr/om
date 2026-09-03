"""
Test support for the minitui chat surface: a loop-free driver stand-in with a manual clock, simple `har.Session`
stand-ins for driving `PromptPump`, and small helpers for reading frames and scrollback.
"""
import asyncio
import typing as ta

from omdev.tui import minitui as mt

from ..app import APP_KEY_MAP
from ..app import AppKey
from ..app import MinituiChatApp


##


class Clock:
    def __init__(self) -> None:
        super().__init__()

        self.now = 0.

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class Surface:
    def __init__(self, width: int = 80) -> None:
        super().__init__()

        self.width = width


class Driver:
    """Records commits and invalidations; timers fire on a manual clock via `fire_after`."""

    def __init__(self) -> None:
        super().__init__()

        self.clock = Clock()
        self.surface = Surface()
        self.timers = mt.Timers(self.clock)
        self.commits: list[tuple[mt.Line, ...]] = []
        self.invalidations = 0
        self.stopped = False
        self.suspends = 0

    def commit(self, lines) -> None:
        self.commits.append(tuple(lines))

    def invalidate(self) -> None:
        self.invalidations += 1

    def stop(self) -> None:
        self.stopped = True

    def suspend(self) -> None:
        self.suspends += 1

    def fire_after(self, seconds: float) -> int:
        self.clock.advance(seconds)
        return self.timers.fire_due()


##


class BlockingSession:
    """The first prompt parks until cancelled; every later prompt completes immediately."""

    def __init__(self) -> None:
        super().__init__()

        self.prompts: list[str] = []
        self.first_started = asyncio.Event()
        self.first_stopped = asyncio.Event()
        self.second_done = asyncio.Event()
        self._never = asyncio.Event()

    async def prompt(self, text: str) -> None:
        self.prompts.append(text)
        if len(self.prompts) == 1:
            self.first_started.set()
            try:
                await self._never.wait()
            finally:
                self.first_stopped.set()
        else:
            self.second_done.set()


class RecordingSession:
    """Every prompt completes immediately."""

    def __init__(self) -> None:
        super().__init__()

        self.prompts: list[str] = []
        self.prompted = asyncio.Event()

    async def prompt(self, text: str) -> None:
        self.prompts.append(text)
        self.prompted.set()


class FailingSession:
    """The first prompt raises `error`; every later prompt completes immediately."""

    def __init__(self, error: Exception) -> None:
        super().__init__()

        self._error = error
        self.prompts: list[str] = []
        self.second_done = asyncio.Event()

    async def prompt(self, text: str) -> None:
        self.prompts.append(text)
        if len(self.prompts) == 1:
            raise self._error
        self.second_done.set()


##


def make_app() -> tuple[MinituiChatApp, Driver]:
    driver = Driver()
    return MinituiChatApp(ta.cast(mt.AsyncioDriver, driver)), driver


def frame_lines(app: MinituiChatApp) -> list[str]:
    return [line.text for line in app.render(80, 24).lines]


def commit_texts(driver: Driver) -> list[str]:
    return ['\n'.join(line.text for line in commit) for commit in driver.commits]


def app_key(ak: AppKey) -> mt.Key:
    """The first bound key for an app action."""

    keys = APP_KEY_MAP[ak]
    if isinstance(keys, mt.Key):
        return keys
    return keys[0]


async def settle(until: ta.Callable[[], bool] | None = None, *, max_steps: int = 20) -> None:
    """
    Yield to the loop a bounded number of times so already-scheduled callbacks and task steps run - stopping early
    once `until` holds. Bounded rather than awaiting a condition so a regression fails instead of hanging.
    """

    for _ in range(max_steps):
        if until is not None and until():
            return
        await asyncio.sleep(0)
