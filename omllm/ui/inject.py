import uuid

from omcore import inject as inj

from .agent.inject.inject import bind_agent
from .backends.inject import bind_backends
from .commands.inject import bind_commands
from .config import UiConfig
from .types import UiId


##


def bind_ui(config: UiConfig) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(UiConfig, to_const=config),

        bind_agent(config),
        bind_backends(config),
        bind_commands(config),

        inj.bind(UiId(uuid.uuid7())),
    ]

    return inj.as_elements(*lst)
