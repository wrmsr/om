# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
TODO:
 - sanity / upper bound read/write timeouts
"""
import collections
import dataclasses as dc
import heapq
import select
import time
import typing as ta

from ....lite.check import check
from ....logs.modules import get_module_logger
from ...streambufs.utils import ByteStreamBuffers
from ..core import IoPipeline
from ..core import IoPipelineHandlerRef
from ..core import IoPipelineHandlerUpdate
from ..core import IoPipelineMessages
from ..core import IoPipelineService
from ..core import IoPipelineUpdate
from ..flow.types import IoPipelineFlow
from ..flow.types import IoPipelineFlowMessages
from ..sched.types import IoPipelineScheduling
from .metadata import DriverIoPipelineMetadata


log = get_module_logger(globals())  # noqa


##


class SyncSocketIoPipelineDriver:
    @dc.dataclass(frozen=True)
    class Config:
        DEFAULT: ta.ClassVar['SyncSocketIoPipelineDriver.Config']

        read_chunk_size: int = 64 * 1024
        write_chunk_max: ta.Optional[int] = None

        strict_input_flow: bool = False

    Config.DEFAULT = Config()

    #

    def __init__(
            self,
            spec: IoPipeline.Spec,
            sock: ta.Any,
            config: ta.Optional[Config] = None,
    ) -> None:
        super().__init__()

        self._spec = spec
        self._sock = sock
        if config is None:
            config = self.Config.DEFAULT
        self._config = config

        self._input_q: collections.deque[ta.Any] = collections.deque()
        self._input_q.append(IoPipelineMessages.InitialInput())

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def config(self) -> Config:
        return self._config

    @property
    def pipeline(self) -> IoPipeline:
        return self._pipeline

    #

    _pipeline: IoPipeline

    _flow: ta.Optional[IoPipelineFlow]

    def _opt_pipeline(self) -> ta.Optional[IoPipeline]:
        try:
            return self._pipeline
        except AttributeError:
            return None

    def _ensure_pipeline(self) -> IoPipeline:
        try:
            return self._pipeline
        except AttributeError:
            pass

        self._sched = self._SchedulingService(self)

        self._pipeline = pipeline = self._make_pipeline()

        self._flow = flow = pipeline.services.find(IoPipelineFlow)
        if flow is None:
            self._want_read = True

        return pipeline

    def _make_pipeline(self) -> IoPipeline:
        return IoPipeline(dc.replace(
            self._spec,

            metadata=[
                *self._spec.metadata,
                DriverIoPipelineMetadata(self),
            ],

            services=[
                *self._spec.services,
                self._sched,
            ],
        ))

    @property
    def is_running(self) -> bool:
        if (pipeline := self._opt_pipeline()) is None:
            return False
        return pipeline.is_ready

    #

    def close(self) -> None:
        if (pipeline := self._opt_pipeline()) is not None:
            pipeline.destroy()

    def __enter__(self) -> 'SyncSocketIoPipelineDriver':  # noqa
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    #

    _want_read: bool = False

    def _do_read(self) -> ta.List[ta.Any]:
        out: ta.List[ta.Any] = []

        b = self._sock.recv(self._config.read_chunk_size)

        if not b:
            out.append(IoPipelineMessages.FinalInput())
        else:
            out.append(b)
            if self._flow is not None:
                out.append(IoPipelineFlowMessages.FlushInput())

        if self._flow is not None:
            self._want_read = False

        return out

    #

    class _SchedulingService(IoPipelineScheduling, IoPipelineService):
        def __init__(self, d: 'SyncSocketIoPipelineDriver') -> None:
            super().__init__()

            self._d = d

            self._pipeline: ta.Optional[IoPipeline] = None

            self._seq = 0
            self._pending: ta.List[ta.Tuple[float, int, SyncSocketIoPipelineDriver._SchedulingService._Handle]] = []
            self._live: ta.Set[SyncSocketIoPipelineDriver._SchedulingService._Handle] = set()

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

        def next_delay(self) -> ta.Optional[float]:
            self._clear_cancelled()
            if not self._pending:
                return None
            return max(0., self._pending[0][0] - time.monotonic())

        def _run_due(self) -> int:
            self._clear_cancelled()

            now = time.monotonic()
            due: ta.List[SyncSocketIoPipelineDriver._SchedulingService._Handle] = []

            while self._pending and self._pending[0][0] <= now:
                _, _, h = heapq.heappop(self._pending)
                if not h._cancelled:  # noqa
                    due.append(h)
                self._clear_cancelled()

            ran = 0
            for i, h in enumerate(due):
                if h._cancelled:  # noqa
                    continue

                h._done = True  # noqa
                self._live.remove(h)

                try:
                    with self._d.pipeline.enter():
                        h._fn()  # noqa

                except BaseException:
                    for rh in due[i + 1:]:
                        if not rh._cancelled:  # noqa
                            heapq.heappush(self._pending, (rh._deadline, rh._seq, rh))  # noqa
                    raise

                ran += 1

            return ran

        @ta.final
        class _Handle(IoPipelineScheduling.Handle):
            def __init__(
                    self,
                    sched: 'SyncSocketIoPipelineDriver._SchedulingService',
                    handler_ref: IoPipelineHandlerRef,
                    fn: ta.Callable[[], None],
                    deadline: float,
                    seq: int,
            ) -> None:
                self._sched = sched
                self._deadline = deadline
                self._seq = seq
                self._handler_ref = handler_ref
                self._fn = fn

                self._cancelled = False
                self._done = False

            def cancel(self) -> None:
                if self._cancelled or self._done:
                    return

                self._cancelled = True
                self._sched._live.remove(self)  # noqa

        def schedule(
                self,
                handler_ref: IoPipelineHandlerRef,
                delay_s: float,
                fn: ta.Callable[[], None],
        ) -> IoPipelineScheduling.Handle:
            pipeline = check.not_none(self._pipeline)
            check.is_(handler_ref.pipeline, pipeline)
            check.state(pipeline.is_ready)
            check.state(not handler_ref.invalidated)

            h = self._Handle(
                self,
                handler_ref,
                fn,
                time.monotonic() + max(0., delay_s),
                self._seq,
            )
            self._seq += 1
            heapq.heappush(self._pending, (h._deadline, h._seq, h))  # noqa
            self._live.add(h)
            return h

        def cancel_all(self, handler_ref: ta.Optional[IoPipelineHandlerRef] = None) -> None:
            for h in tuple(self._live):
                if handler_ref is None or h._handler_ref is handler_ref:  # noqa
                    h.cancel()

            self._pending = [e for e in self._pending if not e[2]._cancelled]  # noqa
            heapq.heapify(self._pending)

    _sched: _SchedulingService

    #

    def _wait_for_read_or_timer(
            self,
            *,
            want_read: bool,
    ) -> ta.Literal['read', 'timer']:
        while True:
            timer_delay = self._sched.next_delay()

            socket_timeout: ta.Optional[float] = None
            if want_read:
                try:
                    socket_timeout = self._sock.gettimeout()
                except AttributeError:
                    pass

                if socket_timeout == 0.:
                    return 'read'
            else:
                check.not_none(timer_delay)

            if timer_delay is None:
                if socket_timeout is None:
                    check.state(want_read)
                    return 'read'
                timeout = socket_timeout
            elif socket_timeout is None:
                timeout = timer_delay
            else:
                timeout = min(timer_delay, socket_timeout)

            readable, _, _ = select.select(
                [self._sock] if want_read else [],
                [],
                [],
                timeout,
            )
            if readable:
                return 'read'

            if self._sched._run_due():  # noqa
                return 'timer'

            if (
                    socket_timeout is not None and
                    (timer_delay is None or socket_timeout <= timer_delay)
            ):
                raise TimeoutError('timed out')

    #

    def _handle_output(self, msg: ta.Any) -> ta.Literal['handled', 'unhandled', 'stop']:
        if ByteStreamBuffers.can_bytes(msg):
            for mv in ByteStreamBuffers.iter_segments(msg):
                self._sock.sendall(mv)
            return 'handled'

        elif isinstance(msg, IoPipelineFlowMessages.FlushOutput):
            # self._sock.flush()
            return 'handled'

        elif isinstance(msg, IoPipelineMessages.FinalOutput):
            return 'stop'

        elif isinstance(msg, IoPipelineMessages.Defer):
            self._pipeline.run_deferred(msg)
            return 'handled'

        elif isinstance(msg, IoPipelineFlowMessages.ReadyForInput):
            check.state(self._flow is not None)
            if self._config.strict_input_flow:
                check.state(not self._want_read)
            self._want_read = True
            return 'handled'

        else:
            return 'unhandled'

    #

    def enqueue(self, *in_msgs: ta.Any) -> None:
        self._input_q.extend(in_msgs)

    def _poll(self) -> ta.Union[
        ta.Tuple[ta.Literal['unhandled'], ta.Any],
        ta.Literal['read', 'stop'],
        None,
    ]:
        pipeline = self._ensure_pipeline()  # noqa
        check.state(pipeline.is_ready)

        while True:
            if (out_msg := pipeline.output.poll()) is not None:
                handled = self._handle_output(out_msg)

                if handled == 'handled':
                    continue

                elif handled == 'unhandled':
                    return ('unhandled', out_msg)

                elif handled == 'stop':
                    return 'stop'

                else:
                    raise RuntimeError(f'Unknown handled value: {handled!r}')

            if self._input_q:
                pipeline.feed_in(self._input_q.popleft())
                continue

            if not pipeline.saw_final_input and self._want_read:
                return 'read'

            return None

    def next(
            self,
            *,
            read: bool = True,
            raise_on_stall: bool = True,
    ) -> ta.Optional[ta.Any]:
        pipeline = self._ensure_pipeline()  # noqa
        check.state(pipeline.is_ready)

        ran_timer = bool(self._sched._run_due())  # noqa

        while True:
            out = self._poll()

            if isinstance(out, tuple):
                ok, ov = out
                if ok == 'unhandled':
                    return ov

                else:
                    raise RuntimeError(f'Unknown output: {ok!r}')

            elif out == 'read':
                if read:
                    if ran_timer:
                        return None

                    if self._wait_for_read_or_timer(want_read=True) == 'read':
                        self._input_q.extend(self._do_read())
                    else:
                        ran_timer = True

                else:
                    return None

            elif out == 'stop':
                pipeline.destroy()

                return None

            elif out is None:
                if ran_timer:
                    return None

                if read and self._sched.next_delay() is not None:
                    check.equal(self._wait_for_read_or_timer(want_read=False), 'timer')
                    ran_timer = True

                elif raise_on_stall:
                    raise RuntimeError('Pipeline stalled')

                else:
                    return None

            else:
                raise RuntimeError(f'Unknown output: {out!r}')

        raise RuntimeError('unreachable')  # noqa

    def loop_until_done(self) -> None:
        try:
            while True:
                if (out := self.next()) is not None:
                    raise TypeError(out)

                if not self._pipeline.is_ready:
                    break

        finally:
            self.close()
