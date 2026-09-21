"""
Test support: the tui's injector with no tui on it. `bind_tui` is used as it is; the little a frontend adds to it is
stood in for; and what a test has to steer - what the llm says, where the sessions are kept - is overridden.
"""
import contextlib
import typing as ta

from omcore import dataclasses as dc
from omcore import inject as inj

from .... import agent as agn
from .... import harness as har
from .... import llm
from ....agent.tests.scripted import scripted_backend
from ....core import ui
from ..config import Config
from ..inject import AgentEventSubscribers
from ..inject import bind_tui


##


class DenyingPermissionAsker(agn.PermissionAsker):
    async def ask(
            self,
            requestor: agn.PermissionRequestor,
            target: agn.PermissionTarget,
            rule: agn.PermissionRule,
    ) -> agn.DecidedPermissionState:
        return agn.PermissionState.DENY


def bind_headless_tui(config: Config) -> inj.Elements:
    return inj.as_elements(
        inj.bind(config),

        bind_tui(config),

        inj.bind(ui.NopTextDisplayer()),
        inj.bind(ui.TextDisplayer, to_key=ui.NopTextDisplayer),

        inj.bind(ui.RaiseQuitSignal(SystemExit)),
        inj.bind(ui.QuitSignal, to_key=ui.RaiseQuitSignal),

        inj.bind(DenyingPermissionAsker()),
        inj.bind(agn.PermissionAsker, to_key=DenyingPermissionAsker),
    )


def bind_scripted_backend(*turns: ta.Any) -> inj.Elemental:
    """An override: the backends the config asked for, replaced by a scripted one saying what it is given to say."""

    return inj.bind(
        agn.BackendManager,
        to_const=agn.DictBackendManager({
            llm.ImmediateBackend: {None: scripted_backend(*turns)},  # type: ignore[type-abstract]
        }),
    )


##


@dc.dataclass(frozen=True, kw_only=True)
class HeadlessTui:
    injector: inj.AsyncInjector

    agent: agn.Agent
    session: har.Session


@contextlib.asynccontextmanager
async def headless_tui(*els: inj.Elemental) -> ta.AsyncIterator[HeadlessTui]:
    async with inj.create_async_managed_injector(
        *els,
        factory=inj.create_asyncio_injector,
    ) as injector:
        # What a frontend's main does with its injector, short of running anything on a terminal.
        agent = await injector[agn.Agent]
        tool_set = await injector[agn.ToolSet]
        session = await injector[har.Session]

        for el in await injector[AgentEventSubscribers]:
            agent.subscribe(el)

        await agent.update_state(
            lambda state: dc.replace(
                state,
                context=dc.replace(
                    state.context,
                    tools=tool_set,
                ),
            ),
        )

        config = await injector[Config]
        if config.resume is not None:
            await session.resume()

        yield HeadlessTui(
            injector=injector,
            agent=agent,
            session=session,
        )
