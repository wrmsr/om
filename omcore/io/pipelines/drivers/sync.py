# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import collections
import dataclasses as dc
import select
import typing as ta

from ....lite.check import check
from ....logs.modules import get_module_logger
from ...streambufs.utils import ByteStreamBuffers
from ..core import IoPipeline
from ..core import IoPipelineMessages
from ..flow.types import IoPipelineFlow
from ..flow.types import IoPipelineFlowMessages
from ..sched.heap import HeapIoPipelineSchedulingService
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

        self._write_q: ta.Deque[ta.Union[memoryview, IoPipelineFlowMessages.FlushOutput]] = collections.deque()
        self._write_q_bytes = 0
        self._output_writable = True

        self._socket_mode_prepared = False
        self._socket_mode_changed = False
        self._socket_original_timeout: ta.Optional[float] = None

        self._transport_final_output: ta.Optional[IoPipelineMessages.FinalOutput] = None

        self._state = IoPipelineDriverState.NEW

    _pipeline: IoPipeline

    _flow: ta.Optional[IoPipelineFlow]

    _want_read: bool = False

    _sched: HeapIoPipelineSchedulingService

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

            self._sched = HeapIoPipelineSchedulingService()

            self._pipeline = pipeline = self._make_pipeline()

            self._flow = flow = pipeline.services.find(IoPipelineFlow)
            self._want_read = IoPipelineFlow.is_auto_read(flow)

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
            self._transport_final_output = None
            self._restore_socket_mode()

    def _fail(self) -> None:
        self._state = IoPipelineDriverState.FAILED
        self._write_q.clear()
        self._write_q_bytes = 0
        try:
            if (pipeline := self._opt_pipeline()) is not None and pipeline.is_ready:
                pipeline.destroy()
        finally:
            self._transport_final_output = None
            self._restore_socket_mode()

    def __enter__(self) -> 'SyncSocketIoPipelineDriver':  # noqa
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    #

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
            self._want_read = False
        else:
            out.append(b)
            if self._flow is not None:
                out.append(IoPipelineFlowMessages.FlushInput())
                self._want_read = self._flow.is_auto_read()

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

        head = self._write_q[0]
        if isinstance(head, IoPipelineFlowMessages.FlushOutput):
            self._write_q.popleft()
            with self._pipeline.enter():
                if not head.is_done():
                    head.set_succeeded(None)
            return True

        mv = head
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
                ran_timer = bool(self._sched.run_due())
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

    def _complete_transport_final_output(self) -> None:
        msg = check.not_none(self._transport_final_output)
        self._transport_final_output = None
        with self._pipeline.enter():
            if not msg.is_done():
                msg.set_succeeded(None)

    #

    def _handle_output(self, msg: ta.Any) -> ta.Literal['handled', 'unhandled']:
        if ByteStreamBuffers.can_bytes(msg):
            self._enqueue_write(msg)
            return 'handled'

        elif isinstance(msg, IoPipelineFlowMessages.FlushOutput):
            self._write_q.append(msg)
            return 'handled'

        elif isinstance(msg, IoPipelineMessages.FinalOutput):
            check.none(self._transport_final_output)
            self._transport_final_output = msg
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

            if self._write_q and isinstance(self._write_q[0], IoPipelineFlowMessages.FlushOutput):
                self._try_write()
                continue

            if self._transport_final_output is not None:
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
            ran_timer = bool(self._sched.run_due())
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
                    self._restore_socket_mode()
                    self._complete_transport_final_output()
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
                if self._transport_final_output is not None and not self._write_q:
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
