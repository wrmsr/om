import contextlib
import typing as ta
import uuid

from omcore import inject as inj
from omcore import lang

from ... import agent as agn
from ...agent.inject.events import event_subscribers_binder as agent_event_subscribers
from ...core import ui
from ...core.asyncs.inject import bind_asyncio_job_runner
from ...core.asyncs.inject import bind_asyncio_runtime
from ..agent.inject.inject import bind_agent
from ..agent.setup import AgentSetup
from ..backends.inject import bind_backends
from ..commands.inject import bind_commands
from ..config import UiConfig
from ..types import UiId
from .injectors import AgentInjector
from .injectors import AgentInjectorBindings
from .injectors import AgentUiInjector
from .injectors import AgentUiInjectorBindings
from .injectors import UiInjector
from .injectors import agent_injector_bindings_binder
from .injectors import agent_ui_injector_bindings_binder
from .injectors import bind_injector_import


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

            #

            bind_injector_import(UiInjector, ui.QuitSignal),
            bind_injector_import(UiInjector, ui.TextDisplayer),
        ))

    async def _provide_agent_ui_injector(
            self,
            *,
            agent_injector: inj.AsyncInjector,
    ) -> AgentUiInjector:
        agent_ui_injector = await inj.create_asyncio_injector(
            self.bind_agent_ui(),

            #

            *(await agent_injector[AgentUiInjectorBindings]),

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

            bind_injector_import(UiInjector, agn.PermissionAsker),

            bind_injector_import(UiInjector, AgentUiInjectorBindings),
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

            *(await ui_injector[AgentInjectorBindings]),

            inj.bind(AgentUiInjector, to_async_fn=self._provide_agent_ui_injector, singleton=True, eager=True),
        ))

        return AgentInjector(agent_injector)

    #

    def bind_ui(self) -> inj.Elements:
        return self._ui_rewriter(inj.as_elements(
            inj.bind(UiConfig, to_const=self._config),

            inj.bind(UiId(uuid.uuid7())),

            #

            bind_commands(self._config),

            bind_asyncio_job_runner(),
            bind_asyncio_runtime(),

            #

            inj.bind(AgentInjector, to_async_fn=self._provide_agent_injector, singleton=True),

            #

            agent_injector_bindings_binder().bind_items_provider(singleton=True),
            agent_ui_injector_bindings_binder().bind_items_provider(singleton=True),

            #

            bind_injector_import(AgentInjector, agn.Agent),
            bind_injector_import(AgentInjector, agn.Session),

            bind_injector_import(AgentInjector, AgentSetup),

            bind_injector_import(AgentInjector, AgentUiInjector),

            #

            agent_event_subscribers().bind_items_provider(singleton=True),
        ))


##


def bind_ui(
        config: UiConfig,
        **kwargs: ta.Any,
) -> inj.Elements:
    return UiBinder(config, **kwargs).bind_ui()
