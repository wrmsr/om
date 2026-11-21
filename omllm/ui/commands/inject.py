import typing as ta

from omcore import inject as inj
from omcore import lang

from ..config import UiConfig
from ..inject.injectors import AgentUiInjector
from ..inject.injectors import bind_agent_ui_injector_bindings
from .base import Command
from .base import Commands
from .compact import CompactCommand
from .effort import EffortCommand
from .manager import CommandsManager
from .model import ModelCommand
from .permissions import PermissionsCommand
from .processes import ProcessesCommand
from .simple import EchoCommand
from .simple import QuitCommand
from .status import StatusCommand
from .steer import SteerCommand


##


@lang.cached_function
def commands_binder() -> inj.ItemsBinderHelper[Command]:
    return inj.items_binder_helper[Command](Commands)


def bind_command_singleton(cls: ta.Any) -> inj.Elemental:
    return inj.as_elements(
        inj.bind(cls, singleton=True),
        commands_binder().bind_item(to_key=cls),
    )


##


class _UI_COMMANDS(lang.Marker):  # noqa
    pass


async def _provide_commands(
        ui_injector: inj.AsyncInjector,
        agent_ui_injector: AgentUiInjector,
) -> Commands:
    ui_commands = await ui_injector[inj.as_key(Commands, tag=_UI_COMMANDS)]
    agent_ui_commands = await agent_ui_injector.v[Commands]
    return Commands([
        *ui_commands,
        *agent_ui_commands,
    ])


##


def bind_commands(config: UiConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        bind_command_singleton(EchoCommand),
        bind_command_singleton(QuitCommand),

        bind_agent_ui_injector_bindings(
            bind_command_singleton(CompactCommand),
            bind_command_singleton(EffortCommand),
            bind_command_singleton(ModelCommand),
            bind_command_singleton(PermissionsCommand),
            bind_command_singleton(StatusCommand),
            bind_command_singleton(SteerCommand),
        ),
    ])

    if config.exec:
        lst.extend([
            bind_agent_ui_injector_bindings(
                inj.bind(ProcessesCommand, singleton=True),
                commands_binder().bind_item(to_key=ProcessesCommand),
            ),
        ])

    lst.extend([
        commands_binder().bind_items_provider(singleton=True, tag=_UI_COMMANDS),
        inj.bind(Commands, to_async_fn=_provide_commands, singleton=True),

        bind_agent_ui_injector_bindings(
            commands_binder().bind_items_provider(singleton=True),
        ),

        inj.bind(CommandsManager, singleton=True),
    ])

    return inj.as_elements(*lst)
