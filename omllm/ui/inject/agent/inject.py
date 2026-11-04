from omcore import inject as inj

from ....core.asyncs.inject import bind_job_runner
from ...config import UiConfig
from .context import bind_context
from .core import bind_core
from .events import bind_events
from .permissions import bind_permissions
from .session import bind_sessions
from .subagents import bind_subagents
from .systemprompt import bind_system_prompt
from .toolinvocation import bind_tool_invocation
from .tools import bind_tools
from .turns import bind_turns
from .web import bind_web


##


def bind_agent(config: UiConfig) -> inj.Elements:
    lst: list[inj.Elemental] = [
        bind_core(config),
        bind_events(config),
        bind_permissions(config),
        bind_context(config),
        bind_tool_invocation(config),
        bind_turns(config),
        bind_sessions(config),
        bind_subagents(config),
        bind_system_prompt(config),
        bind_tools(config),
        bind_web(config),
    ]

    lst.append(
        # Blocking work (the quickjs tool's evals) runs off the loop through this, one per injector, closed with it.
        bind_job_runner(),
    )

    return inj.as_elements(*lst)
