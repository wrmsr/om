# ruff: noqa: UP006 UP007 UP045
# @om-lite
import abc
import typing as ta

from ....lite.abstract import Abstract
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
        """

        raise NotImplementedError

    @abc.abstractmethod
    def cancel_all(self, handler_ref: ta.Optional[IoPipelineHandlerRef] = None) -> None:
        """Cancel callbacks owned by an exact handler ref, or all callbacks when omitted."""

        raise NotImplementedError
