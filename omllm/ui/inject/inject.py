"""
TODO:
 - AgentUi child injector
"""
import contextlib
import typing as ta
import uuid

from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import lang

from ... import agent as agn
from ...core import ui
from ..agent.inject.events import agent_event_subscribers
from ..agent.inject.inject import bind_agent
from ..agent.setup import AgentSetup
from ..backends.inject import bind_backends
from ..commands.inject import bind_commands
from ..commands.manager import CommandsManager
from ..config import UiConfig
from ..types import UiId


##


class InjectorBox(dc.Box[inj.AsyncInjector], abstract=True):
    pass


def _bind_injector_import(box_cls: type[InjectorBox], key: ta.Any) -> inj.Elemental:
    return inj.bind(key, to_async_fn=inj.target(i=box_cls)(lambda i: i.v[key]))


##


class UiInjector(InjectorBox, final=True):
    pass


class AgentInjector(InjectorBox, final=True):
    pass


class AgentUiInjector(InjectorBox, final=True):
    pass


##


class UiBinder:
    def __init__(
            self,
            config: UiConfig,
            *,
            ui_rewriter: inj.ElementsRewriter | None = None,
            agent_rewriter: inj.ElementsRewriter | None = None,
            agent_ui_rewriter: inj.ElementsRewriter | None = None,
    ) -> None:
        super().__init__()

        self._config = config

        self._ui_rewriter = ui_rewriter or lang.identity
        self._agent_rewriter = agent_rewriter or lang.identity
        self._agent_ui_rewriter = agent_ui_rewriter or lang.identity

    #

    def bind_agent_ui(self) -> inj.Elements:
        return self._agent_ui_rewriter(inj.as_elements(
            bind_commands(self._config),

            #

            _bind_injector_import(UiInjector, ui.QuitSignal),
            _bind_injector_import(UiInjector, ui.TextDisplayer),
        ))

    async def _provide_agent_ui_injector(
            self,
            *,
            agent_injector: inj.AsyncInjector,
    ) -> AgentUiInjector:
        agent_ui_injector = await inj.create_asyncio_injector(
            self.bind_agent_ui(),

            #

            parent=agent_injector,
        )

        return AgentUiInjector(agent_ui_injector)

    #

    def bind_agent(self) -> inj.Elements:
        return self._agent_rewriter(inj.as_elements(
            inj.bind(UiConfig, to_const=self._config),

            bind_agent(self._config),
            bind_backends(self._config),

            #

            _bind_injector_import(UiInjector, agn.PermissionAsker),
        ))

    async def _provide_agent_injector(
            self,
            *,
            ui_injector: inj.AsyncInjector,
            aes: contextlib.AsyncExitStack,
    ) -> AgentInjector:
        agent_injector = await aes.enter_async_context(inj.create_asyncio_managed_injector(
            self.bind_agent(),

            inj.bind(UiInjector(ui_injector)),

            inj.bind(AgentUiInjector, to_async_fn=self._provide_agent_ui_injector, singleton=True, eager=True),
        ))

        return AgentInjector(agent_injector)

    #

    def bind_ui(self) -> inj.Elements:
        return self._ui_rewriter(inj.as_elements(
            inj.bind(UiConfig, to_const=self._config),

            inj.bind(UiId(uuid.uuid7())),

            #

            inj.bind(AgentInjector, to_async_fn=self._provide_agent_injector, singleton=True),

            #

            _bind_injector_import(AgentInjector, agn.Agent),
            _bind_injector_import(AgentInjector, agn.Session),

            _bind_injector_import(AgentInjector, AgentSetup),

            _bind_injector_import(AgentInjector, AgentUiInjector),

            #

            _bind_injector_import(AgentUiInjector, CommandsManager),

            #

            agent_event_subscribers().bind_items_provider(singleton=True),
        ))


##


def bind_ui(config: UiConfig) -> inj.Elements:
    return UiBinder(config).bind_ui()
