from omcore import inject as inj

from .... import agent as agn
from ....agent.inject.events import bind_events
from ....agent.lifecycle.inject import bind_lifecycle
from ....agent.permissions.inject import bind_permissions
from ....agent.projection.inject import bind_projection
from ....agent.tools.inject import bind_tool_invocation
from ....agent.turns.inject import bind_turns
from ....core.asyncs.inject import bind_asyncio_job_runner
from ....core.asyncs.inject import bind_asyncio_runtime
from ..config import AgentConfig
from ..setup import AgentSetup
from .session import bind_sessions
from .subagents import bind_subagents
from .systemprompt import bind_system_prompt
from .tools import bind_tools
from .web import bind_web


##


def bind_agent(config: AgentConfig, *, remote_client: agn.RemoteAgentClient | None = None) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    lst.append(
        inj.bind(AgentConfig, to_const=config),
    )

    #

    lst.extend([
        bind_events(),
        bind_lifecycle(),
        bind_permissions(),
        bind_projection(),
        bind_tool_invocation(),
        bind_turns(),

        bind_asyncio_job_runner(),
        bind_asyncio_runtime(),
    ])

    #

    lst.extend([
        bind_sessions(config),
        bind_subagents(config),
        bind_system_prompt(config),
        bind_tools(config, remote_client=remote_client),
        bind_web(config),
    ])

    #

    lst.extend([
        inj.bind(agn.Agent, singleton=True),

        inj.bind(AgentSetup, singleton=True),
    ])

    #

    return inj.as_elements(*lst)
