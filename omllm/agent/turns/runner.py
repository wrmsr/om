from omcore.asyncs.asynclite import all as asl

from ... import llm
from ..backends import BackendManager
from ..projection.types import LlmContextBuilder
from ..types.turns import TurnParams
from ..types.turns import TurnResult
from ..types.turns import TurnRunner
from .loop import TurnLoop


##


class TurnLoopRunner(TurnRunner):
    def __init__(
            self,
            *,
            backends: BackendManager,
            sleeps: asl.Sleeps | None = None,
            context_builder: LlmContextBuilder | None = None,
    ) -> None:
        super().__init__()

        self._backends = backends
        self._sleeps = sleeps
        self._context_builder = context_builder

    async def run_turn(self, params: TurnParams) -> TurnResult:
        llm_backend = self._backends.get_backend(
            llm.ImmediateBackend,  # type: ignore[type-abstract]
            params.in_state.model,
        )

        loop = TurnLoop(
            new_messages=params.new_messages,
            config=params.in_state.turn_config,
            context=params.in_state.context,
            subscriber=params.subscriber,
            llm_backend=llm_backend,
            tool_env=params.in_state.tool_env,
            sleeps=self._sleeps,
            context_builder=self._context_builder,
            inbox=params.inbox,
        )

        return await loop.run()
