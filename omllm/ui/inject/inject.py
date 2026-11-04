import uuid

from omcore import inject as inj

from ..config import UiConfig
from ..types import UiId
from .agent.inject import bind_agent
from .backends import bind_backends
from .commands import bind_commands


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
