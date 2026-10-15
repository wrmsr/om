# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import asyncio
import collections
import dataclasses as dc
import functools
import typing as ta
import weakref

from .....lite.abstract import Abstract
from .....lite.check import check
from .....logs.modules import get_module_loggers
from .....logs.utils import async_exception_logging
from ....streambufs.direct import DirectByteStreamBuffer
from ....streambufs.segmented import SegmentedByteStreamBuffer
from ....streambufs.utils import ByteStreamBuffers
from ...asyncs import AsyncIoPipelineMessages
from ...core import IoPipeline
from ...core import IoPipelineMessages
from ...core import IoPipelineServices
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


log, alog = get_module_loggers(globals())  # noqa


##


class PollAsyncioStreamIoPipelineDriver(IoPipelinePostingTarget):
    """
    An asyncio pipeline driver with a poll-based interface mirroring the sync driver's API. Unlike
    LoopAsyncioStreamIoPipelineDriver which runs its own internal event loop via run(), this driver exposes next() and
    loop_until_done() methods that let the caller control stepping. Unhandled pipeline output messages are returned from
    next(), enabling streaming use cases.

    ShutdownOutput calls the writer's `write_eof()`, which the transport performs after the bytes already written, and
    completes after the following drain - the same transport-boundary guarantee FlushOutput receives. A writer which
    cannot write EOF fails the message with UnsupportedIoPipelineError and is left intact. Reading continues afterwards.

    The driver is task-stable: besides whatever task steps it, it runs one task reading the transport and one draining
    it (which also performs the graceful close), both for its whole life. Timers use the heap scheduler the other
    drivers use, with one loop timer handle armed for the earliest deadline, which wakes the command loop with a
    command. Only an Await supplied as a coroutine becomes a task of its own, since it must run concurrently.

    Enqueued messages, posted work, and completed reads are commands on one queue, processed in order; a post wakes a
    driver waiting on it.
    """

    @dc.dataclass(frozen=True)
    class Config:
        DEFAULT: ta.ClassVar['PollAsyncioStreamIoPipelineDriver.Config']

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
            reader: asyncio.StreamReader,
            writer: ta.Optional[asyncio.StreamWriter] = None,
            config: ta.Optional[Config] = None,
            *,
            _pipeline_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,
    ) -> None:
        super().__init__()

        self._spec = spec
        self._reader = reader
        self._writer = writer
        self._closing_writer: ta.Optional[asyncio.StreamWriter] = None
        if config is None:
            config = PollAsyncioStreamIoPipelineDriver.Config.DEFAULT
        self._config = config
        self._pipeline_kwargs = _pipeline_kwargs

        #

        self._shutdown_event = asyncio.Event()
        self._command_queue: asyncio.Queue = asyncio.Queue()

        self._state = IoPipelineDriverState.NEW
        self._has_init = False
        self._loop: ta.Optional[asyncio.AbstractEventLoop] = None

        # The one task which calls the writer's drain(), and performs the graceful close, woken through an event. A
        # drain is requested with a flag; the fences (FlushOutput and ShutdownOutput) requested before it is called are
        # the ones it completes. A drain is outstanding from its start until its completion command has been handled.
        # The idle event is set while the drainer has nothing requested or running.
        self._drainer_task: ta.Optional[asyncio.Task] = None
        self._drainer_event = asyncio.Event()
        self._drain_requested = False
        self._drains_outstanding = 0
        self._drain_idle_event = asyncio.Event()
        self._drain_idle_event.set()
        self._pending_drain_fences: ta.List[IoPipelineMessages.Completable] = []
        self._post_drain_output_q: collections.deque[ta.Any] = collections.deque()
        # Output bytes held behind a pending drain count toward writability as much as the transport's own buffer.
        self._post_drain_output_bytes = 0

        # Pending awaits, each marked whether the driver created its task (from a coroutine) and so owns it.
        self._pending_awaits: ta.Dict[asyncio.Future, bool] = {}

        # The graceful close is performed by the drainer task once FinalOutput reached the terminal, so commands -
        # timers, awaits, reads to discard - are serviced while the transport flushes.
        self._close_requested = False
        self._close_in_progress = False
        self._transport_final_output: ta.Optional[IoPipelineMessages.FinalOutput] = None
        self._saved_write_limits: ta.Optional[ta.Tuple[int, int]] = None

        # The loop timer armed for the scheduler's earliest deadline: a timer handle, not a task.
        self._timer_handle: ta.Optional[asyncio.TimerHandle] = None
        self._timer_deadline: ta.Optional[float] = None

        self._read_task: ta.Optional[asyncio.Task] = None
        self._want_read = False
        self._want_read_event = asyncio.Event()
        self._has_read_eof: bool = False

        self._output_writable = True
        self._output_shutdown = False

        self._command_handlers: ta.Mapping[ta.Type['PollAsyncioStreamIoPipelineDriver._Command'], ta.Callable[[ta.Any, ta.Any], ta.Awaitable[None]]]  # noqa
        self._output_handlers: ta.Mapping[type, ta.Callable[[ta.Any, ta.Any], ta.Awaitable[ta.Optional[str]]]]

        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._FeedInCommand([
            IoPipelineMessages.InitialInput(),
        ]))

        # Usable before the pipeline exists: a post made then runs once it does.
        self._posting = TargetIoPipelinePostingService(self)

    _sched: HeapIoPipelineSchedulingService

    _pipeline: IoPipeline

    _flow: ta.Optional[IoPipelineFlow]

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
    def posting(self) -> TargetIoPipelinePostingService:
        """The pipeline's posting service, usable from construction on."""

        return self._posting

    @property
    def is_running(self) -> bool:
        return (
            self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING) and
            hasattr(self, '_pipeline') and
            self._pipeline.is_ready
        )

    @property
    def output_shutdown(self) -> bool:
        """Whether a ShutdownOutput has shut down the writer's output half."""

        return self._output_shutdown

    ##
    # init

    async def _ensure_init(self) -> IoPipeline:
        if self._has_init:
            return self._pipeline
        check.state(self._state is IoPipelineDriverState.NEW)
        self._has_init = True

        try:
            return self._init()

        except BaseException:
            self._state = IoPipelineDriverState.FAILED
            self._shutdown_event.set()

            try:
                if self._pipeline.is_ready:
                    self._pipeline.destroy()
            except AttributeError:
                pass

            await self._abort_writer()
            raise

    def _init(self) -> IoPipeline:
        self._loop = loop = asyncio.get_running_loop()
        self._sched = HeapIoPipelineSchedulingService(
            loop.time,
            on_earliest_change=functools.partial(
                PollAsyncioStreamIoPipelineDriver._on_sched_earliest_change,
                weakref.ref(self),
            ),
        )

        services = IoPipelineServices.of(self._spec.services)
        self._flow = services.find(IoPipelineFlow)

        self._command_handlers = self._build_command_handlers()
        self._output_handlers = self._build_output_handlers()

        #

        self._pipeline = IoPipeline(
            dc.replace(
                self._spec,
                metadata=(*self._spec.metadata, DriverIoPipelineMetadata(self)),
                services=(*self._spec.services, self._sched, self._posting),
            ),
            **(self._pipeline_kwargs or {}),
        )

        if self._flow is not None and self._writer is not None:
            self._writer.transport.set_write_buffer_limits(
                high=self._config.write_high_watermark,
                low=self._config.write_low_watermark,
            )

        #

        self._read_task = asyncio.create_task(self._read_task_main())
        if self._writer is not None:
            self._drainer_task = asyncio.create_task(self._drainer_task_main())

        if self._is_auto_read():
            self._want_read = True
            self._want_read_event.set()

        self._state = IoPipelineDriverState.RUNNING

        return self._pipeline

    def _is_auto_read(self) -> bool:
        return (flow := self._flow) is None or flow.is_auto_read()

    ##
    # async utils

    def _own_loop_running(self) -> bool:
        """
        Whether the driver's own loop is the one running here - the only case in which `close()` may wait for what it
        cancels. Closed from anywhere else - a coroutine closed by garbage collection once its loop is gone, say, or a
        caller on another loop - it does its bookkeeping without suspending, and without touching a closed loop.
        """

        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            return False
        if (loop := self._loop) is None:
            return True  # Not yet initialized: whichever loop runs here is as good as any.
        return running is loop and not loop.is_closed()

    def _loop_closed(self) -> bool:
        return (loop := self._loop) is not None and loop.is_closed()

    async def _cancel_tasks(
            self,
            *tasks: ta.Optional[asyncio.Future],
            wait: bool = True,
    ) -> None:
        if self._loop_closed():
            return  # Nothing can run any more, and a closed loop refuses the cancellation's callbacks.

        cts: ta.List[asyncio.Future] = []

        for t in tasks:
            if t is not None and not t.done():
                t.cancel()
                cts.append(t)

        if cts and wait:
            await asyncio.gather(*cts, return_exceptions=True)

    #

    async def _gracefully_close_writer(self) -> None:
        """
        Flushes everything written, then closes the transport. Closing it first would stop it reading at once, and a
        peer which has yet to read this side's output may be waiting for its own to be read first.
        """

        if self._writer is None:
            return

        writer = self._writer
        self._writer = None
        self._closing_writer = writer

        try:
            buffered = writer.transport.get_write_buffer_size()
        except AttributeError:
            # An SSL transport whose underlying transport is already gone (3.8): nothing is left to flush, and the
            # close reports what became of the connection.
            buffered = 0

        if buffered > 0:
            # Zero watermarks make the drain return once the buffer is empty rather than at the low watermark.
            self._set_write_limits(writer, high=0, low=0)
            await writer.drain()

        writer.close()
        # Cancelling a wait on the transport's close cancels the transport's own close waiter, which every later wait
        # would then raise from: the wait itself is shielded, and an abort completes it.
        await asyncio.shield(writer.wait_closed())
        if self._closing_writer is writer:
            self._closing_writer = None

    @staticmethod
    def _set_write_limits(writer: asyncio.StreamWriter, *, high: int, low: int) -> None:
        try:
            writer.transport.set_write_buffer_limits(high=high, low=low)
        except (AttributeError, NotImplementedError):
            pass

    async def _abort_writer(self, *, wait: bool = True) -> None:
        writer = self._writer
        if writer is None:
            writer = self._closing_writer
        if writer is None:
            return

        self._writer = None
        self._closing_writer = None

        try:
            try:
                writer.transport.abort()
            except (AttributeError, NotImplementedError):
                writer.close()

            if wait:
                await writer.wait_closed()

        except Exception:  # noqa
            pass

    ##

    class _Command(Abstract):
        pass

    ##
    # feed in

    @dc.dataclass(frozen=True)
    class _FeedInCommand(_Command):
        msgs: ta.Sequence[ta.Any]

        fut: ta.Optional['asyncio.Future[None]'] = None

        def __repr__(self) -> str:
            return f'{self.__class__.__name__}([{", ".join(map(repr, self.msgs))}])'

    async def _handle_command_feed_in(self, cmd: _FeedInCommand) -> None:
        try:
            self._pipeline.feed_in(*cmd.msgs)

        except BaseException as e:
            # The waiter may have been cancelled meanwhile; the queued input is still processed.
            if (fut := cmd.fut) is not None and not fut.done():
                fut.set_exception(e)
            raise

        else:
            if (fut := cmd.fut) is not None and not fut.done():
                fut.set_result(None)

    def enqueue_waitable(self, *msgs: ta.Any) -> 'asyncio.Future[None]':
        check.state(self._state in (IoPipelineDriverState.NEW, IoPipelineDriverState.RUNNING))

        fut: asyncio.Future[None] = asyncio.Future()
        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._FeedInCommand(msgs, fut=fut))
        return fut

    def enqueue(self, *msgs: ta.Any) -> None:
        check.state(self._state in (IoPipelineDriverState.NEW, IoPipelineDriverState.RUNNING))

        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._FeedInCommand(msgs))

    ##
    # posting

    @dc.dataclass(frozen=True)
    class _PostCommand(_Command):
        post: IoPipelinePost

    def accept_post(self, post: IoPipelinePost) -> None:
        if self._state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED):
            raise ClosedIoPipelinePostingError(f'{self!r} is {self._state.name}')
        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._PostCommand(post))

    async def _handle_command_post(self, cmd: _PostCommand) -> None:
        cmd.post.run(self._pipeline)

    ##
    # read task

    async def _read_task_main(self) -> None:
        try:
            while not self._shutdown_event.is_set():
                # In manual flow mode, wait for ReadyForInput to signal via _want_read_event.
                if not self._is_auto_read():
                    await self._want_read_event.wait()

                    if self._shutdown_event.is_set():
                        break

                    self._want_read_event.clear()

                try:
                    data = await self._reader.read(min(
                        self._config.read_batch_max_bytes,
                        self._config.read_chunk_size * self._config.read_batch_max_reads,
                    ))
                except asyncio.CancelledError:
                    raise
                except Exception as e:  # noqa
                    if not self._shutdown_event.is_set():
                        self._command_queue.put_nowait(
                            PollAsyncioStreamIoPipelineDriver._ReadFailedCommand(e),
                        )
                    break

                if self._shutdown_event.is_set():
                    break

                self._command_queue.put_nowait(
                    PollAsyncioStreamIoPipelineDriver._ReadCompletedCommand(data),
                )

                if not data:  # EOF
                    break

        except asyncio.CancelledError:
            pass

    ##
    # read completed

    class _ReadCompletedCommand(_Command):
        def __init__(self, data: ta.Union[bytes, ta.List[bytes]]) -> None:
            self._data = data

        def __repr__(self) -> str:
            return (
                f'{self.__class__.__name__}@{id(self):x}'
                f'({"[...]" if isinstance(self._data, list) else "..." if self._data else ""})'
            )

        def data(self) -> ta.Sequence[bytes]:
            if isinstance(self._data, bytes):
                return [self._data]
            elif isinstance(self._data, list):
                return self._data
            else:
                raise TypeError(self._data)

    @dc.dataclass(frozen=True)
    class _ReadFailedCommand(_Command):
        exc: BaseException

    async def _handle_command_read_completed(self, cmd: _ReadCompletedCommand) -> None:
        if self._state is IoPipelineDriverState.DRAINING:
            # Nothing consumes input any more, but it is still taken off the transport (and dropped) so a peer blocked
            # on this side reading can proceed to read this side's remaining output.
            if self._flow is not None and not self._is_auto_read():
                self._want_read_event.set()
            return

        eof = False
        data: ta.List[bytes] = []

        in_msgs: ta.List[ta.Any] = []

        for b in cmd.data():
            check.state(not eof)
            if not b:
                eof = True
            else:
                data.append(b)

        if data:
            if len(data) == 1:
                in_msgs.append(DirectByteStreamBuffer(data[0]))
            else:
                buf = SegmentedByteStreamBuffer()
                for b in data:
                    buf.write(b)
                in_msgs.append(buf)

        if data and self._flow is not None:
            in_msgs.append(IoPipelineFlowMessages.FlushInput())

        if self._flow is not None:
            self._want_read = False

        if eof:
            self._has_read_eof = True

            in_msgs.append(IoPipelineMessages.FinalInput())

        #

        self._pipeline.feed_in(*in_msgs)

        #

    async def _handle_command_read_failed(self, cmd: _ReadFailedCommand) -> None:
        raise cmd.exc

    ##
    # scheduling

    def _arm_timer(self) -> None:
        """
        Arms one loop timer for the scheduler's earliest deadline, which wakes the command loop with a command, unless
        one is already armed for it. A wake at a since cancelled deadline runs nothing and is harmless.
        """

        if (loop := self._loop) is None or loop.is_closed():
            return

        deadline = self._sched.next_deadline()
        if deadline == self._timer_deadline:
            return

        if (th := self._timer_handle) is not None:
            self._timer_handle = None
            th.cancel()

        self._timer_deadline = deadline
        if deadline is not None and not self._shutdown_event.is_set():
            self._timer_handle = loop.call_at(
                deadline,
                PollAsyncioStreamIoPipelineDriver._on_timer,
                weakref.ref(self),
            )

    def _disarm_timer(self) -> None:
        self._timer_deadline = None
        if (th := self._timer_handle) is not None:
            self._timer_handle = None
            th.cancel()

    @staticmethod
    def _on_sched_earliest_change(
            d_ref: ta.Callable[[], ta.Optional['PollAsyncioStreamIoPipelineDriver']],
    ) -> None:
        if (d := d_ref()) is not None:
            d._arm_timer()  # noqa

    @staticmethod
    def _on_timer(
            d_ref: ta.Callable[[], ta.Optional['PollAsyncioStreamIoPipelineDriver']],
    ) -> None:
        if (d := d_ref()) is None:
            return

        d._timer_handle = None  # noqa
        d._timer_deadline = None  # noqa
        if not d._shutdown_event.is_set():  # noqa
            d._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._TimerCommand())  # noqa

    class _TimerCommand(_Command):
        pass

    async def _handle_command_timer(self, cmd: _TimerCommand) -> None:
        self._sched.run_due()

    ##
    # shutdown

    class _ShutdownCommand(_Command):
        pass

    ##
    # deferred continuations

    @dc.dataclass(frozen=True)
    class _DeferCommand(_Command):
        msg: IoPipelineMessages.Defer

    async def _handle_command_defer(self, cmd: _DeferCommand) -> None:
        # A deferred continuation is a fairness yield: the timers due go first.
        self._sched.run_due()
        if self._pipeline.is_ready:
            self._pipeline.run_deferred(cmd.msg)

    ##
    # graceful close

    @dc.dataclass(frozen=True)
    class _CloseCompletedCommand(_Command):
        exc: ta.Optional[BaseException] = None

    @property
    def _close_pending(self) -> bool:
        return self._close_requested or self._close_in_progress

    def _request_close(self) -> None:
        """Asks the drainer task to perform the graceful close, after any drain it has pending."""

        self._close_requested = True
        self._drainer_event.set()

    def _fail_graceful_close(self, exc: BaseException) -> None:
        self._finish_flush_outputs(
            self._take_pending_drain_fences(),
            exc,
            raise_listener_errors=False,
        )
        if (msg := self._transport_final_output) is not None:
            self._transport_final_output = None
            self._finish_final_output(msg, exc, raise_listener_errors=False)

    async def _complete_graceful_close(self) -> None:
        msg = check.not_none(self._transport_final_output)
        self._transport_final_output = None

        try:
            self._finish_flush_outputs(self._take_pending_drain_fences())
        finally:
            self._finish_final_output(msg)

        self._shutdown_event.set()
        self._want_read_event.set()
        await self._cancel_tasks(self._read_task)
        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._ShutdownCommand())

    async def _handle_command_close_completed(self, cmd: _CloseCompletedCommand) -> None:
        if self._transport_final_output is None:
            return  # Closed or failed meanwhile.

        if (exc := cmd.exc) is not None:
            # The peer reset the connection while it was being flushed, say.
            self._fail_graceful_close(exc)
            await self._fail()
            raise exc

        await self._complete_graceful_close()

    ##
    # output drain

    @dc.dataclass(frozen=True)
    class _DrainCompletedCommand(_Command):
        fences: ta.Sequence[IoPipelineMessages.Completable]
        exc: ta.Optional[BaseException] = None

    def _finish_flush_outputs(
            self,
            flush_outputs: ta.Iterable[IoPipelineMessages.Completable],
            exc: ta.Optional[BaseException] = None,
            *,
            raise_listener_errors: bool = True,
    ) -> None:
        flush_outputs = list(flush_outputs)
        if not flush_outputs:
            return

        first_listener_exc: ta.Optional[BaseException] = None

        with self._pipeline.enter():
            for flush_output in flush_outputs:
                if flush_output.is_done():
                    continue
                try:
                    if exc is None:
                        flush_output.set_succeeded(None)
                    else:
                        flush_output.set_failed(exc)
                except BaseException as listener_exc:  # noqa
                    if first_listener_exc is None:
                        first_listener_exc = listener_exc

        if first_listener_exc is not None and raise_listener_errors:
            raise first_listener_exc

    def _take_pending_drain_fences(self) -> ta.List[IoPipelineMessages.Completable]:
        fences = self._pending_drain_fences
        self._pending_drain_fences = []
        return fences

    def _finish_final_output(
            self,
            msg: IoPipelineMessages.FinalOutput,
            exc: ta.Optional[BaseException] = None,
            *,
            raise_listener_errors: bool = True,
    ) -> None:
        if msg.is_done():
            return

        try:
            with self._pipeline.enter():
                if exc is None:
                    msg.set_succeeded(None)
                else:
                    msg.set_failed(exc)
        except BaseException:  # noqa
            if raise_listener_errors:
                raise

    def _set_shutdown_drain_limits(self) -> None:
        """
        `write_eof()` half-closes the transport only once its buffer has emptied, whereas `drain()` returns once the
        buffer reaches the low watermark. For the shutdown's drain to complete at the half-close - success means the
        transport's output half was shut down - the watermarks are zero until it has completed. Nothing may produce
        ordinary output once ShutdownOutput reached the terminal, so the zero limits announce nothing.
        """

        if (writer := self._writer) is None or self._saved_write_limits is not None:
            return
        try:
            self._saved_write_limits = writer.transport.get_write_buffer_limits()  # (low, high)
        except (AttributeError, NotImplementedError):
            self._saved_write_limits = None
        self._set_write_limits(writer, high=0, low=0)

    def _restore_write_limits(self) -> None:
        if (writer := self._writer) is None:
            return
        if (saved := self._saved_write_limits) is not None:
            self._saved_write_limits = None
            self._set_write_limits(writer, high=saved[1], low=saved[0])
        elif self._flow is not None:
            self._set_write_limits(
                writer,
                high=self._config.write_high_watermark,
                low=self._config.write_low_watermark,
            )

    @property
    def _drain_pending(self) -> bool:
        return self._drain_requested or self._drains_outstanding > 0

    def _request_drain(self, fence: ta.Optional[IoPipelineMessages.Completable] = None) -> None:
        """
        Asks the drainer task for a drain, completing `fence` with it. A fence requested before the drain is called is
        completed by that drain; one requested while a drain runs - possible only through direct output handling, as
        the command loop holds fences behind a pending drain - is completed by the drain which follows it.
        """

        if self._writer is None:
            if fence is not None:
                self._finish_flush_outputs([fence])
            return

        if fence is not None:
            self._pending_drain_fences.append(fence)

        if not self._drain_requested:
            self._drain_requested = True
            self._drain_idle_event.clear()
            self._drainer_event.set()

    async def _drainer_task_main(self) -> None:
        """
        The one task which calls the writer's `drain()`, and performs the graceful close after FinalOutput, woken
        through an event as the work arises. Drains never overlap, as the stream API requires: a drain requested while
        one runs follows it. Completions are reported to the command loop as commands.
        """

        try:
            while True:
                if self._drain_requested:
                    self._drain_requested = False
                    fences = self._take_pending_drain_fences()
                    self._drains_outstanding += 1
                    exc: ta.Optional[BaseException] = None
                    try:
                        await self._drain_writer()
                    except asyncio.CancelledError:
                        raise
                    except BaseException as e:  # noqa
                        exc = e
                    finally:
                        if not self._drain_requested:
                            self._drain_idle_event.set()
                    self._command_queue.put_nowait(
                        PollAsyncioStreamIoPipelineDriver._DrainCompletedCommand(fences, exc),
                    )
                    if exc is not None:
                        return  # The driver fails on it: nothing more can be drained or closed.
                    continue

                if self._close_requested:
                    self._close_requested = False
                    self._close_in_progress = True
                    exc = None
                    try:
                        await self._gracefully_close_writer()
                    except asyncio.CancelledError:
                        raise
                    except BaseException as e:  # noqa
                        exc = e
                    finally:
                        self._close_in_progress = False
                    self._command_queue.put_nowait(
                        PollAsyncioStreamIoPipelineDriver._CloseCompletedCommand(exc),
                    )
                    return

                await self._drainer_event.wait()
                self._drainer_event.clear()

        except asyncio.CancelledError:
            pass

    async def _drain_writer(self) -> None:
        if (writer := self._writer) is None:
            return
        if self._output_shutdown:
            self._set_shutdown_drain_limits()
        await writer.drain()

    async def _handle_command_drain_completed(self, cmd: _DrainCompletedCommand) -> None:
        if self._drains_outstanding:
            self._drains_outstanding -= 1

        if self._state not in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING):
            return

        if (exc := cmd.exc) is not None:
            self._finish_flush_outputs(
                [*cmd.fences, *self._take_pending_drain_fences()],
                exc,
                raise_listener_errors=False,
            )
            await self._fail()
            raise exc

        if self._output_shutdown and not self._drains_outstanding:
            self._restore_write_limits()

        self._finish_flush_outputs(cmd.fences)

        if self._state is IoPipelineDriverState.RUNNING:
            self._update_output_writability(drained=True)

    ##
    # awaits

    @dc.dataclass(frozen=True)
    class _AwaitCompletedCommand(_Command):
        msg: AsyncIoPipelineMessages.Await
        fut: ta.Optional[asyncio.Future]

    @dc.dataclass(frozen=True)
    class _AwaitFailedCommand(_Command):
        msg: AsyncIoPipelineMessages.Await
        exc: BaseException

    async def _handle_command_await_completed(self, cmd: _AwaitCompletedCommand) -> None:
        fut = cmd.fut

        if fut is None:
            # Bare yield / sleep(0) case.
            with self._pipeline.enter():
                cmd.msg.set_succeeded(None)
            return

        self._pending_awaits.pop(fut, None)

        if cmd.msg.is_done():
            # Failed meanwhile by its producer - a multiplexed stream which ended, say - which cancelled the work.
            return

        try:
            result = fut.result()
        except BaseException as e:  # noqa
            with self._pipeline.enter():
                cmd.msg.set_failed(e)
        else:
            with self._pipeline.enter():
                cmd.msg.set_succeeded(result)

    async def _handle_command_await_failed(self, cmd: _AwaitFailedCommand) -> None:
        with self._pipeline.enter():
            cmd.msg.set_failed(cmd.exc)

    async def _handle_output_await(
            self,
            msg: AsyncIoPipelineMessages.Await,
    ) -> ta.Optional[str]:
        loop = asyncio.get_running_loop()

        # A coroutine becomes a task the driver creates, and so owns: it is cancelled if the Await is failed by its
        # producer before it completes, and when the driver closes. A task or future supplied is the caller's.
        created = asyncio.iscoroutine(msg.obj)

        try:
            fut = asyncio.ensure_future(msg.obj)
        except BaseException as e:  # noqa
            self._command_queue.put_nowait(
                PollAsyncioStreamIoPipelineDriver._AwaitFailedCommand(msg, e),
            )
            return None

        try:
            fut_loop = fut.get_loop()
        except AttributeError:
            fut_loop = loop

        if fut_loop is not loop:
            self._command_queue.put_nowait(
                PollAsyncioStreamIoPipelineDriver._AwaitFailedCommand(
                    msg,
                    RuntimeError(f'awaitable {fut!r} is attached to a different event loop'),
                ),
            )
            return None

        self._pending_awaits[fut] = created

        def done_callback(f: asyncio.Future) -> None:
            self._command_queue.put_nowait(
                PollAsyncioStreamIoPipelineDriver._AwaitCompletedCommand(msg, f),
            )

        fut.add_done_callback(done_callback)  # noqa

        if created:
            def msg_done(m: IoPipelineMessages.Completable) -> None:
                if not fut.done():
                    fut.cancel()

            msg.add_listener(msg_done)

        return None

    async def _cancel_created_awaits(self, *, wait: bool = True) -> None:
        tasks = [fut for fut, created in self._pending_awaits.items() if created]
        self._pending_awaits.clear()
        await self._cancel_tasks(*tasks, wait=wait)

    ##
    # command handling

    def _build_command_handlers(self) -> ta.Mapping[
        ta.Type[_Command],
        ta.Callable[[ta.Any, ta.Any], ta.Awaitable[None]],
    ]:
        cls = type(self)
        return {
            PollAsyncioStreamIoPipelineDriver._FeedInCommand: cls._handle_command_feed_in,
            PollAsyncioStreamIoPipelineDriver._PostCommand: cls._handle_command_post,
            PollAsyncioStreamIoPipelineDriver._ReadCompletedCommand: cls._handle_command_read_completed,
            PollAsyncioStreamIoPipelineDriver._ReadFailedCommand: cls._handle_command_read_failed,
            PollAsyncioStreamIoPipelineDriver._TimerCommand: cls._handle_command_timer,
            PollAsyncioStreamIoPipelineDriver._DeferCommand: cls._handle_command_defer,
            PollAsyncioStreamIoPipelineDriver._DrainCompletedCommand: cls._handle_command_drain_completed,
            PollAsyncioStreamIoPipelineDriver._CloseCompletedCommand: cls._handle_command_close_completed,
            PollAsyncioStreamIoPipelineDriver._AwaitCompletedCommand: cls._handle_command_await_completed,
            PollAsyncioStreamIoPipelineDriver._AwaitFailedCommand: cls._handle_command_await_failed,
        }

    async def _handle_command(self, cmd: _Command) -> None:
        log.debug(lambda: f'Handling command: {cmd!r}')

        try:
            fn = self._command_handlers[cmd.__class__]
        except KeyError:
            raise TypeError(f'Unknown command type: {cmd.__class__}') from None

        try:
            await fn(self, cmd)
        except BaseException:
            if self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING):
                await self._fail()
            raise

        if (
                self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING) and
                not self._pipeline.is_ready
        ):
            # Destroyed from under the driver - by an application policy in a timer callback, say: an explicit close.
            await self.close()

    ##
    # output handling

    async def _handle_output_final_output(self, msg: IoPipelineMessages.FinalOutput) -> ta.Optional[str]:
        """
        The graceful close - flushing everything written, then closing the transport - is performed by the drainer
        task, so that while a peer which has yet to read keeps it from completing, the driver still runs timers,
        completes awaits, and keeps taking the peer's output off the transport (and dropping it) so the peer can
        proceed to read this side's.
        """

        self._state = IoPipelineDriverState.DRAINING
        self._transport_final_output = msg

        # Input is taken but not consumed from now on: let a manual-mode read task read regardless.
        self._want_read_event.set()

        if self._writer is None or self._drainer_task is None:
            await self._complete_graceful_close()
            return None

        # A drain still pending completes first, on its own; the drainer task then performs the close.
        self._request_close()
        return None

    async def _handle_output_defer(self, msg: IoPipelineMessages.Defer) -> ta.Optional[str]:
        # A deferred continuation is a fairness yield: the commands already queued - reads, awaits, drain completions -
        # and then the timers due go first.
        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._DeferCommand(msg))
        return None

    async def _handle_output_bytes(self, msg: ta.Any) -> None:
        for mv in ByteStreamBuffers.iter_segments(msg):
            if self._writer is not None and mv:
                if (wcm := self._config.write_chunk_max) is None:
                    self._writer.write(mv)
                else:
                    for pos in range(0, len(mv), wcm):
                        self._writer.write(mv[pos:pos + wcm])

        self._update_output_writability()

    async def _handle_output_flush_output(self, msg: IoPipelineFlowMessages.FlushOutput) -> ta.Optional[str]:
        self._request_drain(msg)
        return None

    async def _handle_output_shutdown_output(self, msg: IoPipelineMessages.ShutdownOutput) -> ta.Optional[str]:
        if (writer := self._writer) is not None:
            if not writer.can_write_eof():
                with self._pipeline.enter():
                    if not msg.is_done():
                        msg.set_failed(UnsupportedIoPipelineError(f'{writer!r} cannot write eof'))
                return None

            writer.write_eof()

        self._output_shutdown = True
        self._request_drain(msg)
        return None

    async def _handle_output_ready_for_input(self, msg: IoPipelineFlowMessages.ReadyForInput) -> ta.Optional[str]:
        check.state(self._flow is not None)
        if self._config.strict_input_flow:
            check.state(not self._want_read)
        self._want_read = True
        self._want_read_event.set()
        return None

    def _hold_post_drain_output(self, msg: ta.Any) -> None:
        self._post_drain_output_q.append(msg)
        if ByteStreamBuffers.can_bytes(msg):
            self._post_drain_output_bytes += ByteStreamBuffers.bytes_len(msg)
            # Without this a producer continuing through Defers - which are not held - would never be paused.
            self._update_output_writability()

    def _take_post_drain_output(self) -> ta.Any:
        msg = self._post_drain_output_q.popleft()
        if ByteStreamBuffers.can_bytes(msg):
            self._post_drain_output_bytes -= ByteStreamBuffers.bytes_len(msg)
        return msg

    def _update_output_writability(self, *, drained: bool = False) -> None:
        """
        The transport's own write buffer limits are the watermarks, so it pauses and resumes with the same hysteresis.
        A completed drain means it resumed - its buffer reached the low watermark - so unless the buffer has since grown
        past the high watermark, output is writable again.
        """

        if (
                self._state is not IoPipelineDriverState.RUNNING or
                self._flow is None or
                self._writer is None or
                self._output_shutdown
        ):
            return

        size = self._writer.transport.get_write_buffer_size() + self._post_drain_output_bytes
        if self._output_writable:
            if size > self._config.write_high_watermark:
                self._output_writable = False
                self._pipeline.feed_in(IoPipelineFlowMessages.PauseOutput())

        elif (
                (
                    size <= self._config.write_low_watermark or
                    (drained and size <= self._config.write_high_watermark)
                ) and
                # Never announced once ShutdownOutput reached the terminal - not just once the transport performed it -
                # since from then on nothing may produce ordinary output.
                not self._pipeline.saw_shutdown_output
        ):
            self._output_writable = True
            self._pipeline.feed_in(IoPipelineFlowMessages.ReadyForOutput())

    def _ensure_paused_output_drain(self) -> None:
        """
        The transport writes in the background, and nothing else observes it catching up: while output is paused, a
        drain must be pending, or a producer which honors writability without flushing would wait forever. Started only
        once no runnable output remains, so it never delays fences already queued behind the paused output.
        """

        if (
                not self._output_writable and
                not self._drain_pending and
                self._state is IoPipelineDriverState.RUNNING and
                self._writer is not None and
                not self._output_shutdown
        ):
            self._request_drain()

    def _build_output_handlers(self) -> ta.Mapping[
        type,
        ta.Callable[[ta.Any, ta.Any], ta.Awaitable[ta.Optional[str]]],
    ]:
        cls = type(self)
        return {
            IoPipelineMessages.FinalOutput: cls._handle_output_final_output,
            IoPipelineMessages.Defer: cls._handle_output_defer,
            IoPipelineFlowMessages.FlushOutput: cls._handle_output_flush_output,
            IoPipelineMessages.ShutdownOutput: cls._handle_output_shutdown_output,
            IoPipelineFlowMessages.ReadyForInput: cls._handle_output_ready_for_input,
            AsyncIoPipelineMessages.Await: cls._handle_output_await,
        }

    async def _handle_output(self, msg: ta.Any) -> str:
        log.debug(lambda: f'Handling output: {msg!r}')

        try:
            if ByteStreamBuffers.can_bytes(msg):
                await self._handle_output_bytes(msg)
                return 'handled'

            try:
                fn = self._output_handlers[msg.__class__]
            except KeyError:
                return 'unhandled'

            ret = await fn(self, msg)
            return ret if ret is not None else 'handled'

        except BaseException:
            if self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING):
                await self._fail()
            raise

    ##
    # core loop

    @staticmethod
    def _is_drain_ordered_output(msg: ta.Any) -> bool:
        return ByteStreamBuffers.can_bytes(msg) or isinstance(msg, (
            IoPipelineFlowMessages.FlushOutput,
            IoPipelineMessages.ShutdownOutput,
            IoPipelineMessages.FinalOutput,
        ))

    def _has_pending_work(self) -> bool:
        if self._pending_awaits:
            return True

        if self._drain_pending or self._close_pending:
            return True

        if self._read_task is not None and not self._read_task.done():
            return True

        if hasattr(self, '_sched') and self._sched.next_deadline() is not None:
            return True

        return False

    async def next(
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

        pipeline = await self._ensure_init()

        try:
            self._sched.run_due()
        except BaseException:
            await self._fail()
            raise

        while True:
            if not pipeline.is_ready:
                # Destroyed from under the driver - by an application policy in a callback, say: an explicit close.
                await self.close()
                return None

            if self._drain_pending:
                while (blocked_msg := pipeline.output.poll()) is not None:
                    # Only output bytes and output fences are ordered against a pending drain. Everything else - read
                    # requests, deferred work, awaits, unhandled messages for the caller - is not, and must not wait
                    # behind a drain stalled on the peer: a read request held here would stop input while output waits
                    # for the peer to read, deadlocking two such peers.
                    if self._is_drain_ordered_output(blocked_msg):
                        self._hold_post_drain_output(blocked_msg)
                        continue

                    handled = await self._handle_output(blocked_msg)

                    if handled == 'handled':
                        continue

                    elif handled == 'unhandled':
                        return blocked_msg

                    else:
                        raise RuntimeError(f'Unexpected handled value for {blocked_msg!r}: {handled!r}')

            else:
                if self._post_drain_output_q:
                    out_msg = self._take_post_drain_output()
                else:
                    out_msg = pipeline.output.poll()

                if out_msg is not None:
                    handled = await self._handle_output(out_msg)

                    if handled == 'handled':
                        continue

                    elif handled == 'unhandled':
                        return out_msg

                    elif handled == 'stop':
                        break

                    else:
                        raise RuntimeError(f'Unknown handled value: {handled!r}')

            self._ensure_paused_output_drain()

            # Handling pipeline output (notably a Defer) can schedule timers just as handling a command can, so the
            # loop timer is (re)armed for the earliest deadline before any wait.
            self._arm_timer()

            try:
                cmd = self._command_queue.get_nowait()
            except asyncio.QueueEmpty:
                if self._shutdown_event.is_set():
                    break

                if not read:
                    if not self._close_pending:
                        return None
                    # The graceful close is the driver's own work in flight, not input: it is waited for as it always
                    # was, but with what arrives meanwhile - timers, awaits, reads to discard - serviced.

                elif raise_on_stall and not self._has_pending_work():
                    raise RuntimeError('Pipeline stalled') from None

                cmd = await self._command_queue.get()

            if isinstance(cmd, PollAsyncioStreamIoPipelineDriver._ShutdownCommand):
                break

            await self._handle_command(cmd)

        try:
            pipeline.destroy()
        except BaseException:
            await self._fail()
            raise

        self._state = IoPipelineDriverState.CLOSED
        return None

    @async_exception_logging(alog)
    async def loop_until_done(self) -> None:
        try:
            while True:
                if (out := await self.next()) is not None:
                    raise TypeError(out)

                if not self._pipeline.is_ready:
                    break

        finally:
            await self.close()

    ##
    # lifecycle

    def _drain_command_queue(self, exc: BaseException) -> None:
        posts: ta.List[IoPipelinePost] = []
        while True:
            try:
                cmd = self._command_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if (
                    isinstance(cmd, PollAsyncioStreamIoPipelineDriver._FeedInCommand) and
                    (fut := cmd.fut) is not None and
                    not fut.done()
            ):
                fut.set_exception(exc)
            elif isinstance(cmd, PollAsyncioStreamIoPipelineDriver._PostCommand):
                posts.append(cmd.post)

        fail_io_pipeline_posts(posts, exc)

    async def _fail(self) -> None:
        self._state = IoPipelineDriverState.FAILED
        await self.close()

    async def close(self) -> None:
        """Abort the driver without waiting for graceful pipeline output completion."""

        if self._state is IoPipelineDriverState.CLOSED:
            return

        failed = self._state is IoPipelineDriverState.FAILED

        # Only on its own running loop may the driver wait for what it cancels.
        wait = self._own_loop_running()

        try:
            self._shutdown_event.set()

            self._want_read_event.set()

            self._disarm_timer()

            self._drain_requested = False
            self._drains_outstanding = 0
            self._close_requested = False
            await self._cancel_tasks(self._drainer_task, wait=wait)
            self._drainer_task = None
            self._drain_idle_event.set()
            self._fail_graceful_close(AbortedIoPipelineError('Driver closed before transport flush completion'))
            self._post_drain_output_q.clear()
            self._post_drain_output_bytes = 0

            await self._cancel_tasks(self._read_task, wait=wait)
            await self._cancel_created_awaits(wait=wait)

            # Input never processed is released, and anyone waiting on it is told.
            self._drain_command_queue(AbortedIoPipelineError('Driver closed before the input was processed'))
            self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._ShutdownCommand())

            await self._abort_writer(wait=wait)

            if hasattr(self, '_sched'):
                self._sched.cancel_all()

            if self._has_init:
                try:
                    if self._pipeline.is_ready:
                        self._pipeline.destroy()
                except AttributeError:
                    pass

        except BaseException:
            self._state = IoPipelineDriverState.FAILED
            raise

        self._state = IoPipelineDriverState.FAILED if failed else IoPipelineDriverState.CLOSED

    async def __aenter__(self) -> 'PollAsyncioStreamIoPipelineDriver':  # noqa
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
