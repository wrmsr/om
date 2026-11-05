from omcore.asyncs.asynclite import all as asl

from ...core.asyncs.base import AsyncGroupRunner
from ..lifecycle.managers import ContextLifecycleManager
from ..projection.types import LlmContextBuilder
from ..types.tools import ToolInvoker
from ..types.turns import TurnParams
from ..types.turns import TurnResult
from ..types.turns import TurnRunner
from .loop import TurnLoop


##


class LoopTurnRunner(TurnRunner):
    def __init__(
            self,
            *,
            tool_invoker: ToolInvoker | None = None,
            cancellation: asl.Cancellation,
            group_runner: AsyncGroupRunner,
            sleeps: asl.Sleeps | None = None,
            context_builder: LlmContextBuilder | None = None,
            context_lifecycle_manager: ContextLifecycleManager | None = None,
    ) -> None:
        super().__init__()

        self._cancellation = cancellation
        self._group_runner = group_runner
        self._sleeps = sleeps
        self._context_builder = context_builder
        self._context_lifecycle_manager = context_lifecycle_manager
        self._tool_invoker = tool_invoker

    async def run_turn(self, params: TurnParams) -> TurnResult:
        loop = TurnLoop(
            params,

            tool_invoker=self._tool_invoker,
            cancellation=self._cancellation,
            group_runner=self._group_runner,
            sleeps=self._sleeps,
            context_builder=self._context_builder,
            context_lifecycle_manager=self._context_lifecycle_manager,
        )

        return await loop.run()
