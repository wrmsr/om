# ruff: noqa: UP006 UP007 UP045
# @om-lite
import abc
import typing as ta

from ....lite.abstract import Abstract
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerRef


##


class IoPipelineScheduling(Abstract):
    class Handle(Abstract):
        @abc.abstractmethod
        def cancel(self) -> None:
            """Idempotently cancel the callback if it has not begun running."""

            raise NotImplementedError

    @abc.abstractmethod
    def schedule(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[], None],
    ) -> Handle:
        """
        Schedule a callback owned by an active handler ref.

        The callback must not run after its owning handler ref is invalidated.
        Callers that need the owning context should use schedule_context instead of closing over it.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def schedule_context(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[IoPipelineHandlerContext], None],
    ) -> Handle:
        """
        Schedule a callback receiving its owning handler context.

        Unlike a closure over the context, this lets scheduler implementations retain it non-owningly and avoids a
        reference cycle when the handler retains the returned handle. The callback should likewise avoid closing over
        the handler, context, or handler ref.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def cancel_all(self, handler_ref: ta.Optional[IoPipelineHandlerRef] = None) -> None:
        """Cancel callbacks owned by an exact handler ref, or all callbacks when omitted."""

        raise NotImplementedError
