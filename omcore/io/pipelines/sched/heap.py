# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import heapq
import time
import typing as ta
import weakref

from ....lite.check import check
from ..core import IoPipeline
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerRef
from ..core import IoPipelineHandlerUpdate
from ..core import IoPipelineService
from ..core import IoPipelineUpdate
from .types import IoPipelineScheduling


##


@ta.final
class HeapIoPipelineSchedulingService(IoPipelineScheduling, IoPipelineService):
    """
    Tickless heap scheduling for select-, poll-, and generator-style pipeline drivers.

    `next_deadline()` returns an absolute deadline in the configured clock's time base, while `next_delay()` returns
    the corresponding relative delay. The default clock is `time.monotonic()`; deterministic drivers may inject one.
    Drivers call `run_due()` after waiting. Callbacks execute inside their pipeline and are automatically cancelled
    when their owning handler is removed or the pipeline is destroyed.
    """

    def __init__(self, clock: ta.Callable[[], float] = time.monotonic) -> None:
        super().__init__()

        self._clock = clock

        self.__pipeline_ref: ta.Optional[weakref.ReferenceType] = None

        self._seq = 0
        self._pending: ta.List[ta.Tuple[float, int, HeapIoPipelineSchedulingService._Handle]] = []
        self._live: ta.Set[HeapIoPipelineSchedulingService._Handle] = set()

    @property
    def _pipeline(self) -> ta.Optional[IoPipeline]:
        if self.__pipeline_ref is None:
            return None
        return self.__pipeline_ref()

    @_pipeline.setter
    def _pipeline(self, pipeline: ta.Optional[IoPipeline]) -> None:
        self.__pipeline_ref = None if pipeline is None else weakref.ref(pipeline)

    def pipeline_update(self, pipeline: IoPipeline, kind: IoPipelineUpdate) -> None:
        if kind == 'added':
            check.none(self._pipeline)
            self._pipeline = pipeline

        elif kind == 'removed':
            if self._pipeline is None:
                return

            check.is_(pipeline, self._pipeline)
            self.cancel_all()
            self._pipeline = None

    def handler_update(self, handler_ref: IoPipelineHandlerRef, kind: IoPipelineHandlerUpdate) -> None:
        if kind == 'removing':
            self.cancel_all(handler_ref)

    def _clear_cancelled(self) -> None:
        while self._pending and self._pending[0][2]._cancelled:  # noqa
            heapq.heappop(self._pending)

    def next_deadline(self) -> ta.Optional[float]:
        """Return the earliest absolute `time.monotonic()` deadline, or none when no callback is pending."""

        self._clear_cancelled()
        if not self._pending:
            return None
        return self._pending[0][0]

    def next_delay(self) -> ta.Optional[float]:
        """Return the non-negative delay until the earliest callback, or none when no callback is pending."""

        if (deadline := self.next_deadline()) is None:
            return None
        return max(0., deadline - self._clock())

    def run_due(self) -> int:
        """Run the callbacks due at entry and return the number that ran."""

        self._clear_cancelled()

        now = self._clock()
        due: ta.List[HeapIoPipelineSchedulingService._Handle] = []

        while self._pending and self._pending[0][0] <= now:
            _, _, handle = heapq.heappop(self._pending)
            if not handle._cancelled:  # noqa
                due.append(handle)
            self._clear_cancelled()

        ran = 0
        for i, handle in enumerate(due):
            if handle._cancelled:  # noqa
                continue

            handle._done = True  # noqa
            self._live.remove(handle)

            try:
                with check.not_none(self._pipeline).enter():
                    handle._run()  # noqa

            except BaseException:
                for remaining_handle in due[i + 1:]:
                    if not remaining_handle._cancelled:  # noqa
                        heapq.heappush(self._pending, (  # noqa
                            remaining_handle._deadline,  # noqa
                            remaining_handle._seq,  # noqa
                            remaining_handle,
                        ))
                raise

            ran += 1

        return ran

    @ta.final
    class _Handle(IoPipelineScheduling.Handle):
        def __init__(
                self,
                sched: 'HeapIoPipelineSchedulingService',
                handler_ref: IoPipelineHandlerRef,
                fn: ta.Callable[..., None],
                with_context: bool,
                deadline: float,
                seq: int,
        ) -> None:
            self.__sched_ref = weakref.ref(sched)
            self._deadline = deadline
            self._seq = seq
            self.__handler_context_ref = weakref.ref(handler_ref._context)  # noqa
            self._fn = fn
            self._with_context = with_context

            self._cancelled = False
            self._done = False

        @property
        def _handler_context(self) -> IoPipelineHandlerContext:
            return check.not_none(self.__handler_context_ref())

        def _run(self) -> None:
            if self._with_context:
                self._fn(self._handler_context)
            else:
                self._fn()

        def cancel(self) -> None:
            if self._cancelled or self._done:
                return

            self._cancelled = True
            if (sched := self.__sched_ref()) is not None:
                sched._live.discard(self)  # noqa

    def _schedule(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[..., None],
            *,
            with_context: bool,
    ) -> IoPipelineScheduling.Handle:
        pipeline = check.not_none(self._pipeline)
        check.is_(handler_ref.pipeline, pipeline)
        check.state(pipeline.is_ready)
        check.state(not handler_ref.invalidated)

        handle = self._Handle(
            self,
            handler_ref,
            fn,
            with_context,
            self._clock() + max(0., delay_s),
            self._seq,
        )
        self._seq += 1
        heapq.heappush(self._pending, (handle._deadline, handle._seq, handle))  # noqa
        self._live.add(handle)
        return handle

    def schedule(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[], None],
    ) -> IoPipelineScheduling.Handle:
        return self._schedule(handler_ref, delay_s, fn, with_context=False)

    def schedule_context(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[IoPipelineHandlerContext], None],
    ) -> IoPipelineScheduling.Handle:
        return self._schedule(handler_ref, delay_s, fn, with_context=True)

    def cancel_all(self, handler_ref: ta.Optional[IoPipelineHandlerRef] = None) -> None:
        for handle in tuple(self._live):
            if handler_ref is None or handle._handler_context is handler_ref._context:  # noqa
                handle.cancel()

        self._pending = [entry for entry in self._pending if not entry[2]._cancelled]  # noqa
        heapq.heapify(self._pending)
