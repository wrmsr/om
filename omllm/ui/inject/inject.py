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
from ..agent.inject.inject import bind_agent
from ..backends.inject import bind_backends
from ..commands.inject import bind_commands
from ..commands.manager import CommandsManager
from ..config import UiConfig
from ..types import UiId
from .runtime import bind_runtime


##


@dc.dataclass(frozen=True, kw_only=True)
class _AgentExports:
    agent: agn.Agent
    session: agn.Session

    # TODO: events / agent_event_subscribers

    commands_manager: CommandsManager


async def _provide_agent_exports(
        config: UiConfig,
        *,
        app_injector: inj.AsyncInjector,
        aes: contextlib.AsyncExitStack,
) -> ta.Any:
    @contextlib.asynccontextmanager
    async def provide():
        async with inj.create_asyncio_managed_injector(
                inj.bind(UiConfig, to_const=config),

                bind_agent(config),
                bind_backends(config),
                bind_commands(config),

                inj.bind(ui.QuitSignal, to_const=(await app_injector[ui.QuitSignal])),
        ) as injector:
            yield _AgentExports(
                agent=(await injector[agn.Agent]),
                session=(await injector[agn.Session]),

                commands_manager=(await injector[CommandsManager]),
            )

    return await aes.enter_async_context(provide())


def _bind_agent_export(attr, cls):
    return inj.bind(cls, to_fn=inj.target(x=_AgentExports)(lambda x: getattr(x, attr)), singleton=True)


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
            inj.bind(_AgentExports, to_async_fn=_provide_agent_exports, singleton=True),

            _bind_agent_export('agent', agn.Agent),
            _bind_agent_export('session', agn.Session),

            _bind_agent_export('commands_manager', CommandsManager),
        ])

    else:
        lst.extend([
            bind_agent(config),
            bind_backends(config),
            bind_commands(config),
        ])

    return inj.as_elements(*lst)
