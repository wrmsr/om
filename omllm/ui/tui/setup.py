"""
await agent.update_state(
    lambda state: dc.replace(
        state,

        context=dc.replace(
            state.context,
            system_prompt='\n\n'.join([
                f'Current working directory: {cwd}',
            ]),
            tools=tool_set,
        ),
    ),
)

await agent.update_state(
    lambda state: dc.replace(
        state,

        context=dc.replace(
            state.context,
            system_prompt='\n\n'.join([
                f'Current working directory: {cwd}',
            ]),
            tools=tool_set,
        ),
    ),
)
"""
from omcore import dataclasses as dc

from ... import agent as agn
from ... import llm
from ...core import processes as procs
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
            root_process_scope: procs.RootProcessScope | None = None,
            initial_llm_options: InitialLlmOptions | None = None,
    ) -> None:
        super().__init__()

        self._agent = agent
        self._backends = backends
        self._tools = tools
        self._cwd = cwd
        self._root_process_scope = root_process_scope
        self._initial_llm_options = initial_llm_options

    async def run(self) -> None:
        def update(state: agn.State) -> agn.State:
            cwd = self._cwd.v if self._cwd is not None else None

            #

            context = dc.replace(
                state.context,

                system_prompt='\n\n'.join([
                    *([f'Current working directory: {cwd}'] if cwd is not None else []),
                ]),

                tools=self._tools,
            )

            #

            tool_env = agn.ToolEnvironment(
                cwd=cwd,

                processes=self._root_process_scope,
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

            return dc.replace(
                state,

                context=context,

                tool_env=tool_env,

                turn_config=turn_config,
            )

        await self._agent.update_state_exclusively(update)
