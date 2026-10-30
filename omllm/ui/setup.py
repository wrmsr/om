from omcore import dataclasses as dc

from .. import agent as agn
from .. import llm
from ..core import processes as procs
from .types import InitialLlmOptions
from .types import TargetCwd


##


class AgentSetup:
    """Shared frontend setup. Prompt configuration belongs to the host, independently of the tool environment."""

    def __init__(
            self,
            *,
            agent: agn.Agent,
            backends: agn.BackendManager,
            tools: agn.ToolSet,
            cwd: TargetCwd | None = None,
            system_prompts: agn.SystemPromptManager,
            process_scope: procs.ProcessScope | None = None,
            initial_llm_options: InitialLlmOptions | None = None,
    ) -> None:
        """The process scope is the agent's own: the root scope for the root agent, a child of its parent's beneath."""

        super().__init__()

        self._agent = agent
        self._backends = backends
        self._tools = tools
        self._cwd = cwd
        self._system_prompts = system_prompts
        self._process_scope = process_scope
        self._initial_llm_options = initial_llm_options

    async def run(self) -> None:
        def update(state: agn.State) -> agn.State:
            cwd = self._cwd.v if self._cwd is not None else None

            #

            context = dc.replace(
                state.context,

                system_prompt=self._system_prompts.build_system_prompt(),

                tools=self._tools,
            )

            #

            tool_env = agn.ToolEnvironment(
                cwd=cwd,

                processes=self._process_scope,
            )

            #

            turn_config = state.turn_config or agn.TurnConfig()

            if turn_config.llm_retry is None:
                turn_config = dc.replace(
                    turn_config,

                    llm_retry=agn.LlmRetryConfig(),
                )

            if self._initial_llm_options is not None:
                turn_config = dc.replace(
                    turn_config,

                    llm_options=(turn_config.llm_options or llm.Options()).merge(self._initial_llm_options.v),
                )

            #

            llm_backend = self._backends.get_backend(
                llm.ImmediateBackend,  # type: ignore[type-abstract]
                state.model,
            )

            model = llm_backend.model

            # An unsupported effort is rejected here, at startup, rather than by the first request - and against the
            # tools actually installed, as some models narrow their supported levels when tools are present.
            if (
                    turn_config.llm_options is not None and
                    (effort := turn_config.llm_options.reasoning_effort) is not None
            ):
                llm.validate_reasoning_effort(
                    model,
                    effort,
                    with_tools=bool(self._tools),
                )

            #

            return dc.replace(
                state,

                context=context,

                model=model,

                tool_env=tool_env,

                turn_config=turn_config,
            )

        await self._agent.update_state_exclusively(update)
