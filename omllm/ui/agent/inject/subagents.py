"""
Injector wiring for subagents: each spawn is a sibling agent injector under `HostInjector` (standing up an agent scope
of its own - its own `Agent`, `TURN_SCOPE`, `TOOL_INVOCATION_SCOPE`, tools, system prompt, event subscribers, and
process scope - over the host's shared backends, permissions, and tool infrastructure). Subagents run headlessly with
no `AgentUiInjector`. See `omllm/agent/subagents/DESIGN.md`.
"""
import contextlib
import typing as ta
import uuid

from omcore import check
from omcore import inject as inj

from .... import agent as agn
from ....agent.inject.events import event_subscribers_binder as agent_event_subscribers
from ....agent.tools.inject import AgentTools
from ....agent.tools.inject import AgentToolSets
from ....core import processes as procs
from ..config import AgentConfig
from ..setup import AgentSetup
from ..systemprompt import EnvironmentSystemPromptContributor
from .instance import bind_agent_instance
from .systemprompt import system_prompt_contributors_binder
from .tools import bind_agent_tool_class


##


ParentProcessScope = ta.NewType('ParentProcessScope', procs.ProcessScope)


async def _provide_subagent_process_scope(
        aes: contextlib.AsyncExitStack,
        run_id: agn.SubagentRunId,
        parent: ParentProcessScope,
) -> procs.ProcessScope:
    # Closed with the subagent injector's stack: processes the subagent leaves behind die with it.
    return await aes.enter_async_context(parent.child(agn.subagent_process_scope_name(run_id)))


def _provide_subagent_tool_set(
        tools: AgentTools,
        tool_sets: AgentToolSets,
        profile: agn.SubagentProfile,
) -> agn.ToolSet:
    pool = agn.ToolSet([*tools, *(t for ts in tool_sets for t in ts)])

    # Nesting is not supported yet: the subagent tool is bound in the root agent alone, and must not appear here.
    check.not_in(agn.SubagentTool.name, pool.by_name)

    return profile.select_tools(pool)


def bind_subagent_agent(
        config: AgentConfig,
        *,
        run_id: agn.SubagentRunId,
        profile: agn.SubagentProfile,
        parent_process_scope: procs.ProcessScope,
        progress: agn.ToolProgressSink | None,
) -> inj.Elements:
    """
    A headless agent injector for one subagent run, created as a sibling child of `HostInjector` (no shadowing, no
    `AgentUiInjector`).
    """

    return inj.as_elements(
        bind_agent_instance(config),

        inj.bind(run_id),
        inj.bind(profile),

        # Profile-filtered tool set over this subagent's own tool instances.
        inj.bind(agn.ToolSet, singleton=True, to_fn=_provide_subagent_tool_set),

        # Its own system prompt: profile prompt + shared environment and fs guidance.
        inj.bind(agn.SubagentProfileSystemPromptContributor, singleton=True),
        system_prompt_contributors_binder().bind_item(to_key=agn.SubagentProfileSystemPromptContributor),
        system_prompt_contributors_binder().bind_item(to_key=EnvironmentSystemPromptContributor),
        *(
            [system_prompt_contributors_binder().bind_item(to_key=agn.FsSystemPromptContributor)]
            if config.fs else []
        ),

        # Its own event subscribers: the relay to the parent's progress sink, and none of the root's.
        inj.bind(agn.ToolProgressSink, to_const=progress if progress is not None else agn.NopToolProgressSink()),
        inj.bind(agn.SubagentEventRelay, singleton=True),
        agent_event_subscribers().bind_item(to_key=agn.SubagentEventRelay),

        # Its own process scope, under the parent's.
        inj.bind(ParentProcessScope, to_const=parent_process_scope),
        inj.bind(procs.ProcessScope, singleton=True, to_async_fn=_provide_subagent_process_scope),
    )


##


class ChildInjectorSubagentRunner(agn.SubagentRunner):
    """
    Bound in `HostInjector` so its `injector` is `HostInjector`: each subagent runs in a sibling managed child injector
    created for the run and torn down with it.
    """

    def __init__(
            self,
            *,
            injector: inj.AsyncInjector,
            config: AgentConfig,
    ) -> None:
        super().__init__()

        self._injector = injector
        self._config = config

    async def run_subagent(self, params: agn.SubagentRunParams) -> agn.SubagentRunResult:
        run_id = agn.SubagentRunId(uuid.uuid7())

        # The parent's scope is where the subagent's goes. In the ui every agent has one, the root scope at the top.
        parent_process_scope = check.not_none(check.not_none(params.env).processes)

        async with inj.create_asyncio_managed_injector(
            bind_subagent_agent(
                self._config,
                run_id=run_id,
                profile=params.profile,
                parent_process_scope=parent_process_scope,
                progress=params.progress,
            ),
            parent=self._injector,
        ) as child:
            agent = await child[agn.Agent]

            await (await child[AgentSetup]).run()

            await agent.update_state(lambda state: agn.apply_subagent_profile(state, params.profile))

            return await agn.drive_subagent(
                agent,
                run_id=run_id,
                prompt=params.prompt,
            )


##


def _explore_tool_names(config: AgentConfig) -> list[str]:
    """
    The read-only tools among those configured. Decided here, by the names of the tool classes bound for the config,
    which is a weak linkage: the concern owning a tool should be the one to say whether an explorer gets it.
    """

    names: list[str] = []

    if config.fs:
        names.extend([
            agn.GlobTool.name,
            agn.LsTool.name,
            agn.ReadTool.name,
        ])

    if config.exec and config.fs:
        names.append(agn.RipgrepTool.name)

    if config.web:
        names.extend([
            agn.WebFetchTool.name,
            agn.WebSearchTool.name,
        ])

    return names


def _provide_subagent_profiles(config: AgentConfig) -> agn.SubagentProfiles:
    profiles = [agn.GENERAL_SUBAGENT_PROFILE]

    # With nothing read-only to give it, there is no explorer to offer.
    if (explore_tool_names := _explore_tool_names(config)):
        profiles.append(agn.explore_subagent_profile(explore_tool_names))

    return agn.SubagentProfiles(profiles)


def bind_subagent_infrastructure(config: AgentConfig) -> inj.Elements:
    """Host-level subagent infrastructure: profiles and `ChildInjectorSubagentRunner` (bound in `HostInjector`)."""

    if not config.subagents:
        return inj.as_elements()

    return inj.as_elements(
        inj.bind(agn.SubagentProfiles, singleton=True, to_fn=_provide_subagent_profiles),

        inj.bind(ChildInjectorSubagentRunner, singleton=True),
        inj.bind(agn.SubagentRunner, to_key=ChildInjectorSubagentRunner),
    )


def bind_root_subagent_tool(config: AgentConfig) -> inj.Elements:
    """Binds `SubagentTool` into the root agent injector alone (subagents do not nest yet)."""

    if not config.subagents:
        return inj.as_elements()

    return inj.as_elements(
        inj.bind(agn.SubagentTool, singleton=True),
        bind_agent_tool_class(agn.SubagentTool),
    )
