from omcore import dataclasses as dc

from .. import llm
from .agent import Agent
from .backends import BackendManager
from .lifecycle.managers import ContextLifecycleManager
from .lifecycle.managers import StandardContextLifecycleManager
from .projection.builders import StandardLlmContextBuilder
from .projection.types import LlmContextBuilder
from .types.lifecycle import ContextReduction
from .types.states import State
from .types.turns import TurnConfig


##


class ContextCompactionRunner:
    """
    Compacts an agent's context on request: the reduction a run makes under pressure, made outside of one and
    unconditionally. The agent is held against prompts for the duration, so that no run starts on the state about to
    be replaced. What changed is returned, and reaches the agent's subscribers as a state update - a run announces its
    own reductions as they happen, but there is no run here to.
    """

    def __init__(
            self,
            *,
            backends: BackendManager,
            context_builder: LlmContextBuilder | None = None,
            context_lifecycle_manager: ContextLifecycleManager | None = None,
    ) -> None:
        super().__init__()

        self._backends = backends
        if context_builder is None:
            context_builder = StandardLlmContextBuilder()
        self._context_builder = context_builder
        if context_lifecycle_manager is None:
            context_lifecycle_manager = StandardContextLifecycleManager()
        self._context_lifecycle_manager = context_lifecycle_manager

    async def run_compaction(
            self,
            agent: Agent,
            *,
            instructions: str | None = None,
    ) -> ContextReduction | None:
        """
        Returns what changed, or None when there was nothing to compact. Raises NoContextCompactorError when the
        lifecycle manager has no compactor, and AgentBusyError when a run is in progress.
        """

        reductions: list[ContextReduction | None] = []

        async def fn(state: State) -> State:
            backend = self._backends.get_backend(
                llm.ImmediateBackend,  # type: ignore[type-abstract]
                state.model,
            )
            turn_config = state.turn_config if state.turn_config is not None else TurnConfig()

            result = await self._context_lifecycle_manager.compact(
                state.context,
                builder=self._context_builder,
                backend=backend,
                options=turn_config.llm_options,
                config=turn_config.context_lifecycle,
                instructions=instructions,
            )
            reductions.append(result.reduction)

            return dc.replace(state, context=result.context)

        await agent.update_state_exclusively(fn)

        [reduction] = reductions
        return reduction
