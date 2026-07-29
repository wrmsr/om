# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import collections
import dataclasses as dc
import math
import typing as ta

from ....lite.check import check
from ...streambufs.utils import ByteStreamBuffers
from ..core import IoPipeline
from ..core import IoPipelineMessages
from ..flow.types import IoPipelineFlow
from ..flow.types import IoPipelineFlowMessages
from ..sched.heap import HeapIoPipelineSchedulingService
from .metadata import DriverIoPipelineMetadata
from .types import IoPipelineDriverState


##


class PureIoPipelineDriver:
    """
    Deterministically drive a pipeline without an operating-system transport or event loop.

    Transport input is supplied with `feed_input()` and consumed by `next(read=True)`. Outbound bytes remain queued
    until `drain_output()` explicitly accepts them across the simulated transport boundary. Consequently flush and
    final-output completion, partial writes, watermarks, and timer races can be exercised without sockets or sleeps.
    Queued bytes-like segments are retained by reference until accepted and must not be mutated or recycled meanwhile.

    The clock starts at zero and advances only through `advance_time()`. With no scheduled callback the driver remains
    tickless; advancing time does not itself run work, so callers retain the same explicit stepping model as `next()`.
    """

    @dc.dataclass(frozen=True)
    class Config:
        DEFAULT: ta.ClassVar['PureIoPipelineDriver.Config']

        read_chunk_size: int = 64 * 1024
        write_chunk_max: ta.Optional[int] = None

        strict_input_flow: bool = False

        write_high_watermark: int = 64 * 1024
        write_low_watermark: int = 16 * 1024

        def __post_init__(self) -> None:
            """Validate simulated chunk sizes and output writability watermarks."""

            if self.read_chunk_size < 1:
                raise ValueError(self.read_chunk_size)
            if self.write_chunk_max is not None and self.write_chunk_max < 1:
                raise ValueError(self.write_chunk_max)
            if not (0 <= self.write_low_watermark <= self.write_high_watermark):
                raise ValueError((self.write_low_watermark, self.write_high_watermark))

    Config.DEFAULT = Config()

    class _Clock:
        def __init__(self) -> None:
            self.now = 0.

        def __call__(self) -> float:
            return self.now

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

        self._input_q: ta.Deque[ta.Any] = collections.deque([IoPipelineMessages.InitialInput()])
        self._transport_input_q: ta.Deque[ta.Any] = collections.deque()
        self._fed_final_input = False

        self._write_q: ta.Deque[
            ta.Union[memoryview, IoPipelineFlowMessages.FlushOutput]
        ] = collections.deque()
        self._write_q_bytes = 0
        self._output_writable = True

        self._transport_final_output: ta.Optional[IoPipelineMessages.FinalOutput] = None

        self._clock = self._Clock()
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

    @property
    def is_running(self) -> bool:
        return (
            self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING) and
            hasattr(self, '_pipeline') and
            self._pipeline.is_ready
        )

    @property
    def pending_output_bytes(self) -> int:
        return self._write_q_bytes

    @property
    def has_pending_output(self) -> bool:
        return bool(self._write_q) or self._transport_final_output is not None

    @property
    def wants_input(self) -> bool:
        return (
            self._state is IoPipelineDriverState.RUNNING and
            not self._pipeline.saw_final_input and
            self._want_read
        )

    #

    _pipeline: IoPipeline
    _flow: ta.Optional[IoPipelineFlow]
    _sched: HeapIoPipelineSchedulingService
    _want_read = False

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
            self._sched = HeapIoPipelineSchedulingService(self._clock)
            self._pipeline = pipeline = IoPipeline(dc.replace(
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

            self._flow = flow = pipeline.services.find(IoPipelineFlow)
            self._want_read = IoPipelineFlow.is_auto_read(flow)

        except BaseException:
            self._state = IoPipelineDriverState.FAILED
            raise

        self._state = IoPipelineDriverState.RUNNING
        return pipeline

    #

    def close(self) -> None:
        """Abort the pipeline and discard all simulated transport input and output."""

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
            self._input_q.clear()
            self._transport_input_q.clear()
            self._write_q.clear()
            self._write_q_bytes = 0
            self._transport_final_output = None

    def _fail(self) -> None:
        self._state = IoPipelineDriverState.FAILED
        try:
            if (pipeline := self._opt_pipeline()) is not None and pipeline.is_ready:
                pipeline.destroy()
        finally:
            self._input_q.clear()
            self._transport_input_q.clear()
            self._write_q.clear()
            self._write_q_bytes = 0
            self._transport_final_output = None

    def __enter__(self) -> 'PureIoPipelineDriver':  # noqa
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    #

    def enqueue(self, *in_msgs: ta.Any) -> None:
        """Queue already-decoded inbound messages directly at the driver boundary."""

        self._input_q.extend(in_msgs)

    def feed_input(self, *in_msgs: ta.Any) -> None:
        """Make transport input available for a later `next(read=True)` step."""

        check.state(not self._fed_final_input)
        for msg in in_msgs:
            check.not_isinstance(msg, IoPipelineMessages.FinalInput)
            self._transport_input_q.append(msg)

    def feed_eof(self) -> None:
        """Make the simulated transport EOF available for a later input step."""

        check.state(not self._fed_final_input)
        self._fed_final_input = True
        self._transport_input_q.append(IoPipelineMessages.FinalInput())

    def _do_read(self) -> ta.List[ta.Any]:
        if not self._transport_input_q:
            return []

        msg = self._transport_input_q.popleft()
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self._want_read = False
            return [msg]

        if isinstance(msg, (bytes, bytearray, memoryview)) and len(msg) > self._config.read_chunk_size:
            mv = memoryview(msg)
            chunk = bytes(mv[:self._config.read_chunk_size])
            self._transport_input_q.appendleft(mv[self._config.read_chunk_size:])
            msg = chunk

        out = [msg]
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

    def _complete_flush_output(self, msg: IoPipelineFlowMessages.FlushOutput) -> None:
        with self._pipeline.enter():
            if not msg.is_done():
                msg.set_succeeded(None)

    def _gracefully_close(self) -> None:
        pipeline = self._pipeline
        final_output = check.not_none(self._transport_final_output)
        check.empty(self._write_q)

        self._transport_final_output = None
        try:
            with pipeline.enter():
                if not final_output.is_done():
                    final_output.set_succeeded(None)
            pipeline.destroy()
        except BaseException:
            self._state = IoPipelineDriverState.FAILED
            raise
        else:
            self._state = IoPipelineDriverState.CLOSED

    def drain_output(self, max_bytes: ta.Optional[int] = None) -> bytes:
        """
        Accept queued bytes across the simulated transport boundary.

        `max_bytes` bounds this acceptance step. When omitted, `Config.write_chunk_max` supplies the bound; when both
        are omitted all currently queued bytes are accepted. Zero-byte flush fences at the reached boundary complete
        in the same call. A pending FinalOutput completes once the queue has drained.
        """

        self._ensure_pipeline()
        check.state(self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING))

        if max_bytes is not None and max_bytes < 0:
            raise ValueError(max_bytes)
        if (write_chunk_max := self._config.write_chunk_max) is not None:
            max_bytes = write_chunk_max if max_bytes is None else min(max_bytes, write_chunk_max)

        remaining = max_bytes
        out: ta.List[bytes] = []
        try:
            while self._write_q:
                head = self._write_q[0]
                if isinstance(head, IoPipelineFlowMessages.FlushOutput):
                    self._write_q.popleft()
                    self._complete_flush_output(head)
                    continue

                if remaining == 0:
                    break

                n = len(head) if remaining is None else min(len(head), remaining)
                out.append(bytes(head[:n]))
                self._write_q_bytes -= n
                if n == len(head):
                    self._write_q.popleft()
                else:
                    self._write_q[0] = head[n:]

                if remaining is not None:
                    remaining -= n

            self._update_output_writability()

            if self._transport_final_output is not None and not self._write_q:
                self._gracefully_close()

        except BaseException:
            if self._state is not IoPipelineDriverState.FAILED:
                self._fail()
            raise

        return b''.join(out)

    #

    def advance_time(self, delay_s: float) -> None:
        """Advance the driver's manual monotonic clock without implicitly running callbacks."""

        if not math.isfinite(delay_s) or delay_s < 0.:
            raise ValueError(delay_s)
        self._clock.now += delay_s

    def next_deadline(self) -> ta.Optional[float]:
        if self._state not in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING):
            return None
        return self._sched.next_deadline()

    #

    def _handle_output(self, msg: ta.Any) -> ta.Literal['handled', 'unhandled']:
        if ByteStreamBuffers.can_bytes(msg):
            self._enqueue_write(msg)
            return 'handled'

        if isinstance(msg, IoPipelineFlowMessages.FlushOutput):
            self._write_q.append(msg)
            return 'handled'

        if isinstance(msg, IoPipelineMessages.FinalOutput):
            check.none(self._transport_final_output)
            self._transport_final_output = msg
            self._state = IoPipelineDriverState.DRAINING
            return 'handled'

        if isinstance(msg, IoPipelineMessages.Defer):
            self._pipeline.run_deferred(msg)
            return 'handled'

        if isinstance(msg, IoPipelineFlowMessages.ReadyForInput):
            check.state(self._flow is not None)
            if self._config.strict_input_flow:
                check.state(not self._want_read)
            self._want_read = True
            return 'handled'

        return 'unhandled'

    def _poll(self) -> ta.Union[
        ta.Tuple[ta.Literal['unhandled'], ta.Any],
        ta.Literal['read', 'write'],
        None,
    ]:
        pipeline = self._ensure_pipeline()
        check.state(pipeline.is_ready)

        self._sched.run_due()

        while True:
            if (out_msg := pipeline.output.poll()) is not None:
                handled = self._handle_output(out_msg)
                if handled == 'handled':
                    continue
                return ('unhandled', out_msg)

            if self._input_q:
                pipeline.feed_in(self._input_q.popleft())
                continue

            if self._transport_final_output is not None or self._write_q:
                return 'write'

            if self._transport_input_q and not pipeline.saw_final_input and self._want_read:
                return 'read'

            return None

    def next(
            self,
            *,
            read: bool = True,
            raise_on_stall: bool = True,
    ) -> ta.Optional[ta.Any]:
        """
        Advance until an unhandled output or no immediately runnable work remains.

        The pure driver never waits. `read=False` additionally leaves supplied transport input untouched, matching the
        non-waiting embedding contract of the socket and asyncio drivers.
        """

        self._ensure_pipeline()
        while True:
            try:
                out = self._poll()
            except BaseException:
                self._fail()
                raise

            if isinstance(out, tuple):
                return out[1]

            if out == 'read':
                if not read:
                    return None
                try:
                    self._input_q.extend(self._do_read())
                except BaseException:
                    self._fail()
                    raise
                continue

            if out == 'write':
                return None

            if out is None:
                if read and raise_on_stall:
                    raise RuntimeError('Pipeline stalled')
                return None

            raise RuntimeError(f'Unknown output: {out!r}')

    def loop_until_done(self) -> bytes:
        """Drive supplied work to graceful completion and return accepted transport output."""

        output: ta.List[bytes] = []
        try:
            while self.is_running or self._state is IoPipelineDriverState.NEW:
                if (out := self.next(read=True, raise_on_stall=False)) is not None:
                    raise TypeError(out)
                if self.has_pending_output:
                    output.append(self.drain_output())
                    continue
                if self._transport_input_q and self.wants_input:
                    continue
                if self.is_running:
                    raise RuntimeError('Pipeline stalled')
        finally:
            self.close()

        return b''.join(output)
