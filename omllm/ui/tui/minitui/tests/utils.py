"""
Test support for the minitui chat surface: a loop-free driver stand-in with a manual clock, a real agent over a scripted
model for driving `PromptPump`, and small helpers for reading frames and scrollback.
"""
import asyncio
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore.asyncs.asynclite import all as asl
from omdev import minitui as mt

from ..... import agent as agn
from ..... import llm
from .....core.asyncs.asyncio import AsyncioGroupRunner
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
        self.alt_screen = False

    def commit(self, lines) -> None:
        self.commits.append(tuple(lines))

    def set_alt_screen(self, enabled: bool) -> None:
        self.alt_screen = enabled

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


async def make_agent(backend: llm.Backend, *, tools: ta.Sequence[agn.Tool] = ()) -> agn.Agent:
    """A real agent on a real turn loop: the model is the only thing stood in for, by whatever backend is given."""

    agent = agn.Agent(
        turn_runner=agn.TurnLoopRunner(
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
            backends=agn.DictBackendManager({llm.ImmediateBackend: {None: backend}}),  # type: ignore[type-abstract]
        ),
    )

    if tools:
        await agent.update_state(lambda s: dc.replace(s, context=agn.Context(tools=agn.ToolSet(list(tools)))))

    return agent


def user_texts(agent: agn.Agent) -> list[str]:
    """The prompts which made it into the agent's transcript, in order."""

    return [
        check.isinstance(m.content, str)
        for m in agent.state.context.messages or ()
        if isinstance(m, llm.UserMessage)
    ]


class FirstInvocationGate:
    """
    A scripted stream backend's gate which parks the first invocation ahead of its first emission until it is
    cancelled, as a prompt waiting on a model which is not answering is. Every later invocation goes straight through.
    """

    def __init__(self) -> None:
        super().__init__()

        self.started = asyncio.Event()
        self.stopped = asyncio.Event()
        self._never = asyncio.Event()

    async def __call__(self, point: llm.BackendScriptGatePoint) -> None:
        if point.invocation_index or point.emission_index:
            return

        self.started.set()
        try:
            await self._never.wait()
        finally:
            self.stopped.set()


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


async def settle_idle(agent: agn.Agent, until: ta.Callable[[], bool] | None = None) -> None:
    """
    `settle`, for waiting out an agent's run rather than a callback or two: until the agent is between prompts and
    `until` holds. A run takes many more turns of the loop than `settle` allows by default; they are bounded all the
    same.
    """

    await settle(lambda: not agent.is_busy and (until is None or until()), max_steps=200)
