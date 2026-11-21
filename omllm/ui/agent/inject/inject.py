from omcore import inject as inj

from .... import agent as agn
from ....agent.lifecycle.inject import bind_lifecycle
from ....agent.permissions.inject import bind_permissions
from ....agent.projection.inject import bind_projection
from ....agent.tools.inject import provide_tool_set
from ....core import processes as procs
from ....core.asyncs.inject import bind_asyncio_job_runner
from ....core.asyncs.inject import bind_asyncio_runtime
from ..config import AgentConfig
from .instance import bind_agent_instance
from .session import bind_agent_session
from .session import bind_session_infrastructure
from .subagents import bind_root_subagent_tool
from .subagents import bind_subagent_infrastructure
from .systemprompt import bind_root_system_prompt
from .systemprompt import bind_system_prompt_infrastructure
from .tools import bind_tool_infrastructure
from .web import bind_web


##


def bind_agent_host(config: AgentConfig) -> inj.Elements:
    """
    Host-level infrastructure shared across every agent (root agent, subagents, and any sibling tenant agents) in a
    running host process: runtime, job runner, permissions, projection, context lifecycle, tool ops, session db, web
    clients, shared prompt contributors, and the subagent runner.
    """

    return inj.as_elements(
        inj.bind(AgentConfig, to_const=config),

        bind_asyncio_job_runner(),
        bind_asyncio_runtime(),

        bind_lifecycle(),
        bind_permissions(),
        bind_projection(),

        bind_session_infrastructure(config),
        bind_subagent_infrastructure(config),
        bind_system_prompt_infrastructure(config),
        bind_tool_infrastructure(config),
        bind_web(config),
    )


def bind_root_agent(config: AgentConfig) -> inj.Elements:
    """
    Root-agent injector bindings, created as a child of `HostInjector`: per-agent instance bindings (turn and tool
    scopes, tool classes, `Agent`, `AgentSetup`), root `ProcessScope`, session, root system prompt, `ToolSet`, and
    (when enabled) `SubagentTool`.
    """

    return inj.as_elements(
        bind_agent_instance(config),

        inj.bind(procs.ProcessScope, to_key=procs.RootProcessScope),

        bind_agent_session(config),
        bind_root_system_prompt(config),
        bind_root_subagent_tool(config),

        inj.bind(agn.ToolSet, to_fn=provide_tool_set, singleton=True),
    )
