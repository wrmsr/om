# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import abc
import collections
import dataclasses as dc
import fcntl
import os
import select
import typing as ta

from ....lite.abstract import Abstract
from ....lite.check import check
from ....logs.modules import get_module_logger
from ...streambufs.segmented import SegmentedByteStreamBuffer
from ...streambufs.utils import ByteStreamBuffers
from ..core import IoPipeline
from ..core import IoPipelineMessages
from ..flow.types import IoPipelineFlow
from ..flow.types import IoPipelineFlowMessages
from ..sched.heap import HeapIoPipelineSchedulingService
from .metadata import DriverIoPipelineMetadata
from .types import IoPipelineDriverState


SyncIoPipelineDriverT = ta.TypeVar('SyncIoPipelineDriverT', bound='SyncIoPipelineDriver')


log = get_module_logger(globals())  # noqa


##


class SyncIoPipelineDriver(Abstract):
    """
    Drive a pipeline over a caller-owned synchronous transport, blocking the calling thread.

    The transport must be used exclusively through the driver while it is active. Subclasses supply the handful of
    transport operations - nonblocking reads and writes, the file descriptors to wait on, and switching the transport
    into and out of nonblocking mode - and everything else (pipeline stepping, queued writes, watermarks, timers, the
    readiness wait) is shared.
    """

    @dc.dataclass(frozen=True)
    class Config:
        DEFAULT: ta.ClassVar['SyncIoPipelineDriver.Config']

        read_chunk_size: int = 64 * 1024
        read_batch_max_bytes: int = 1024 * 1024
        read_batch_max_reads: int = 16
        write_chunk_max: ta.Optional[int] = None

        strict_input_flow: bool = False

        write_high_watermark: int = 64 * 1024
        write_low_watermark: int = 16 * 1024

        def __post_init__(self) -> None:
            """Validate I/O chunk sizes and output writability watermarks."""

            if self.read_chunk_size < 1:
                raise ValueError(self.read_chunk_size)
            if self.read_batch_max_bytes < 1:
                raise ValueError(self.read_batch_max_bytes)
            if self.read_batch_max_reads < 1:
                raise ValueError(self.read_batch_max_reads)
            if self.write_chunk_max is not None and self.write_chunk_max < 1:
                raise ValueError(self.write_chunk_max)
            if not (0 <= self.write_low_watermark <= self.write_high_watermark):
                raise ValueError((self.write_low_watermark, self.write_high_watermark))

    Config.DEFAULT = Config()

    #

    def __init__(
            self,
            spec: IoPipeline.Spec,
            config: ta.Optional[Config] = None,
    ) -> None:
        super().__init__()

        self._spec = spec
        if config is None:
            config = self.Config.DEFAULT
        self._config = config

        self._input_q: collections.deque[ta.Any] = collections.deque()
        self._input_q.append(IoPipelineMessages.InitialInput())

        self._write_q: ta.Deque[ta.Union[memoryview, IoPipelineFlowMessages.FlushOutput]] = collections.deque()
        self._write_q_bytes = 0
        self._output_writable = True

        self._transport_prepared = False
        self._wait_timeout_s: ta.Optional[float] = None

        self._transport_final_output: ta.Optional[IoPipelineMessages.FinalOutput] = None
        self._pending_read_error: ta.Optional[OSError] = None

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

    @property
    def wait_timeout_s(self) -> ta.Optional[float]:
        return self._wait_timeout_s

    @wait_timeout_s.setter
    def wait_timeout_s(self, timeout_s: ta.Optional[float]) -> None:
        """
        An additional bound on each readiness wait, on top of the transport's own timeout. Lets a host which must not
        block forever - say, while closing against a peer which has stopped reading - get a TimeoutError back from
        `next` and decide what to do. May be changed at any time between calls.
        """

        if timeout_s is not None and timeout_s < 0.:
            raise ValueError(timeout_s)
        self._wait_timeout_s = timeout_s

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
            self._prepare_transport_once()

            self._sched = HeapIoPipelineSchedulingService()

            self._pipeline = pipeline = self._make_pipeline()

            self._flow = flow = pipeline.services.find(IoPipelineFlow)
            self._want_read = IoPipelineFlow.is_auto_read(flow)

        except BaseException:
            self._state = IoPipelineDriverState.FAILED
            self._restore_transport_if_prepared()
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

    ##
    # transport

    @abc.abstractmethod
    def _prepare_transport(self) -> None:
        """Switch the transport to nonblocking mode. Called once before the pipeline is created."""

        raise NotImplementedError

    @abc.abstractmethod
    def _restore_transport(self) -> None:
        """Undo _prepare_transport. Called on close or failure, possibly more than once."""

        raise NotImplementedError

    @abc.abstractmethod
    def _transport_timeout(self) -> ta.Optional[float]:
        """
        The transport's own I/O timeout, bounding each readiness wait: None blocks indefinitely, zero never blocks, and
        exceeding a positive value raises TimeoutError. A socket reports the timeout it had before being made
        nonblocking.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def _read_fileno(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def _write_fileno(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def _read_into(self, buf: memoryview) -> int:
        """Read up to len(buf) bytes, returning 0 at EOF. Raises BlockingIOError when nothing is available."""

        raise NotImplementedError

    @abc.abstractmethod
    def _write(self, data: memoryview) -> int:
        """Write some of data, returning the number of bytes accepted. Raises BlockingIOError when none can be."""

        raise NotImplementedError

    #

    def _prepare_transport_once(self) -> None:
        if self._transport_prepared:
            return
        self._transport_prepared = True
        self._prepare_transport()

    def _restore_transport_if_prepared(self) -> None:
        if not self._transport_prepared:
            return
        self._transport_prepared = False
        self._restore_transport()

    #

    def close(self) -> None:
        """Abort the pipeline, discard queued output, and restore the caller-owned transport's original mode."""

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
            self._pending_read_error = None
            self._restore_transport_if_prepared()

    def _fail(self) -> None:
        self._state = IoPipelineDriverState.FAILED
        self._write_q.clear()
        self._write_q_bytes = 0
        self._pending_read_error = None
        try:
            if (pipeline := self._opt_pipeline()) is not None and pipeline.is_ready:
                pipeline.destroy()
        finally:
            self._transport_final_output = None
            self._restore_transport_if_prepared()

    def __enter__(self: SyncIoPipelineDriverT) -> SyncIoPipelineDriverT:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    #

    def _do_read(self) -> ta.List[ta.Any]:
        out: ta.List[ta.Any] = []

        buf = SegmentedByteStreamBuffer(chunk_size=self._config.read_chunk_size)
        remaining = self._config.read_batch_max_bytes
        eof = False
        for _ in range(self._config.read_batch_max_reads):
            reserve = buf.reserve(min(self._config.read_chunk_size, remaining))
            try:
                read = self._read_into(reserve)
            except BlockingIOError:
                reserve.release()
                buf.commit(0)
                break
            except OSError as exc:
                reserve.release()
                buf.commit(0)
                if not len(buf):
                    self._fail()
                    raise
                self._pending_read_error = exc
                break
            except BaseException:
                reserve.release()
                buf.commit(0)
                raise
            else:
                reserve.release()
                buf.commit(read)

            if not read:
                eof = True
                break

            remaining -= read
            if remaining < 1:
                break

        if len(buf):
            out.append(buf)

        if len(buf) and self._flow is not None:
            out.append(IoPipelineFlowMessages.FlushInput())
            self._want_read = self._flow.is_auto_read()

        if eof:
            out.append(IoPipelineMessages.FinalInput())
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
            n = self._write(write_mv)
        except BlockingIOError:
            return False
        except OSError:
            self._fail()
            raise

        if n < 1:
            error = BrokenPipeError('transport write returned no progress')
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
                socket_timeout = self._transport_timeout()
                if (wt := self._wait_timeout_s) is not None:
                    socket_timeout = wt if socket_timeout is None else min(socket_timeout, wt)
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
                    [self._read_fileno()] if want_read else [],
                    [self._write_fileno()] if want_write else [],
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

            if (read_error := self._pending_read_error) is not None:
                self._pending_read_error = None
                self._fail()
                raise read_error

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
                    self._restore_transport_if_prepared()
                    self._complete_transport_final_output()
                    pipeline.destroy()
                except BaseException:
                    self._state = IoPipelineDriverState.FAILED
                    raise
                else:
                    self._state = IoPipelineDriverState.CLOSED
                finally:
                    self._restore_transport_if_prepared()

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


##


class SocketSyncIoPipelineDriver(SyncIoPipelineDriver):
    """
    Drive a pipeline over a caller-owned socket.

    The driver temporarily makes the socket nonblocking so reads, queued writes, and timers can share one readiness
    wait, then restores the original timeout when the pipeline closes or fails. The socket's original timeout, if any,
    bounds each wait.
    """

    def __init__(
            self,
            spec: IoPipeline.Spec,
            sock: ta.Any,
            config: ta.Optional[SyncIoPipelineDriver.Config] = None,
    ) -> None:
        super().__init__(spec, config)

        self._sock = sock

        self._socket_mode_changed = False
        self._socket_original_timeout: ta.Optional[float] = None

    @property
    def socket(self) -> ta.Any:
        return self._sock

    def _prepare_transport(self) -> None:
        try:
            gettimeout = self._sock.gettimeout
            setblocking = self._sock.setblocking
            _ = self._sock.settimeout
        except AttributeError:
            return

        self._socket_original_timeout = gettimeout()
        setblocking(False)
        self._socket_mode_changed = True

    def _restore_transport(self) -> None:
        if not self._socket_mode_changed:
            return
        self._socket_mode_changed = False

        try:
            self._sock.settimeout(self._socket_original_timeout)
        except OSError:
            pass

    def _transport_timeout(self) -> ta.Optional[float]:
        if self._socket_mode_changed:
            return self._socket_original_timeout

        try:
            return self._sock.gettimeout()
        except AttributeError:
            return None

    def _read_fileno(self) -> int:
        return self._sock.fileno()

    def _write_fileno(self) -> int:
        return self._sock.fileno()

    def _read_into(self, buf: memoryview) -> int:
        return self._sock.recv_into(buf)

    def _write(self, data: memoryview) -> int:
        return self._sock.send(data)


# Deprecated spelling, retained for code not yet migrated.
SyncSocketIoPipelineDriver = SocketSyncIoPipelineDriver


##


class FdSyncIoPipelineDriver(SyncIoPipelineDriver):
    """
    Drive a pipeline over a pair of caller-owned file descriptors, such as a pipe pair or a process's own stdio.

    Both descriptors are switched to nonblocking mode while the driver is active and restored afterwards. They may be
    the same descriptor. An optional timeout bounds each readiness wait the same way a socket's timeout would.
    """

    def __init__(
            self,
            spec: IoPipeline.Spec,
            read_fd: int,
            write_fd: int,
            config: ta.Optional[SyncIoPipelineDriver.Config] = None,
            *,
            timeout_s: ta.Optional[float] = None,
    ) -> None:
        super().__init__(spec, config)

        self._read_fd = read_fd
        self._write_fd = write_fd
        self._timeout_s = timeout_s

        self._original_flags: ta.Dict[int, int] = {}

    @property
    def read_fd(self) -> int:
        return self._read_fd

    @property
    def write_fd(self) -> int:
        return self._write_fd

    def _prepare_transport(self) -> None:
        for fd in {self._read_fd, self._write_fd}:
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            self._original_flags[fd] = flags
            if not (flags & os.O_NONBLOCK):
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def _restore_transport(self) -> None:
        flags_by_fd = self._original_flags
        self._original_flags = {}
        for fd, flags in flags_by_fd.items():
            try:
                fcntl.fcntl(fd, fcntl.F_SETFL, flags)
            except OSError:
                pass

    def _transport_timeout(self) -> ta.Optional[float]:
        return self._timeout_s

    def _read_fileno(self) -> int:
        return self._read_fd

    def _write_fileno(self) -> int:
        return self._write_fd

    def _read_into(self, buf: memoryview) -> int:
        data = os.read(self._read_fd, len(buf))
        n = len(data)
        buf[:n] = data
        return n

    def _write(self, data: memoryview) -> int:
        return os.write(self._write_fd, data)
