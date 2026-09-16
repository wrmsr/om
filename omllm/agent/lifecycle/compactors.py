import abc

from omcore import lang

from ..types.context_lifecycle import ContextProjection
from ..types.context_lifecycle import ContextReductionReason
from ..types.contexts import Context


##


class ContextCompactor(lang.Abstract):
    """Optional semantic reducer used after deterministic tool-result pruning is insufficient."""

    @abc.abstractmethod
    async def compact(
            self,
            context: Context,
            *,
            target_tokens: int,
            reason: ContextReductionReason,
    ) -> ContextProjection | None:
        """Returns a complete replacement projection, or None when this context cannot be compacted."""

        raise NotImplementedError
