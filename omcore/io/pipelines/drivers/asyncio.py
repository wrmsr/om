# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import asyncio
import collections
import dataclasses as dc
import typing as ta
import weakref

from ....lite.abstract import Abstract
from ....lite.check import check
from ....logs.modules import get_module_loggers
from ....logs.utils import async_exception_logging
from ...streambufs.utils import ByteStreamBuffers
from ..asyncs import AsyncIoPipelineMessages
from ..core import IoPipeline
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerRef
from ..core import IoPipelineHandlerUpdate
from ..core import IoPipelineMessages
from ..core import IoPipelineService
from ..core import IoPipelineServices
from ..core import IoPipelineUpdate
from ..errors import AbortedIoPipelineError
from ..flow.types import IoPipelineFlow
from ..flow.types import IoPipelineFlowMessages
from ..sched.types import IoPipelineScheduling
from .metadata import DriverIoPipelineMetadata
from .types import IoPipelineDriverState


log, alog = get_module_loggers(globals())  # noqa


##


class PollAsyncioStreamIoPipelineDriver:
    """
    An asyncio pipeline driver with a poll-based interface mirroring the sync driver's API. Unlike
    LoopAsyncioStreamIoPipelineDriver which runs its own internal event loop via run(), this driver exposes next() and
    loop_until_done() methods that let the caller control stepping. Unhandled pipeline output messages are returned from
    next(), enabling streaming use cases.
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

        self._drain_task: ta.Optional[asyncio.Task] = None
        self._drain_again = False
        self._drain_flush_outputs: ta.List[IoPipelineFlowMessages.FlushOutput] = []
        self._next_drain_flush_outputs: ta.List[IoPipelineFlowMessages.FlushOutput] = []
        self._post_drain_output_q: collections.deque[ta.Any] = collections.deque()

        self._pending_awaits: ta.Set[asyncio.Future] = set()

        self._read_task: ta.Optional[asyncio.Task] = None
        self._want_read = False
        self._want_read_event = asyncio.Event()
        self._has_read_eof: bool = False

        self._output_writable = True

        self._command_handlers: ta.Mapping[ta.Type['PollAsyncioStreamIoPipelineDriver._Command'], ta.Callable[[ta.Any, ta.Any], ta.Awaitable[None]]]  # noqa
        self._output_handlers: ta.Mapping[type, ta.Callable[[ta.Any, ta.Any], ta.Awaitable[ta.Optional[str]]]]

        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._FeedInCommand([
            IoPipelineMessages.InitialInput(),
        ]))

    _sched: 'PollAsyncioStreamIoPipelineDriver._SchedulingService'

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
    def is_running(self) -> bool:
        return (
            self._state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING) and
            hasattr(self, '_pipeline') and
            self._pipeline.is_ready
        )

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
        self._sched = self._SchedulingService(self)

        services = IoPipelineServices.of(self._spec.services)
        self._flow = services.find(IoPipelineFlow)

        self._command_handlers = self._build_command_handlers()
        self._output_handlers = self._build_output_handlers()

        #

        self._pipeline = IoPipeline(
            dc.replace(
                self._spec,
                metadata=(*self._spec.metadata, DriverIoPipelineMetadata(self)),
                services=(*self._spec.services, self._sched),
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

        if self._is_auto_read():
            self._want_read = True
            self._want_read_event.set()

        self._state = IoPipelineDriverState.RUNNING

        return self._pipeline

    def _is_auto_read(self) -> bool:
        return (flow := self._flow) is None or flow.is_auto_read()

    ##
    # async utils

    @staticmethod
    async def _cancel_tasks(
            *tasks: ta.Optional[asyncio.Task],
            check_running: bool = False,
    ) -> None:
        if check_running:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return
            else:
                if not loop.is_running():
                    return

        #

        cts: ta.List[asyncio.Task] = []

        for t in tasks:
            if t is not None and not t.done():
                t.cancel()
                cts.append(t)

        if cts:
            await asyncio.gather(*cts, return_exceptions=True)

    #

    async def _gracefully_close_writer(self) -> None:
        if self._writer is None:
            return

        writer = self._writer
        self._writer = None
        self._closing_writer = writer

        writer.close()
        await writer.wait_closed()
        if self._closing_writer is writer:
            self._closing_writer = None

    async def _abort_writer(self) -> None:
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
            if (fut := cmd.fut) is not None:
                fut.set_exception(e)
            raise

        else:
            if (fut := cmd.fut) is not None:
                fut.set_result(None)

    def enqueue_waitable(self, *msgs: ta.Any) -> 'asyncio.Future[None]':
        check.state(not self._shutdown_event.is_set())

        fut: asyncio.Future[None] = asyncio.Future()
        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._FeedInCommand(msgs, fut=fut))
        return fut

    def enqueue(self, *msgs: ta.Any) -> None:
        check.state(not self._shutdown_event.is_set())

        self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._FeedInCommand(msgs))

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
        eof = False
        had_data = False

        in_msgs: ta.List[ta.Any] = []

        for b in cmd.data():
            check.state(not eof)
            if not b:
                eof = True
            else:
                in_msgs.append(b)
                had_data = True

        if had_data and self._flow is not None:
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

    class _SchedulingService(IoPipelineScheduling, IoPipelineService):
        def __init__(self, d: 'PollAsyncioStreamIoPipelineDriver') -> None:
            super().__init__()

            self.__d_ref = weakref.ref(d)

            self.__pipeline_ref: ta.Optional[weakref.ReferenceType] = None

            self._seq = 0
            self._pending: ta.List[PollAsyncioStreamIoPipelineDriver._SchedulingService._Handle] = []
            self._live: ta.Set[PollAsyncioStreamIoPipelineDriver._SchedulingService._Handle] = set()
            self._tasks: ta.Set[asyncio.Task] = set()

        @property
        def _d(self) -> 'PollAsyncioStreamIoPipelineDriver':
            return check.not_none(self.__d_ref())

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

        @ta.final
        class _Handle(IoPipelineScheduling.Handle):
            def __init__(
                    self,
                    sched: 'PollAsyncioStreamIoPipelineDriver._SchedulingService',
                    handler_ref: IoPipelineHandlerRef,
                    deadline: float,
                    seq: int,
                    fn: ta.Callable[..., None],
                    with_context: bool,
            ) -> None:
                self.__sched_ref = weakref.ref(sched)
                self.__handler_context_ref = weakref.ref(handler_ref._context)  # noqa
                self._deadline = deadline
                self._seq = seq
                self._fn = fn
                self._with_context = with_context

                self._task: ta.Optional[asyncio.Task] = None
                self._queued = False
                self._cancelled = False
                self._done = False

            @property
            def _sched(self) -> 'PollAsyncioStreamIoPipelineDriver._SchedulingService':
                return check.not_none(self.__sched_ref())

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

                if self._task is not None:
                    self._task.cancel()

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

            loop = asyncio.get_running_loop()
            h = self._Handle(
                self,
                handler_ref,
                loop.time() + max(0., delay_s),
                self._seq,
                fn,
                with_context,
            )
            self._seq += 1
            self._pending.append(h)
            self._live.add(h)
            return h

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
            for h in tuple(self._live):
                if handler_ref is None or h._handler_context is handler_ref._context:  # noqa
                    h.cancel()

            self._pending = [h for h in self._pending if not h._cancelled]  # noqa

        async def _task_body(self, h: _Handle) -> None:
            delay = max(0., h._deadline - asyncio.get_running_loop().time())  # noqa
            await asyncio.sleep(delay)

            if not h._cancelled:  # noqa
                h._queued = True  # noqa
                self._d._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._ScheduledCommand(h))  # noqa

        def _enqueue_due(self, now: float) -> None:
            due = sorted(
                (
                    h._deadline,  # noqa
                    h._seq,  # noqa
                    h,
                )
                for h in self._live
                if not h._queued and h._deadline <= now  # noqa
            )

            for _, _, h in due:
                if h._task is not None:  # noqa
                    h._task.cancel()  # noqa
                h._queued = True  # noqa
                self._d._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._ScheduledCommand(h))  # noqa

        async def _flush_pending(self) -> None:
            if not (lst := self._pending):
                return

            self._pending = []

            for h in lst:
                if h._cancelled or h._queued:  # noqa
                    continue

                task = asyncio.create_task(self._task_body(h))
                h._task = task  # noqa
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)

        def _take(self, h: _Handle) -> bool:
            if h._cancelled or h._done:  # noqa
                return False

            check.in_(h, self._live)
            h._done = True  # noqa
            self._live.remove(h)
            return True

    @dc.dataclass(frozen=True)
    class _ScheduledCommand(_Command):
        handle: 'PollAsyncioStreamIoPipelineDriver._SchedulingService._Handle'

    async def _handle_command_scheduled(self, cmd: _ScheduledCommand) -> None:
        if not self._sched._take(cmd.handle):  # noqa
            return

        with self._pipeline.enter():
            cmd.handle._run()  # noqa

    ##
    # shutdown

    class _ShutdownCommand(_Command):
        pass

    ##
    # output drain

    @dc.dataclass(frozen=True)
    class _DrainCompletedCommand(_Command):
        task: asyncio.Task

    def _finish_flush_outputs(
            self,
            flush_outputs: ta.Iterable[IoPipelineFlowMessages.FlushOutput],
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

    def _take_drain_flush_outputs(self) -> ta.List[IoPipelineFlowMessages.FlushOutput]:
        flush_outputs = self._drain_flush_outputs
        self._drain_flush_outputs = []
        if self._next_drain_flush_outputs:
            flush_outputs.extend(self._next_drain_flush_outputs)
            self._next_drain_flush_outputs = []
        return flush_outputs

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

    def _start_drain(self) -> None:
        check.none(self._drain_task)
        writer = check.not_none(self._writer)

        task = asyncio.create_task(writer.drain())
        self._drain_task = task

        def done_callback(done_task: asyncio.Task) -> None:
            if not self._shutdown_event.is_set():
                self._command_queue.put_nowait(
                    PollAsyncioStreamIoPipelineDriver._DrainCompletedCommand(done_task),
                )

        task.add_done_callback(done_callback)

    def _request_drain(self, flush_output: IoPipelineFlowMessages.FlushOutput) -> None:
        if self._writer is None:
            self._finish_flush_outputs([flush_output])
            return

        if self._drain_task is not None:
            self._drain_again = True
            self._next_drain_flush_outputs.append(flush_output)
            return

        self._drain_flush_outputs.append(flush_output)
        self._start_drain()

    async def _cancel_drain_task(self, *, propagate_done_error: bool = False) -> None:
        task = self._drain_task
        self._drain_task = None
        self._drain_again = False

        if task is None:
            return

        was_done = task.done()
        if not was_done:
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)

        if propagate_done_error and was_done and not task.cancelled():
            task.result()

    async def _handle_command_drain_completed(self, cmd: _DrainCompletedCommand) -> None:
        if cmd.task is not self._drain_task:
            return

        self._drain_task = None
        drain_again = self._drain_again
        self._drain_again = False
        flush_outputs = self._drain_flush_outputs
        self._drain_flush_outputs = []

        try:
            cmd.task.result()
        except BaseException as e:
            flush_outputs.extend(self._next_drain_flush_outputs)
            self._next_drain_flush_outputs = []
            self._finish_flush_outputs(flush_outputs, e, raise_listener_errors=False)
            await self._fail()
            raise

        self._finish_flush_outputs(flush_outputs)

        if self._state is IoPipelineDriverState.RUNNING:
            self._update_output_writability()
            if drain_again:
                self._drain_flush_outputs = self._next_drain_flush_outputs
                self._next_drain_flush_outputs = []
                self._start_drain()

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

        self._pending_awaits.discard(fut)

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

        self._pending_awaits.add(fut)

        def done_callback(f: asyncio.Future) -> None:
            self._command_queue.put_nowait(
                PollAsyncioStreamIoPipelineDriver._AwaitCompletedCommand(msg, f),
            )

        fut.add_done_callback(done_callback)  # noqa
        return None

    ##
    # command handling

    def _build_command_handlers(self) -> ta.Mapping[
        ta.Type[_Command],
        ta.Callable[[ta.Any, ta.Any], ta.Awaitable[None]],
    ]:
        cls = type(self)
        return {
            PollAsyncioStreamIoPipelineDriver._FeedInCommand: cls._handle_command_feed_in,
            PollAsyncioStreamIoPipelineDriver._ReadCompletedCommand: cls._handle_command_read_completed,
            PollAsyncioStreamIoPipelineDriver._ReadFailedCommand: cls._handle_command_read_failed,
            PollAsyncioStreamIoPipelineDriver._ScheduledCommand: cls._handle_command_scheduled,
            PollAsyncioStreamIoPipelineDriver._DrainCompletedCommand: cls._handle_command_drain_completed,
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

    ##
    # output handling

    async def _handle_output_final_output(self, msg: IoPipelineMessages.FinalOutput) -> ta.Optional[str]:
        self._shutdown_event.set()
        self._want_read_event.set()

        self._state = IoPipelineDriverState.DRAINING
        try:
            await self._cancel_drain_task(propagate_done_error=True)
            await self._cancel_tasks(self._read_task, check_running=True)
            await self._gracefully_close_writer()

        except BaseException as e:
            self._finish_flush_outputs(
                self._take_drain_flush_outputs(),
                e,
                raise_listener_errors=False,
            )
            self._finish_final_output(msg, e, raise_listener_errors=False)
            await self._fail()
            raise

        try:
            self._finish_flush_outputs(self._take_drain_flush_outputs())
        finally:
            self._finish_final_output(msg)

        return 'stop'

    async def _handle_output_defer(self, msg: IoPipelineMessages.Defer) -> ta.Optional[str]:
        self._pipeline.run_deferred(msg)
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

    async def _handle_output_ready_for_input(self, msg: IoPipelineFlowMessages.ReadyForInput) -> ta.Optional[str]:
        check.state(self._flow is not None)
        if self._config.strict_input_flow:
            check.state(not self._want_read)
        self._want_read = True
        self._want_read_event.set()
        return None

    def _update_output_writability(self) -> None:
        if (
                self._state is not IoPipelineDriverState.RUNNING or
                self._flow is None or
                self._writer is None
        ):
            return

        size = self._writer.transport.get_write_buffer_size()
        if self._output_writable:
            if size > self._config.write_high_watermark:
                self._output_writable = False
                self._pipeline.feed_in(IoPipelineFlowMessages.PauseOutput())

        elif size <= self._config.write_low_watermark:
            self._output_writable = True
            self._pipeline.feed_in(IoPipelineFlowMessages.ReadyForOutput())

    def _build_output_handlers(self) -> ta.Mapping[
        type,
        ta.Callable[[ta.Any, ta.Any], ta.Awaitable[ta.Optional[str]]],
    ]:
        cls = type(self)
        return {
            IoPipelineMessages.FinalOutput: cls._handle_output_final_output,
            IoPipelineMessages.Defer: cls._handle_output_defer,
            IoPipelineFlowMessages.FlushOutput: cls._handle_output_flush_output,
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

    def _has_pending_work(self) -> bool:
        if self._pending_awaits:
            return True

        if self._drain_task is not None:
            return True

        if self._read_task is not None and not self._read_task.done():
            return True

        if hasattr(self, '_sched') and self._sched._live:  # noqa
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
        check.state(pipeline.is_ready)

        self._sched._enqueue_due(asyncio.get_running_loop().time())  # noqa

        while True:
            if self._drain_task is not None:
                while (blocked_msg := pipeline.output.poll()) is not None:
                    if isinstance(blocked_msg, (BaseException, IoPipelineMessages.Error)):
                        return blocked_msg
                    self._post_drain_output_q.append(blocked_msg)

            else:
                if self._post_drain_output_q:
                    out_msg = self._post_drain_output_q.popleft()
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

            try:
                cmd = self._command_queue.get_nowait()
            except asyncio.QueueEmpty:
                if self._shutdown_event.is_set():
                    break

                if not read:
                    return None

                if raise_on_stall and not self._has_pending_work():
                    raise RuntimeError('Pipeline stalled') from None

                cmd = await self._command_queue.get()

            if isinstance(cmd, PollAsyncioStreamIoPipelineDriver._ShutdownCommand):
                break

            await self._handle_command(cmd)

            await self._sched._flush_pending()  # noqa

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

    async def _fail(self) -> None:
        self._state = IoPipelineDriverState.FAILED
        await self.close()

    async def close(self) -> None:
        """Abort the driver without waiting for graceful pipeline output completion."""

        if self._state is IoPipelineDriverState.CLOSED:
            return

        failed = self._state is IoPipelineDriverState.FAILED

        try:
            self._shutdown_event.set()

            self._want_read_event.set()

            await self._cancel_drain_task()
            self._finish_flush_outputs(
                self._take_drain_flush_outputs(),
                AbortedIoPipelineError('Driver closed before transport flush completion'),
                raise_listener_errors=False,
            )
            self._post_drain_output_q.clear()

            await self._cancel_tasks(self._read_task, check_running=True)

            self._command_queue.put_nowait(PollAsyncioStreamIoPipelineDriver._ShutdownCommand())

            await self._abort_writer()

            if hasattr(self, '_sched'):
                self._sched.cancel_all()
                if self._sched._tasks:  # noqa
                    await asyncio.gather(*self._sched._tasks, return_exceptions=True)  # noqa

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
