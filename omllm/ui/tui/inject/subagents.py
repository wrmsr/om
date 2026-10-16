"""
Injector wiring for subagents: each spawn is a child injector of the app's, standing up an agent scope of its own - its
own agent, turn scope, tools, system prompt, event subscribers, and process scope - over the app's shared backends,
permissions, and tool infrastructure. See `omllm/agent/subagents/DESIGN.md`.

The child shadows the root's bindings of the per-agent things (the agent, the tool set, the system prompt manager, the
event subscribers, the turn runner) because the root injector is today also the root agent's injector. That shadowing
is a known wart of child injectors, accepted here as the way to get an agent scope running ahead of the split of the
root into an app injector and an agent injector per agent, the root agent's included.
"""
import contextlib
import contextvars
import typing as ta
import uuid

from omcore import check
from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from ....core import processes as procs
from ..config import Config
from ..setup import AgentSetup
from .agent import AgentEventSubscribers
from .agent import ScopedTurnRunner
from .agent import agent_event_subscribers
from .systemprompt import CwdSystemPromptContributor
from .systemprompt import system_prompt_contributors_binder
from .tools import AgentTools
from .tools import AgentToolSets
from .tools import bind_agent_tool_class
from .tools import bind_tool_classes


##


class SUBAGENT_TURN_SCOPED(lang.Marker):  # noqa
    pass


_SUBAGENT_TURN_SCOPE_CONTEXT: contextvars.ContextVar = contextvars.ContextVar(
    f'{__name__}._SUBAGENT_TURN_SCOPE_CONTEXT',
)

# A turn scope of the subagent's own. A child injector may not redeclare its ancestor's `TURN_SCOPE`, and the parent's
# opening of it is in any case visible in the task a subagent runs in, so a nested opening would be refused. Each child
# injector registers this scope for itself: the scope's state is per injector, so any number of subagents run at once
# without seeing each other's openings.
SUBAGENT_TURN_SCOPE: ta.Final = inj.DelimitedScope(
    SUBAGENT_TURN_SCOPED,
    context=inj.ContextVarScopeContext(_SUBAGENT_TURN_SCOPE_CONTEXT),
)


def _provide_subagent_turn_runner(injector: inj.AsyncInjector) -> ScopedTurnRunner:
    return ScopedTurnRunner(
        injector=injector,
        scope=SUBAGENT_TURN_SCOPE,
    )


##


ParentProcessScope = ta.NewType('ParentProcessScope', procs.ProcessScope)


async def _provide_subagent_process_scope(
        aes: contextlib.AsyncExitStack,
        run_id: agn.SubagentRunId,
        parent: ParentProcessScope,
) -> procs.ProcessScope:
    # Closed with the child injector's stack: processes the subagent leaves behind die with it.
    return await aes.enter_async_context(parent.child(agn.subagent_process_scope_name(run_id)))


def _provide_subagent_tool_set(
        tools: AgentTools,
        tool_sets: AgentToolSets,
        profile: agn.SubagentProfile,
) -> agn.ToolSet:
    pool = agn.ToolSet([*tools, *(t for ts in tool_sets for t in ts)])

    # Nesting is not supported yet: the subagent tool is bound in the root alone, and must not have found its way here.
    check.not_in(agn.SubagentTool.name, pool.by_name)

    return profile.select_tools(pool)


def bind_subagent_agent(
        config: Config,
        *,
        run_id: agn.SubagentRunId,
        profile: agn.SubagentProfile,
        parent_process_scope: procs.ProcessScope,
        progress: agn.ToolProgressSink | None,
        aes: contextlib.AsyncExitStack,
) -> inj.Elements:
    """An agent scope for one subagent run, to be created as a child of the app's injector."""

    return inj.as_elements(
        inj.bind(contextlib.AsyncExitStack, to_const=aes),

        inj.bind(run_id),
        inj.bind(profile),

        # Its own turn scope, seeded and populated as the root agent's is.
        inj.bind_scope(SUBAGENT_TURN_SCOPE),
        inj.bind_scope_seed(agn.TurnParams, SUBAGENT_TURN_SCOPE),
        inj.bind(agn.TurnLoop, in_=SUBAGENT_TURN_SCOPE),
        inj.bind(agn.TurnLoopRunner, in_=SUBAGENT_TURN_SCOPE),
        inj.bind(ScopedTurnRunner, singleton=True, to_fn=_provide_subagent_turn_runner),
        inj.bind(agn.TurnRunner, to_key=ScopedTurnRunner),

        inj.bind(agn.Agent, singleton=True),

        # Its own tools: fresh instances of the configured tool classes over the shared infrastructure, of which the
        # profile gets its pick.
        bind_tool_classes(config),
        inj.bind(agn.ToolSet, singleton=True, to_fn=_provide_subagent_tool_set),

        # Its own system prompt: what a subagent of its profile is told, then what the root agent is told of its
        # surroundings.
        system_prompt_contributors_binder().bind_items_provider(singleton=True),
        inj.bind(agn.SubagentProfileSystemPromptContributor, singleton=True),
        system_prompt_contributors_binder().bind_item(to_key=agn.SubagentProfileSystemPromptContributor),
        system_prompt_contributors_binder().bind_item(to_key=CwdSystemPromptContributor),
        inj.bind(agn.SystemPromptManager, singleton=True),

        # Its own event subscribers: the relay to the parent's progress sink, and none of the root's.
        agent_event_subscribers().bind_items_provider(singleton=True),
        inj.bind(agn.ToolProgressSink, to_const=progress if progress is not None else agn.NopToolProgressSink()),
        inj.bind(agn.SubagentEventRelay, singleton=True),
        agent_event_subscribers().bind_item(to_key=agn.SubagentEventRelay),

        # Its own process scope, under the parent's.
        inj.bind(ParentProcessScope, to_const=parent_process_scope),
        inj.bind(procs.ProcessScope, singleton=True, to_async_fn=_provide_subagent_process_scope),

        inj.bind(AgentSetup, singleton=True),
    )


##


class ChildInjectorSubagentRunner(agn.SubagentRunner):
    """Runs each subagent in a child injector of the app's, created for the run and torn down with it."""

    def __init__(
            self,
            *,
            injector: inj.AsyncInjector,
            config: Config,
    ) -> None:
        super().__init__()

        self._injector = injector
        self._config = config

    async def run_subagent(self, params: agn.SubagentRunParams) -> agn.SubagentRunResult:
        run_id = agn.SubagentRunId(uuid.uuid7())

        # The parent's scope is where the subagent's goes. In the ui every agent has one, the root scope at the top.
        parent_process_scope = check.not_none(check.not_none(params.env).processes)

        async with contextlib.AsyncExitStack() as aes:
            child = await inj.create_asyncio_injector(
                bind_subagent_agent(
                    self._config,
                    run_id=run_id,
                    profile=params.profile,
                    parent_process_scope=parent_process_scope,
                    progress=params.progress,
                    aes=aes,
                ),
                parent=self._injector,
            )

            # What a frontend's main does with its injector.
            agent = await child[agn.Agent]

            for el in await child[AgentEventSubscribers]:
                agent.subscribe(el)

            await (await child[AgentSetup]).run()

            await agent.update_state(lambda state: agn.apply_subagent_profile(state, params.profile))

            return await agn.drive_subagent(
                agent,
                run_id=run_id,
                prompt=params.prompt,
            )


##


def _explore_tool_names(config: Config) -> list[str]:
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


def _provide_subagent_profiles(config: Config) -> agn.SubagentProfiles:
    profiles = [agn.GENERAL_SUBAGENT_PROFILE]

    # With nothing read-only to give it, there is no explorer to offer.
    if (explore_tool_names := _explore_tool_names(config)):
        profiles.append(agn.explore_subagent_profile(explore_tool_names))

    return agn.SubagentProfiles(profiles)


def bind_subagents(config: Config) -> inj.Elements:
    if not config.subagents:
        return inj.as_elements()

    return inj.as_elements(
        inj.bind(agn.SubagentProfiles, singleton=True, to_fn=_provide_subagent_profiles),

        inj.bind(ChildInjectorSubagentRunner, singleton=True),
        inj.bind(agn.SubagentRunner, to_key=ChildInjectorSubagentRunner),

        inj.bind(agn.SubagentTool, singleton=True),
        bind_agent_tool_class(agn.SubagentTool),
    )
