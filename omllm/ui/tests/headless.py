"""
Test support: the ui's injector with no ui on it. `bind_ui` is used as it is; the little a frontend adds to it is
stood in for; and what a test has to steer - what the llm says, where the sessions are kept - is overridden.
"""
import contextlib
import typing as ta

from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import lang

from ... import agent as agn
from ...agent.tests.scripted import scripted_backend
from ...core import ui
from ..agent.inject.events import AgentEventSubscribers
from ..agent.setup import AgentSetup
from ..commands.manager import CommandsManager
from ..config import UiConfig
from ..inject.inject import AgentInjector
from ..inject.inject import AgentUiInjector
from ..inject.inject import UiBinder


##


class DenyingPermissionAsker(agn.PermissionAsker):
    async def ask(
            self,
            request: agn.PermissionRequest,
            rule: agn.PermissionRule,
    ) -> agn.DecidedPermissionState:
        return agn.PermissionState.DENY


def bind_headless_ui(
        config: UiConfig,
        *,
        ui_rewriter: inj.ElementsRewriter | None = None,
        agent_rewriter: inj.ElementsRewriter | None = None,
        agent_ui_rewriter: inj.ElementsRewriter | None = None,
) -> inj.Elements:
    return inj.as_elements(
        UiBinder(
            config,
            ui_rewriter=lambda els: (ui_rewriter or lang.identity)(inj.as_elements(
                els,

                inj.bind(ui.NopTextDisplayer()),
                inj.bind(ui.TextDisplayer, to_key=ui.NopTextDisplayer),

                inj.bind(ui.RaiseQuitSignal(SystemExit)),
                inj.bind(ui.QuitSignal, to_key=ui.RaiseQuitSignal),

                inj.bind(DenyingPermissionAsker()),
                inj.bind(agn.PermissionAsker, to_key=DenyingPermissionAsker),
            )),
            agent_rewriter=agent_rewriter,
            agent_ui_rewriter=agent_ui_rewriter,
        ).bind_ui(),
    )


def bind_scripted_backend(*turns: ta.Any) -> inj.Elemental:
    """An override: the backends the config asked for, replaced by a scripted one saying what it is given to say."""

    return inj.bind(
        agn.BackendManager,
        to_const=agn.DictBackendManager.of(scripted_backend(*turns)),
    )


##


@dc.dataclass(frozen=True, kw_only=True)
class HeadlessUi:
    ui_injector: inj.AsyncInjector
    agent_injector: inj.AsyncInjector
    agent_ui_injector: inj.AsyncInjector

    agent: agn.Agent
    session: agn.Session
    commands: CommandsManager


@contextlib.asynccontextmanager
async def headless_ui(*els: inj.Elemental) -> ta.AsyncIterator[HeadlessUi]:
    async with inj.create_asyncio_managed_injector(
        *els,
    ) as ui_injector:
        agent_injector = (await ui_injector[AgentInjector]).v
        agent_ui_injector = (await agent_injector[AgentUiInjector]).v

        # What a frontend's main does with its injector, short of running anything on a terminal.
        agent = await ui_injector[agn.Agent]
        session = await ui_injector[agn.Session]
        commands = await ui_injector[CommandsManager]

        setup = await ui_injector[AgentSetup]
        setup.pre_setup()
        for el in await ui_injector[AgentEventSubscribers]:
            agent.subscribe(el)
        await setup.run()

        config = await ui_injector[UiConfig]
        if config.resume is not None:
            await session.resume()

        async def prompt(input: str) -> None:  # noqa
            if not input:
                return

            if input[0] == '/':
                await commands.parse(input[1:]).run()
                return

            await agent.prompt(input)

        for ax in [
            *(config.autoexec or []),
        ]:
            await prompt(ax)

        yield HeadlessUi(
            ui_injector=ui_injector,
            agent_injector=agent_injector,
            agent_ui_injector=agent_ui_injector,

            agent=agent,
            session=session,
            commands=commands,
        )
