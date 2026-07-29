# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
TODO:
 - self._sock.shutdown(socket.SHUT_WR) ?
"""
import collections
import dataclasses as dc
import socket
import typing as ta

from ....lite.check import check
from ....logs.modules import get_module_logger
from ....sockets.addresses import SocketAddress
from ...fdio.handlers import SocketFdioHandler
from ...streambufs.types import BytesLike
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


class IoPipelineDriverSocketFdioHandler(SocketFdioHandler):
    @dc.dataclass(frozen=True)
    class Config:
        DEFAULT: ta.ClassVar['IoPipelineDriverSocketFdioHandler.Config']

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
            sock: socket.socket,
            addr: SocketAddress,
            spec: IoPipeline.Spec,
            config: ta.Optional[Config] = None,
    ) -> None:
        sock.setblocking(False)
        super().__init__(sock, addr)

        self._spec = spec
        if config is None:
            config = self.Config.DEFAULT
        self._config = config

        self._input_q: collections.deque[ta.Any] = collections.deque()
        self._input_q.append(IoPipelineMessages.InitialInput())

        self._write_q: collections.deque[
            ta.Union[BytesLike, IoPipelineFlowMessages.FlushOutput]
        ] = collections.deque()
        self._write_q_bytes = 0
        self._output_writable = True

        self._transport_final_output: ta.Optional[IoPipelineMessages.FinalOutput] = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._state.name}>'

    @property
    def config(self) -> Config:
        return self._config

    @property
    def pipeline(self) -> IoPipeline:
        return self._pipeline

    #

    ACTIVE_STATES: ta.ClassVar[ta.Tuple[IoPipelineDriverState, ...]] = (
        IoPipelineDriverState.RUNNING,
        IoPipelineDriverState.DRAINING,
    )

    _state: IoPipelineDriverState = IoPipelineDriverState.NEW

    @property
    def state(self) -> IoPipelineDriverState:
        return self._state

    @property
    def is_active(self) -> bool:
        return self._state in self.ACTIVE_STATES

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
            ],
        ))

    #

    def close(self) -> None:
        """Abort the driver and discard any queued transport output."""

        if self._state is IoPipelineDriverState.CLOSED:
            return

        if self._state is IoPipelineDriverState.FAILED:
            if not self.closed:
                self._fail()
            return

        if self._state is IoPipelineDriverState.NEW:
            try:
                super().close()
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

            finally:
                self._write_q.clear()
                self._write_q_bytes = 0
                self._transport_final_output = None

                super().close()

                self._state = IoPipelineDriverState.CLOSED

        except BaseException:  # noqa
            self._state = IoPipelineDriverState.FAILED
            raise

    def _fail(self) -> None:
        try:
            if (pipeline := self._opt_pipeline()) is not None and pipeline.is_ready:
                pipeline.destroy()

        finally:
            self._write_q.clear()
            self._write_q_bytes = 0
            self._transport_final_output = None

            try:
                super().close()
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
            super().close()
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

    #

    _want_read: bool = False

    def _do_read(self) -> ta.List[ta.Any]:
        out: ta.List[ta.Any] = []

        try:
            b = check.not_none(self._sock).recv(self._config.read_chunk_size)
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

    def _try_send(self, b: BytesLike) -> ta.Optional[int]:
        if (wcm := self._config.write_chunk_max) is not None and len(b) > wcm:
            write_b = b[:wcm]
        else:
            write_b = b

        try:
            sr = check.not_none(self._sock).send(write_b)
        except BlockingIOError:
            return None
        except OSError:
            self._fail()
            raise

        if sr < 1:
            error = BrokenPipeError('socket send returned no progress')
            self._fail()
            raise error

        return sr

    def _try_flush_write_q(self) -> None:
        while self._write_q:
            head = self._write_q[0]
            if isinstance(head, IoPipelineFlowMessages.FlushOutput):
                self._write_q.popleft()
                with self._pipeline.enter():
                    if not head.is_done():
                        head.set_succeeded(None)
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
        if self._flow is None:
            return

        if self._output_writable:
            if self._write_q_bytes > self._config.write_high_watermark:
                self._output_writable = False
                self._pipeline.feed_in(IoPipelineFlowMessages.PauseOutput())

        elif self._write_q_bytes <= self._config.write_low_watermark:
            self._output_writable = True
            self._pipeline.feed_in(IoPipelineFlowMessages.ReadyForOutput())

    #

    _sched: HeapIoPipelineSchedulingService

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

        elif isinstance(msg, IoPipelineMessages.FinalOutput):
            check.none(self._transport_final_output)
            self._transport_final_output = msg
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

        try:
            self._sched.run_due()
        except BaseException:
            self._fail()
            raise

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

    def poll(self) -> ta.Union[
        ta.Tuple[ta.Literal['unhandled'], ta.Any],
        ta.Literal['read', 'stop'],
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
        check.state(pipeline.is_ready)

        while True:
            out = self.poll()

            if isinstance(out, tuple):
                ok, ov = out
                if ok == 'unhandled':
                    return ov

                else:
                    raise RuntimeError(f'Unknown output: {ok!r}')

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

    def readable(self) -> bool:
        return (
            self._state is IoPipelineDriverState.RUNNING and
            not self._pipeline.saw_final_input and
            self._want_read
        )

    def writable(self) -> bool:
        return self.is_active and bool(self._write_q)

    def next_deadline(self) -> ta.Optional[float]:
        if not self.is_active:
            return None
        return self._sched.next_deadline()

    #

    def on_readable(self) -> None:
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
