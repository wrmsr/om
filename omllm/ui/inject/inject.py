"""
TODO:
 - AgentUi child injector
"""
import contextlib
import typing as ta
import uuid

from omcore import dataclasses as dc
from omcore import inject as inj

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
from .runtime import bind_runtime


##


class _InjectorBox(dc.Box[inj.AsyncInjector], abstract=True):
    pass


def _bind_injector_import(box_cls: type[_InjectorBox], key: ta.Any) -> inj.Elemental:
    return inj.bind(key, to_async_fn=inj.target(i=box_cls)(lambda i: i.v[key]))


#


class _AppInjector(_InjectorBox, final=True):
    pass


class _AgentInjector(_InjectorBox, final=True):
    pass


async def _provide_agent_injector(
        config: UiConfig,
        *,
        app_injector: inj.AsyncInjector,
        aes: contextlib.AsyncExitStack,
) -> _AgentInjector:
    @contextlib.asynccontextmanager
    async def provide():
        async with inj.create_asyncio_managed_injector(
                inj.bind(UiConfig, to_const=config),

                bind_agent(config),
                bind_backends(config),
                bind_commands(config),

                bind_runtime(config),

                inj.bind(_AppInjector(app_injector)),

                _bind_injector_import(_AppInjector, ui.QuitSignal),
                _bind_injector_import(_AppInjector, ui.TextDisplayer),
        ) as agent_injector:
            yield _AgentInjector(agent_injector)

    return await aes.enter_async_context(provide())


##


_USE_AGENT_INJECTOR = False


def bind_ui(config: UiConfig) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(UiConfig, to_const=config),

        bind_runtime(config),

        inj.bind(UiId(uuid.uuid7())),
    ]

    if _USE_AGENT_INJECTOR:
        lst.extend([
            inj.bind(_AgentInjector, to_async_fn=_provide_agent_injector, singleton=True),

            _bind_injector_import(_AgentInjector, agn.Agent),
            _bind_injector_import(_AgentInjector, agn.Session),

            _bind_injector_import(_AgentInjector, AgentSetup),

            _bind_injector_import(_AgentInjector, CommandsManager),

            agent_event_subscribers().bind_items_provider(singleton=True),
        ])

    else:
        lst.extend([
            bind_agent(config),
            bind_backends(config),
            bind_commands(config),
        ])

    return inj.as_elements(*lst)
