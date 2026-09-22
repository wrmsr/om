import abc
import typing as ta

from omcore import lang

from ... import llm
from ..types.contexts import Context
from ..types.lifecycle import ContextProjection
from ..types.lifecycle import ContextReductionReason


##


class ContextCompactor(lang.Abstract):
    """
    A semantic reducer: replaces a projection with one which says less of the transcript, and so renders to fewer
    tokens. The lifecycle manager reaches for it once deterministic tool-result pruning has not been enough, and on
    request.
    """

    @abc.abstractmethod
    def compact(
            self,
            context: Context,
            *,
            backend: llm.ImmediateBackend,
            target_tokens: int,
            reason: ContextReductionReason,
            instructions: str | None = None,
    ) -> ta.Awaitable[ContextProjection | None]:
        """
        Returns a complete replacement projection, or None when this context cannot be compacted. The backend is the
        run's own, for a compactor which has a model do its work; the target is what the rendered view is to fit in;
        and the instructions, when given, are the user's word on what the reduction is to keep.
        """

        raise NotImplementedError
