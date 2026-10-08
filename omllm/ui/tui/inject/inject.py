from omcore import inject as inj

from ...inject import bind_ui
from ..config import Config
from .agent import bind_agent
from .backends import bind_backends
from .commands import bind_commands
from .permissions import bind_permissions
from .rendering import bind_rendering
from .session import bind_sessions
from .tools import bind_tools
from .web import bind_web


##


def bind_tui(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(config),

        bind_ui(),

        bind_agent(config),
        bind_backends(config),
        bind_commands(config),
        bind_permissions(config),
        bind_rendering(),
        bind_sessions(config),
        bind_tools(config),
        bind_web(config),
    ]

    return inj.as_elements(*lst)
