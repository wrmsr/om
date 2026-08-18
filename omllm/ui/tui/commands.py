from omcore import inject as inj
from omcore import lang

from ... import harness as har
from .config import Config


##


@lang.cached_function
def harness_commands() -> inj.ItemsBinderHelper[har.Command]:
    return inj.items_binder_helper[har.Command](har.Commands)


##


def bind_commands(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        inj.bind(har.EchoCommand, singleton=True),
        harness_commands().bind_item(to_key=har.EchoCommand),

        inj.bind(har.QuitCommand, singleton=True),
        harness_commands().bind_item(to_key=har.QuitCommand),

        inj.bind(har.PermissionsCommand, singleton=True),
        harness_commands().bind_item(to_key=har.PermissionsCommand),
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
