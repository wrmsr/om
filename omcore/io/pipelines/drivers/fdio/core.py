# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The pipeline-driving core shared by the fdio handler forms.

The core owns the pipeline, its boundary and write queues, watermarks, fences, timers, and the driver state, and
performs I/O through an `IoPipelineFdioTransport`. The handler forms - a socket, a single duplex descriptor, or a read
descriptor and a write descriptor registered as two handlers - expose its readiness and deliver the manager's events
to it. Nothing in the core is an `FdioHandler`.
"""
import abc
import collections
import dataclasses as dc
import time
import typing as ta

from .....lite.abstract import Abstract
from .....lite.check import check
from ....streambufs.segmented import SegmentedByteStreamBuffer
from ....streambufs.types import BytesLike
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineMessages
from ...errors import AbortedIoPipelineError
from ...errors import UnsupportedIoPipelineError
from ...flow.types import IoPipelineFlow
from ...flow.types import IoPipelineFlowMessages
from ...posting.types import ClosedIoPipelinePostingError
from ...posting.types import IoPipelinePost
from ...posting.types import IoPipelinePostingTarget
from ...posting.types import TargetIoPipelinePostingService
from ...posting.types import fail_io_pipeline_posts
from ...sched.heap import HeapIoPipelineSchedulingService
from ..metadata import DriverIoPipelineMetadata
from ..types import IoPipelineDriverState


##


class IoPipelineFdioTransport(Abstract):
    """
    The descriptor operations a driving core performs, supplied by a handler form. Descriptors are nonblocking while
    the transport is in use.
    """

    @abc.abstractmethod
    def read_into(self, buf: memoryview) -> int:
        """Reads up to len(buf) bytes, returning 0 at EOF. Raises BlockingIOError when nothing is available."""

        raise NotImplementedError

    @abc.abstractmethod
    def write(self, data: BytesLike) -> int:
        """Writes some of data, returning the number of bytes accepted. Raises BlockingIOError when none can be."""

        raise NotImplementedError

    def shutdown_output(self) -> None:
        """
        Shuts down the transport's output half, leaving its input readable. Called at most once, after all queued
        output has been written. Raises UnsupportedIoPipelineError if the transport cannot half-close, in which case it
        must be left intact; any other exception fails the driver.
        """

        raise UnsupportedIoPipelineError(f'{type(self).__name__} does not support output shutdown')

    @abc.abstractmethod
    def close(self) -> None:
        """Releases the transport: owned descriptors are closed, caller-owned ones restored. Idempotent."""

        raise NotImplementedError


##


class IoPipelineFdioDriver(IoPipelinePostingTarget):
    """
    Drives a pipeline over a transport registered, through a handler form, with an `FdioManager`.

    ShutdownOutput is queued behind the bytes preceding it, then performed by the transport; reading continues
    afterwards. FinalOutput still drains and closes the transport. Enqueued messages and posted work share one boundary
    queue, processed in order; while it is not empty the driver reports a deadline already due, so the manager
    dispatches it in its current poll iteration, or its next one without waiting, with no descriptor event or timer
    involved.
    """

    @dc.dataclass(frozen=True)
    class Config:
        DEFAULT: ta.ClassVar['IoPipelineFdioDriver.Config']

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
            transport: IoPipelineFdioTransport,
            spec: IoPipeline.Spec,
            config: ta.Optional[Config] = None,
    ) -> None:
        super().__init__()

        self._transport = transport
        self._spec = spec
        if config is None:
            config = self.Config.DEFAULT
        self._config = config

        self._input_q: collections.deque[ta.Any] = collections.deque()
        self._input_q.append(IoPipelineMessages.InitialInput())

        self._write_q: collections.deque[ta.Union[
            BytesLike,
            IoPipelineFlowMessages.FlushOutput,
            IoPipelineMessages.ShutdownOutput,
        ]] = collections.deque()
        self._write_q_bytes = 0
        self._output_writable = True
        self._output_shutdown = False
        self._drain_input_ended = False
        self._transport_closed = False

        self._transport_final_output: ta.Optional[IoPipelineMessages.FinalOutput] = None
        self._pending_read_error: ta.Optional[OSError] = None

        # Usable before the pipeline exists: a post made then runs once it does.
        self._posting = TargetIoPipelinePostingService(self)

    _state: IoPipelineDriverState = IoPipelineDriverState.NEW

    _pipeline: IoPipeline

    _flow: ta.Optional[IoPipelineFlow]

    _want_read: bool = False

    _sched: HeapIoPipelineSchedulingService

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._state.name}>'

    @property
    def config(self) -> Config:
        return self._config

    @property
    def transport(self) -> IoPipelineFdioTransport:
        return self._transport

    @property
    def pipeline(self) -> IoPipeline:
        return self._pipeline

    @property
    def posting(self) -> TargetIoPipelinePostingService:
        """The pipeline's posting service, usable from construction on."""

        return self._posting

    #

    ACTIVE_STATES: ta.ClassVar[ta.Tuple[IoPipelineDriverState, ...]] = (
        IoPipelineDriverState.RUNNING,
        IoPipelineDriverState.DRAINING,
    )

    @property
    def state(self) -> IoPipelineDriverState:
        return self._state

    @property
    def is_active(self) -> bool:
        return self._state in self.ACTIVE_STATES

    @property
    def closed(self) -> bool:
        return self._state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)

    @property
    def output_shutdown(self) -> bool:
        """Whether a ShutdownOutput has shut down the transport's output half."""

        return self._output_shutdown

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
            self._sched = HeapIoPipelineSchedulingService()

            self._pipeline = pipeline = self._make_pipeline()

            self._flow = flow = pipeline.services.find(IoPipelineFlow)
            self._want_read = IoPipelineFlow.is_auto_read(flow)

            check.state(pipeline.is_ready)

            self._state = IoPipelineDriverState.RUNNING

            return pipeline

        except BaseException:
            self._state = IoPipelineDriverState.FAILED
            self._fail()
            raise

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
                self._posting,
            ],
        ))

    #

    def _close_transport(self) -> None:
        if self._transport_closed:
            return
        self._transport_closed = True
        self._transport.close()

    def _fail_queued_posts(self) -> None:
        """Posts never run are failed, so their submitters are told; the queue is cleared by the caller."""

        if posts := [item for item in self._input_q if isinstance(item, IoPipelinePost)]:
            fail_io_pipeline_posts(posts, AbortedIoPipelineError('Driver closed before the post ran'))

    def close(self) -> None:
        """Abort the driver and discard any queued transport output."""

        if self._state is IoPipelineDriverState.CLOSED:
            return

        if self._state is IoPipelineDriverState.FAILED:
            if not self._transport_closed:
                self._fail()
            return

        if self._state is IoPipelineDriverState.NEW:
            try:
                self._fail_queued_posts()
                self._input_q.clear()
                self._close_transport()
            except BaseException:
                self._state = IoPipelineDriverState.FAILED
                raise
            else:
                self._state = IoPipelineDriverState.CLOSED
            return

        check.state(self._state in self.ACTIVE_STATES)

        try:
            try:
                if (pipeline := self._opt_pipeline()) is not None and pipeline.is_ready:
                    pipeline.destroy()
                self._fail_queued_posts()

            finally:
                self._input_q.clear()
                self._write_q.clear()
                self._write_q_bytes = 0
                self._transport_final_output = None
                self._pending_read_error = None

                self._close_transport()

                self._state = IoPipelineDriverState.CLOSED

        except BaseException:  # noqa
            self._state = IoPipelineDriverState.FAILED
            raise

    def _fail(self) -> None:
        try:
            self._fail_queued_posts()
        except Exception:  # noqa
            pass

        try:
            if (pipeline := self._opt_pipeline()) is not None and pipeline.is_ready:
                pipeline.destroy()

        finally:
            self._input_q.clear()
            self._write_q.clear()
            self._write_q_bytes = 0
            self._transport_final_output = None
            self._pending_read_error = None

            try:
                self._close_transport()
            finally:
                self._state = IoPipelineDriverState.FAILED

    #

    def _complete_transport_final_output(self) -> None:
        msg = check.not_none(self._transport_final_output)
        self._transport_final_output = None
        with self._pipeline.enter():
            if not msg.is_done():
                msg.set_succeeded(None)

    def _gracefully_close(self) -> None:
        pipeline = self._ensure_pipeline()
        check.state(self._state in self.ACTIVE_STATES)
        check.empty(self._write_q)
        check.not_none(self._transport_final_output)

        try:
            self._close_transport()
            self._complete_transport_final_output()
            pipeline.destroy()

        except BaseException:
            try:
                if pipeline.is_ready:
                    pipeline.destroy()
            finally:
                self._state = IoPipelineDriverState.FAILED
            raise

        else:
            self._state = IoPipelineDriverState.CLOSED

        finally:
            self._write_q.clear()
            self._write_q_bytes = 0
            self._transport_final_output = None
            self._pending_read_error = None

    #

    def _do_read(self) -> ta.List[ta.Any]:
        out: ta.List[ta.Any] = []

        buf = SegmentedByteStreamBuffer(chunk_size=self._config.read_chunk_size)
        remaining = self._config.read_batch_max_bytes
        eof = False
        for _ in range(self._config.read_batch_max_reads):
            reserve = buf.reserve(min(self._config.read_chunk_size, remaining))
            try:
                read = self._transport.read_into(reserve)
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

    def _try_send(self, b: BytesLike) -> ta.Optional[int]:
        if (wcm := self._config.write_chunk_max) is not None and len(b) > wcm:
            write_b = b[:wcm]
        else:
            write_b = b

        try:
            sr = self._transport.write(write_b)
        except BlockingIOError:
            return None
        except OSError:
            self._fail()
            raise

        if sr < 1:
            error = BrokenPipeError('transport write returned no progress')
            self._fail()
            raise error

        return sr

    def _complete_shutdown_output(self, msg: IoPipelineMessages.ShutdownOutput) -> None:
        try:
            self._transport.shutdown_output()

        except UnsupportedIoPipelineError as e:
            with self._pipeline.enter():
                if not msg.is_done():
                    msg.set_failed(e)
            return

        except BaseException:
            self._fail()
            raise

        self._output_shutdown = True
        with self._pipeline.enter():
            if not msg.is_done():
                msg.set_succeeded(None)

    def _try_flush_write_q(self) -> None:
        while self._write_q:
            head = self._write_q[0]
            if isinstance(head, IoPipelineFlowMessages.FlushOutput):
                self._write_q.popleft()
                with self._pipeline.enter():
                    if not head.is_done():
                        head.set_succeeded(None)
                continue

            if isinstance(head, IoPipelineMessages.ShutdownOutput):
                self._write_q.popleft()
                self._complete_shutdown_output(head)
                continue

            b = head
            if (sr := self._try_send(b)) is None:
                return

            self._write_q_bytes -= sr
            if sr == len(b):
                self._write_q.popleft()
            else:
                self._write_q[0] = b[sr:]

    def _do_write_or_q(self, bls: ta.Iterable[BytesLike]) -> None:
        queuing = bool(self._write_q)
        for bl in bls:
            if not bl:
                continue
            if queuing:
                self._write_q.append(bl)
                self._write_q_bytes += len(bl)
                continue

            while True:
                if (sr := self._try_send(bl)) is None:
                    queuing = True
                    self._write_q.append(bl)
                    self._write_q_bytes += len(bl)
                    break

                if sr == len(bl):
                    break
                bl = bl[sr:]

    def _update_output_writability(self) -> None:
        if self._flow is None or self._output_shutdown:
            return

        if self._output_writable:
            if self._write_q_bytes > self._config.write_high_watermark:
                self._output_writable = False
                self._pipeline.feed_in(IoPipelineFlowMessages.PauseOutput())

        elif self._write_q_bytes <= self._config.write_low_watermark and not self._pipeline.saw_shutdown_output:
            # Never announced once ShutdownOutput reached the terminal - not just once the transport performed it -
            # since from then on nothing may produce ordinary output.
            self._output_writable = True
            self._pipeline.feed_in(IoPipelineFlowMessages.ReadyForOutput())

    #

    def _handle_output(self, msg: ta.Any) -> ta.Literal['handled', 'unhandled', 'stop']:
        if ByteStreamBuffers.can_bytes(msg):
            self._do_write_or_q(ByteStreamBuffers.iter_segments(msg))
            self._update_output_writability()
            return 'handled'

        elif isinstance(msg, IoPipelineFlowMessages.FlushOutput):
            if self._write_q:
                self._write_q.append(msg)
            else:
                with self._pipeline.enter():
                    if not msg.is_done():
                        msg.set_succeeded(None)
            return 'handled'

        elif isinstance(msg, IoPipelineMessages.ShutdownOutput):
            if self._write_q:
                self._write_q.append(msg)
            else:
                self._complete_shutdown_output(msg)
            return 'handled'

        elif isinstance(msg, IoPipelineMessages.FinalOutput):
            check.none(self._transport_final_output)
            self._transport_final_output = msg
            return 'stop'

        elif isinstance(msg, IoPipelineMessages.Defer):
            # A deferred continuation is a fairness yield: timers due meanwhile run first.
            self._sched.run_due()
            if self._pipeline.is_ready:
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
        """Queues already-decoded inbound messages at the driver boundary; the manager then dispatches the handler."""

        self._input_q.extend(in_msgs)

    def accept_post(self, post: IoPipelinePost) -> None:
        if self.closed:
            raise ClosedIoPipelinePostingError(f'{self!r} is {self._state.name}')
        self._input_q.append(post)

    def _poll(self) -> ta.Union[
        ta.Tuple[ta.Literal['unhandled'], ta.Any],
        ta.Literal['read', 'stop', 'destroyed'],
        None,
    ]:
        pipeline = self._ensure_pipeline()  # noqa

        try:
            self._sched.run_due()
        except BaseException:
            self._fail()
            raise

        while True:
            if not pipeline.is_ready:
                return 'destroyed'

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
                # Boundary input - enqueued messages and posted work - is processed in order, also while draining.
                if isinstance(item := self._input_q.popleft(), IoPipelinePost):
                    item.run(pipeline)
                else:
                    pipeline.feed_in(item)
                continue

            if (read_error := self._pending_read_error) is not None:
                self._pending_read_error = None
                self._fail()
                raise read_error

            if not pipeline.saw_final_input and self._want_read:
                return 'read'

            return None

    def poll(self) -> ta.Union[
        ta.Tuple[ta.Literal['unhandled'], ta.Any],
        ta.Literal['read', 'stop', 'destroyed'],
        None,
    ]:
        try:
            return self._poll()
        except BaseException:
            if self._state is not IoPipelineDriverState.CLOSED:
                self._fail()
            raise

    def next(
            self,
            *,
            read: bool = True,
            raise_on_stall: bool = True,
    ) -> ta.Optional[ta.Any]:
        """
        Advance until an unhandled output or no work remains.

        When read is false, process only immediately available work without reading from the transport. In this mode,
        raise_on_stall is ignored.
        """

        pipeline = self._ensure_pipeline()  # noqa

        while True:
            out = self.poll()

            if isinstance(out, tuple):
                ok, ov = out
                if ok == 'unhandled':
                    return ov

                else:
                    raise RuntimeError(f'Unknown output: {ok!r}')

            elif out == 'destroyed':
                # Destroyed from under the driver - by an application policy in a callback, say: an explicit close.
                self.close()
                return None

            elif out == 'read':
                if read:
                    if not (in_ := self._do_read()):
                        return None

                    self._input_q.extend(in_)

                else:
                    return None

            elif out == 'stop':
                if self._write_q:
                    self._state = IoPipelineDriverState.DRAINING
                else:
                    self._gracefully_close()

                return None

            elif out is None:
                if not read:
                    return None

                if raise_on_stall:
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

    ##
    # readiness, for the handler forms

    def wants_read(self) -> bool:
        if self._state is IoPipelineDriverState.DRAINING:
            # Input has no consumer any more, but is still taken off the transport, so a peer whose own output is
            # blocked on this side reading is not left waiting forever.
            return not self._drain_input_ended
        return (
            self._state is IoPipelineDriverState.RUNNING and
            not self._pipeline.saw_final_input and
            self._want_read
        )

    def wants_write(self) -> bool:
        return self.is_active and bool(self._write_q)

    def next_deadline(self) -> ta.Optional[float]:
        if not self.is_active:
            return None
        deadline = self._sched.next_deadline()
        if self._input_q:
            # Queued boundary input is due at once: the manager then dispatches `on_timeout` without waiting.
            now = time.monotonic()
            return now if deadline is None else min(deadline, now)
        return deadline

    ##
    # events, from the handler forms

    def _discard_input(self) -> None:
        buf = bytearray(self._config.read_chunk_size)
        mv = memoryview(buf)
        for _ in range(self._config.read_batch_max_reads):
            try:
                n = self._transport.read_into(mv)
            except BlockingIOError:
                return
            except OSError:
                self._drain_input_ended = True
                return
            if not n:
                self._drain_input_ended = True
                return

    def on_readable(self) -> None:
        if self._state is IoPipelineDriverState.DRAINING:
            self._discard_input()
            return
        check.none(self.next(raise_on_stall=False))

    def on_writable(self) -> None:
        check.not_empty(self._write_q)

        self._try_flush_write_q()

        if self._state is IoPipelineDriverState.DRAINING and not self._write_q:
            self._gracefully_close()

        elif self._state is IoPipelineDriverState.RUNNING:
            self._update_output_writability()
            check.none(self.next(read=False))

    def on_timeout(self) -> None:
        check.state(self.is_active)
        check.none(self.next(read=False))
