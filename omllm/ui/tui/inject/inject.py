from omcore import inject as inj

from ..config import Config
from .agent import bind_agent
from .backends import bind_backends
from .commands import bind_commands
from .permissions import bind_permissions
from .session import bind_sessions
from .tools import bind_tools


##


def bind_tui(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = [
        bind_agent(config),
        bind_backends(config),
        bind_commands(config),
        bind_permissions(config),
        bind_sessions(config),
        bind_tools(config),
    ]

    return inj.as_elements(*lst)
