from omcore import dataclasses as dc

from ... import agent as agn
from ... import llm
from ...harness.prompts.base import PromptContext
from ...harness.prompts.builders import PromptBuilder
from .config import Config


##


class AgentInitializer:
    """Shared frontend setup. Prompt configuration belongs to the host, independently of the tool environment."""

    def __init__(
            self,
            *,
            agent: agn.Agent,
            backends: agn.BackendManager,
            tools: agn.ToolSet,
            prompts: PromptBuilder,
            config: Config,
    ) -> None:
        super().__init__()

        self._agent = agent
        self._backends = backends
        self._tools = tools
        self._prompts = prompts
        self._config = config

    async def initialize(self, *, tool_env: agn.ToolEnvironment | None = None) -> None:
        model = self._backends.get_backend(
            llm.ImmediateBackend, self._agent.state.model,  # type: ignore[type-abstract]
        ).model
        llm.validate_reasoning_effort(model, self._config.effort, with_tools=bool(self._tools))
        prompt = self._prompts.build(PromptContext(tool_names=frozenset(t.name for t in self._tools)))

        def update(state: agn.State) -> agn.State:
            config = state.turn_config or agn.TurnConfig()
            return dc.replace(
                state,
                context=dc.replace(state.context, system_prompt=prompt, tools=self._tools),
                tool_env=tool_env,
                turn_config=dc.replace(
                    config,
                    llm_retry=config.llm_retry or agn.LlmRetryConfig(),
                    llm_options=(config.llm_options or llm.Options()).merge(llm.Options(
                        reasoning_effort=self._config.effort,
                        thinking=self._config.thinking,
                    )),
                ),
            )

        await self._agent.update_state_exclusively(update)
