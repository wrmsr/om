from ... import llm
from ..backends import BackendManager
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
    ) -> None:
        super().__init__()

        self._backends = backends

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
        )

        return await loop.run()
