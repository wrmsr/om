import contextlib
import uuid

from omcore import dataclasses as dc

from ... import llm
from ..agent import Agent
from ..systemprompt.manager import SystemPromptManager
from ..systemprompt.types import SystemPromptContributors
from ..types.contexts import Context
from ..types.states import State
from ..types.tools import ToolEnvironment
from ..types.tools import ToolSet
from ..types.turns import TurnConfig
from ..types.turns import TurnRunner
from .driving import drive_subagent
from .driving import subagent_process_scope_name
from .profiles import SubagentProfiles
from .profiles import apply_subagent_profile
from .progress import SubagentEventRelay
from .systemprompt import SubagentProfileSystemPromptContributor
from .types import SubagentRunId
from .types import SubagentRunner
from .types import SubagentRunParams
from .types import SubagentRunResult


##


class AgentSubagentRunner(SubagentRunner):
    """
    Stands a subagent up by hand: a fresh `Agent` on the given turn runner, with its state built here from the profile
    and this runner's own configuration. The reference implementation, and the one for anywhere without an injector.
    """

    def __init__(
            self,
            *,
            turn_runner: TurnRunner,
            tools: ToolSet,
            profiles: SubagentProfiles | None = None,
            model: llm.Model | None = None,
            turn_config: TurnConfig | None = None,
            system_prompt_contributors: SystemPromptContributors | None = None,
    ) -> None:
        """
        The tools are the pool profiles pick from. The profiles are optional here only so the pool can be checked
        against them up front where they are known: a profile naming a tool the pool lacks raises here rather than on
        the first spawn.
        """

        super().__init__()

        self._turn_runner = turn_runner
        self._tools = tools
        self._model = model
        self._turn_config = turn_config
        self._system_prompt_contributors = system_prompt_contributors

        if profiles is not None:
            profiles.validate_tools(tools)

    def _build_system_prompt(self, params: SubagentRunParams) -> str:
        return SystemPromptManager(SystemPromptContributors([
            SubagentProfileSystemPromptContributor(profile=params.profile),
            *(self._system_prompt_contributors or []),
        ])).build_system_prompt()

    async def run_subagent(self, params: SubagentRunParams) -> SubagentRunResult:
        run_id = SubagentRunId(uuid.uuid7())
        profile = params.profile

        tools = profile.select_tools(self._tools)
        system_prompt = self._build_system_prompt(params)

        agent = Agent(turn_runner=self._turn_runner)

        if (progress := params.progress) is not None:
            agent.subscribe(SubagentEventRelay(
                progress=progress,
                run_id=run_id,
                profile=profile,
            ))

        async with contextlib.AsyncExitStack() as aes:
            tool_env: ToolEnvironment | None = None
            if (env := params.env) is not None:
                # Processes the subagent leaves behind die with it, not with the parent's scope.
                processes = env.processes
                if processes is not None:
                    processes = await aes.enter_async_context(processes.child(subagent_process_scope_name(run_id)))

                tool_env = dc.replace(env, processes=processes)

            def update(state: State) -> State:
                return apply_subagent_profile(
                    dc.replace(
                        state,
                        context=Context(
                            system_prompt=system_prompt,
                            tools=tools,
                        ),
                        model=self._model,
                        turn_config=self._turn_config,
                        tool_env=tool_env,
                    ),
                    profile,
                )

            await agent.update_state(update)

            return await drive_subagent(
                agent,
                run_id=run_id,
                prompt=params.prompt,
            )
