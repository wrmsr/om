import typing as ta

from omcore import inject as inj
from omcore import lang

from ...commands.base import Command
from ...commands.base import Commands
from ...commands.compact import CompactCommand
from ...commands.effort import EffortCommand
from ...commands.manager import CommandsManager
from ...commands.permissions import PermissionsCommand
from ...commands.processes import ProcessesCommand
from ...commands.simple import EchoCommand
from ...commands.simple import QuitCommand
from ...commands.status import StatusCommand
from ...commands.steer import SteerCommand
from ..config import Config


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


def bind_commands(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        bind_command_singleton(CompactCommand),
        bind_command_singleton(EchoCommand),
        bind_command_singleton(EffortCommand),
        bind_command_singleton(PermissionsCommand),
        bind_command_singleton(QuitCommand),
        bind_command_singleton(StatusCommand),
        bind_command_singleton(SteerCommand),
    ])

    if config.exec:
        lst.extend([
            inj.bind(ProcessesCommand, singleton=True),
            commands_binder().bind_item(to_key=ProcessesCommand),
        ])

    lst.extend([
        commands_binder().bind_items_provider(singleton=True),

        inj.bind(CommandsManager, singleton=True),
    ])

    return inj.as_elements(*lst)
