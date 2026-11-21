from omcore import inject as inj

from .... import agent as agn
from ....agent.inject.events import bind_events
from ....agent.tools.inject import bind_tool_invocation
from ....agent.turns.inject import bind_turns
from ..config import AgentConfig
from ..setup import AgentSetup
from .systemprompt import system_prompt_contributors_binder
from .tools import bind_tool_classes


##


def bind_agent_instance(config: AgentConfig) -> inj.Elements:
    """
    Core per-agent bindings shared by every agent injector (the root agent and every subagent alike), created as a
    sibling child of `HostInjector`: its own turn and tool-invocation scopes (`TURN_SCOPE`, `TOOL_INVOCATION_SCOPE`),
    event subscribers, tool instances, system prompt manager, `Agent`, and `AgentSetup`.
    """

    return inj.as_elements(
        bind_turns(),
        bind_tool_invocation(),
        bind_events(),

        bind_tool_classes(config),

        system_prompt_contributors_binder().bind_items_provider(singleton=True),
        inj.bind(agn.SystemPromptManager, singleton=True),

        inj.bind(agn.Agent, singleton=True),
        inj.bind(AgentSetup, singleton=True),
    )
