import uuid

from omcore import inject as inj

from ..config import UiConfig
from ..types import UiId
from .agent import bind_agent
from .backends import bind_backends
from .commands import bind_commands
from .permissions import bind_permissions
from .session import bind_sessions
from .subagents import bind_subagents
from .systemprompt import bind_system_prompt
from .tools import bind_tools
from .web import bind_web


##


def bind_ui(config: UiConfig) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(UiConfig, to_const=config),

        bind_agent(config),
        bind_backends(config),
        bind_commands(config),
        bind_permissions(config),
        bind_sessions(config),
        bind_subagents(config),
        bind_system_prompt(config),
        bind_tools(config),
        bind_web(config),

        inj.bind(UiId(uuid.uuid7())),
    ]

    return inj.as_elements(*lst)
