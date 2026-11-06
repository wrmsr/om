from omcore import inject as inj

from .... import agent as agn
from ....core.asyncs.inject import bind_job_runner
from ..config import AgentConfig
from ..setup import AgentSetup
from .context import bind_context
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


def bind_agent(config: AgentConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    lst.append(
        inj.bind(AgentConfig, to_const=config),
    )

    #

    lst.extend([
        bind_context(config),
        bind_events(config),
        bind_permissions(config),
        bind_sessions(config),
        bind_subagents(config),
        bind_system_prompt(config),
        bind_tool_invocation(config),
        bind_tools(config),
        bind_turns(config),
        bind_web(config),

        # Blocking work (the quickjs tool's evals) runs off the loop through this, one per injector, closed with it.
        bind_job_runner(),
    ])

    #

    lst.extend([
        inj.bind(agn.Agent, singleton=True),

        inj.bind(AgentSetup, singleton=True),
    ])

    #

    return inj.as_elements(*lst)
