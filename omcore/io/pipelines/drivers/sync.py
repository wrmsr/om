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
from .types import IoPipelineDriverState


log = get_module_logger(globals())  # noqa


##


class SyncSocketIoPipelineDriver:
    """
    Drive a pipeline over a caller-owned socket.

    The socket must be used exclusively through the driver while it is active. The driver temporarily makes sockets
    nonblocking so reads, queued writes, and timers can share one readiness wait, then restores the original timeout
    when the pipeline closes or fails.
    """

    @dc.dataclass(frozen=True)
    class Config:
        DEFAULT: ta.ClassVar['SyncSocketIoPipelineDriver.Config']

        read_chunk_size: int = 64 * 1024
        write_chunk_max: ta.Optional[int] = None

        strict_input_flow: bool = False

        write_high_watermark: int = 64 * 1024
        write_low_watermark: int = 16 * 1024

        def __post_init__(self) -> None:
            """Validate I/O chunk sizes and output writability watermarks."""

            if self.read_chunk_size < 1:
                raise ValueError(self.read_chunk_size)
            if self.write_chunk_max is not None and self.write_chunk_max < 1:
                raise ValueError(self.write_chunk_max)
            if not (0 <= self.write_low_watermark <= self.write_high_watermark):
                raise ValueError((self.write_low_watermark, self.write_high_watermark))

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

        self._write_q: ta.Deque[memoryview] = collections.deque()
        self._write_q_bytes = 0
        self._output_writable = True

        self._socket_mode_prepared = False
        self._socket_mode_changed = False
        self._socket_original_timeout: ta.Optional[float] = None

        self._saw_transport_final_output = False

        self._state = IoPipelineDriverState.NEW

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def config(self) -> Config:
        return self._config

    @property
    def state(self) -> IoPipelineDriverState:
        return self._state

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

        check.state(self._state is IoPipelineDriverState.NEW)

        try:
            self._prepare_socket_mode()

            self._sched = self._SchedulingService(self)

            self._pipeline = pipeline = self._make_pipeline()

            self._flow = flow = pipeline.services.find(IoPipelineFlow)
            if flow is None:
                self._want_read = True

        except BaseException:
            self._state = IoPipelineDriverState.FAILED
            self._restore_socket_mode()
            raise

        self._state = IoPipelineDriverState.RUNNING

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
        return (
            self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING) and
            (pipeline := self._opt_pipeline()) is not None and
            pipeline.is_ready
        )

    #

    def _prepare_socket_mode(self) -> None:
        if self._socket_mode_prepared:
            return
        self._socket_mode_prepared = True

        try:
            gettimeout = self._sock.gettimeout
            setblocking = self._sock.setblocking
            _ = self._sock.settimeout
        except AttributeError:
            return

        self._socket_original_timeout = gettimeout()
        setblocking(False)
        self._socket_mode_changed = True

    def _restore_socket_mode(self) -> None:
        if not self._socket_mode_changed:
            return
        self._socket_mode_changed = False

        try:
            self._sock.settimeout(self._socket_original_timeout)
        except OSError:
            pass

    def _get_socket_timeout(self) -> ta.Optional[float]:
        if self._socket_mode_changed:
            return self._socket_original_timeout

        try:
            return self._sock.gettimeout()
        except AttributeError:
            return None

    #

    def close(self) -> None:
        """Abort the pipeline, discard queued output, and restore the caller-owned socket's original mode."""

        if self._state is IoPipelineDriverState.CLOSED:
            return

        failed = self._state is IoPipelineDriverState.FAILED
        try:
            if (pipeline := self._opt_pipeline()) is not None and pipeline.is_ready:
                pipeline.destroy()
        except BaseException:
            self._state = IoPipelineDriverState.FAILED
            raise
        else:
            self._state = IoPipelineDriverState.FAILED if failed else IoPipelineDriverState.CLOSED
        finally:
            self._write_q.clear()
            self._write_q_bytes = 0
            self._restore_socket_mode()

    def _fail(self) -> None:
        self._state = IoPipelineDriverState.FAILED
        self._write_q.clear()
        self._write_q_bytes = 0
        try:
            if (pipeline := self._opt_pipeline()) is not None and pipeline.is_ready:
                pipeline.destroy()
        finally:
            self._restore_socket_mode()

    def __enter__(self) -> 'SyncSocketIoPipelineDriver':  # noqa
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    #

    _want_read: bool = False

    def _do_read(self) -> ta.List[ta.Any]:
        out: ta.List[ta.Any] = []

        try:
            b = self._sock.recv(self._config.read_chunk_size)
        except BlockingIOError:
            return out
        except OSError:
            self._fail()
            raise

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

    def _enqueue_write(self, msg: ta.Any) -> None:
        for mv in ByteStreamBuffers.iter_segments(msg):
            if mv:
                self._write_q.append(mv)
                self._write_q_bytes += len(mv)

        self._update_output_writability()

    def _try_write(self) -> bool:
        if not self._write_q:
            return False

        mv = self._write_q[0]
        if (wcm := self._config.write_chunk_max) is not None and len(mv) > wcm:
            write_mv = mv[:wcm]
        else:
            write_mv = mv

        try:
            n = self._sock.send(write_mv)
        except BlockingIOError:
            return False
        except OSError:
            self._fail()
            raise

        if n < 1:
            error = BrokenPipeError('socket send returned no progress')
            self._fail()
            raise error

        self._write_q_bytes -= n
        if n == len(mv):
            self._write_q.popleft()
        else:
            self._write_q[0] = mv[n:]

        self._update_output_writability()
        return True

    def _update_output_writability(self) -> None:
        if self._flow is None or self._state is not IoPipelineDriverState.RUNNING:
            return

        if self._output_writable:
            if self._write_q_bytes > self._config.write_high_watermark:
                self._output_writable = False
                self._pipeline.feed_in(IoPipelineFlowMessages.PauseOutput())

        elif self._write_q_bytes <= self._config.write_low_watermark:
            self._output_writable = True
            self._pipeline.feed_in(IoPipelineFlowMessages.ReadyForOutput())

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

    def _wait_for_io_or_timer(
            self,
            *,
            want_read: bool,
            want_write: bool,
    ) -> ta.Tuple[bool, bool, bool]:
        while True:
            timer_delay = self._sched.next_delay()

            socket_timeout: ta.Optional[float] = None
            if want_read or want_write:
                socket_timeout = self._get_socket_timeout()
            else:
                check.not_none(timer_delay)

            if timer_delay is None:
                if socket_timeout is None:
                    check.state(want_read or want_write)
                    timeout = None
                else:
                    timeout = socket_timeout
            elif socket_timeout is None:
                timeout = timer_delay
            else:
                timeout = min(timer_delay, socket_timeout)

            try:
                readable, writable, _ = select.select(
                    [self._sock] if want_read else [],
                    [self._sock] if want_write else [],
                    [],
                    timeout,
                )
            except (OSError, ValueError):
                self._fail()
                raise

            try:
                ran_timer = bool(self._sched._run_due())  # noqa
            except BaseException:
                self._fail()
                raise
            if readable or writable or ran_timer:
                return (bool(readable), bool(writable), ran_timer)

            if socket_timeout == 0.:
                return (False, False, False)

            if (
                    socket_timeout is not None and
                    (timer_delay is None or socket_timeout <= timer_delay)
            ):
                raise TimeoutError('timed out')

    #

    def _handle_output(self, msg: ta.Any) -> ta.Literal['handled', 'unhandled']:
        if ByteStreamBuffers.can_bytes(msg):
            self._enqueue_write(msg)
            return 'handled'

        elif isinstance(msg, IoPipelineFlowMessages.FlushOutput):
            # self._sock.flush()
            return 'handled'

        elif isinstance(msg, IoPipelineMessages.FinalOutput):
            self._saw_transport_final_output = True
            self._state = IoPipelineDriverState.DRAINING
            return 'handled'

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
        ta.Literal['read', 'write', 'stop'],
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

                else:
                    raise RuntimeError(f'Unknown handled value: {handled!r}')

            if self._saw_transport_final_output:
                return 'write' if self._write_q else 'stop'

            if self._input_q:
                pipeline.feed_in(self._input_q.popleft())
                continue

            if self._write_q:
                return 'write'

            if not pipeline.saw_final_input and self._want_read:
                return 'read'

            return None

    def next(
            self,
            *,
            read: bool = True,
            raise_on_stall: bool = True,
    ) -> ta.Optional[ta.Any]:
        """
        Advance until an unhandled output or no work remains.

        When read is false, process only immediately available work without waiting for transport input or future
        timers. In this mode, raise_on_stall is ignored.
        """

        pipeline = self._ensure_pipeline()  # noqa
        check.state(pipeline.is_ready)

        try:
            ran_timer = bool(self._sched._run_due())  # noqa
        except BaseException:
            self._fail()
            raise

        while True:
            try:
                out = self._poll()
            except BaseException:
                self._fail()
                raise

            if isinstance(out, tuple):
                ok, ov = out
                if ok == 'unhandled':
                    return ov

                else:
                    raise RuntimeError(f'Unknown output: {ok!r}')

            elif out == 'stop':
                try:
                    pipeline.destroy()
                except BaseException:
                    self._state = IoPipelineDriverState.FAILED
                    raise
                else:
                    self._state = IoPipelineDriverState.CLOSED
                finally:
                    self._restore_socket_mode()

                return None

            elif out not in ('read', 'write', None):
                raise RuntimeError(f'Unknown output: {out!r}')

            if ran_timer:
                return None

            want_read = not pipeline.saw_final_input and self._want_read
            want_write = bool(self._write_q)

            if not read:
                while self._write_q and self._try_write():
                    pass
                if self._saw_transport_final_output and not self._write_q:
                    continue
                return None

            if not (want_read or want_write) and self._sched.next_delay() is None:
                if raise_on_stall:
                    raise RuntimeError('Pipeline stalled')
                return None

            readable, writable, ran_timer = self._wait_for_io_or_timer(
                want_read=want_read,
                want_write=want_write,
            )

            progressed = False
            if writable:
                progressed |= self._try_write()
            if readable:
                self._input_q.extend(self._do_read())
                progressed = True

            if not (progressed or ran_timer):
                return None

    def loop_until_done(self) -> None:
        try:
            while True:
                if (out := self.next()) is not None:
                    raise TypeError(out)

                if not self._pipeline.is_ready:
                    break

        finally:
            self.close()
