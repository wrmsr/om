from omcore import inject as inj

from ...inject import bind_ui
from ..config import Config
from ..setup import AgentInitializer
from .agent import bind_agent
from .backends import bind_backends
from .commands import bind_commands
from .permissions import bind_permissions
from .prompts import bind_prompts
from .session import bind_sessions
from .skills import bind_skills
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
        bind_prompts(config),
        bind_sessions(config),
        bind_skills(config),
        bind_tools(config),
        bind_web(config),
        inj.bind(AgentInitializer, singleton=True),
    ]

    return inj.as_elements(*lst)
