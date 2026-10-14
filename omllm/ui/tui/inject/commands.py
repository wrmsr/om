import typing as ta

from omcore import inject as inj
from omcore import lang

from .... import harness as har
from ..config import Config


##


@lang.cached_function
def harness_commands() -> inj.ItemsBinderHelper[har.Command]:
    return inj.items_binder_helper[har.Command](har.Commands)


##


def _bind_command_singleton(cls: ta.Any) -> inj.Elemental:
    return inj.as_elements(
        inj.bind(cls, singleton=True),
        harness_commands().bind_item(to_key=cls),
    )


def bind_commands(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        _bind_command_singleton(har.CompactCommand),
        _bind_command_singleton(har.EchoCommand),
        _bind_command_singleton(har.EffortCommand),
        _bind_command_singleton(har.PermissionsCommand),
        _bind_command_singleton(har.QuitCommand),
        _bind_command_singleton(har.StatusCommand),
        _bind_command_singleton(har.SteerCommand),
    ])

    if config.exec:
        lst.extend([
            inj.bind(har.ProcessesCommand, singleton=True),
            harness_commands().bind_item(to_key=har.ProcessesCommand),
        ])

    lst.extend([
        harness_commands().bind_items_provider(singleton=True),

        inj.bind(har.CommandsManager, singleton=True),
    ])

    return inj.as_elements(*lst)
