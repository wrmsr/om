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
def harness_commands() -> inj.ItemsBinderHelper[Command]:
    return inj.items_binder_helper[Command](Commands)


##


def _bind_command_singleton(cls: ta.Any) -> inj.Elemental:
    return inj.as_elements(
        inj.bind(cls, singleton=True),
        harness_commands().bind_item(to_key=cls),
    )


def bind_commands(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        _bind_command_singleton(CompactCommand),
        _bind_command_singleton(EchoCommand),
        _bind_command_singleton(EffortCommand),
        _bind_command_singleton(PermissionsCommand),
        _bind_command_singleton(QuitCommand),
        _bind_command_singleton(StatusCommand),
        _bind_command_singleton(SteerCommand),
    ])

    if config.exec:
        lst.extend([
            inj.bind(ProcessesCommand, singleton=True),
            harness_commands().bind_item(to_key=ProcessesCommand),
        ])

    lst.extend([
        harness_commands().bind_items_provider(singleton=True),

        inj.bind(CommandsManager, singleton=True),
    ])

    return inj.as_elements(*lst)
