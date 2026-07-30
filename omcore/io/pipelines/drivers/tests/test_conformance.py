# ruff: noqa: SLF001 UP006 UP037 UP045
# @om-lite
import abc
import asyncio
import dataclasses as dc
import socket
import typing as ta

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...errors import AbortedIoPipelineError
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ...sched.types import IoPipelineScheduling
from ..asyncio import PollAsyncioStreamIoPipelineDriver
from ..fdio import IoPipelineDriverSocketFdioHandler
from ..pure import PureIoPipelineDriver
from ..sync import SyncSocketIoPipelineDriver
from ..types import IoPipelineDriverState


##


@dc.dataclass(frozen=True)
class _Emit:
    msgs: ta.Sequence[ta.Any]


@dc.dataclass(frozen=True)
class _ObservedInput:
    msg: ta.Any


@dc.dataclass(frozen=True)
class _TimerOutput:
    delay_s: float
    output: ta.Any


class _RequestInput:
    pass


class _ConformanceIoPipelineHandler(IoPipelineHandler):
    def __init__(self, *, output_after_final_input: ta.Optional[bytes] = None) -> None:
        super().__init__()

        self.inputs: ta.List[ta.Any] = []
        self.output_writability: ta.List[ta.Any] = []
        self._output_after_final_input = output_after_final_input

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Emit):
            for out_msg in msg.msgs:
                ctx.feed_out(out_msg)
            return

        if isinstance(msg, _TimerOutput):
            ctx.services[IoPipelineScheduling].schedule_context(
                ctx.ref,
                msg.delay_s,
                lambda ctx2: ctx2.feed_out(msg.output),
            )
            return

        if isinstance(msg, _RequestInput):
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())
            return

        self.inputs.append(msg)
        if isinstance(msg, (IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput)):
            self.output_writability.append(msg)
        elif isinstance(msg, IoPipelineMessages.FinalInput):
            if self._output_after_final_input is not None:
                ctx.feed_out(self._output_after_final_input)
            ctx.feed_out(_ObservedInput(msg))
        elif not isinstance(msg, (IoPipelineMessages.InitialInput, IoPipelineFlowMessages.FlushInput)):
            ctx.feed_out(_ObservedInput(msg))
            return
        ctx.feed_in(msg)


##


class _ConformanceDriverAdapter(abc.ABC):
    NAME: ta.ClassVar[str]

    def __init__(
            self,
            handler: _ConformanceIoPipelineHandler,
            *,
            manual_input: bool = False,
            explicit_auto_input: bool = False,
            read_chunk_size: int = 64 * 1024,
            read_batch_max_bytes: int = 1024 * 1024,
            read_batch_max_reads: int = 16,
            write_high_watermark: int = 4,
            write_low_watermark: int = 2,
    ) -> None:
        super().__init__()

        self.handler = handler
        self._manual_input = manual_input
        self._explicit_auto_input = explicit_auto_input
        self._read_chunk_size = read_chunk_size
        self._read_batch_max_bytes = read_batch_max_bytes
        self._read_batch_max_reads = read_batch_max_reads
        self._write_high_watermark = write_high_watermark
        self._write_low_watermark = write_low_watermark

    @property
    @abc.abstractmethod
    def state(self) -> IoPipelineDriverState:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def pipeline(self) -> IoPipeline:
        raise NotImplementedError

    @abc.abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def enqueue(self, *msgs: ta.Any) -> ta.Optional[ta.Any]:
        raise NotImplementedError

    @abc.abstractmethod
    async def feed_input(self, data: bytes) -> ta.Any:
        raise NotImplementedError

    @abc.abstractmethod
    async def feed_eof(self) -> ta.Any:
        raise NotImplementedError

    @abc.abstractmethod
    async def step_nonblocking(self) -> ta.Optional[ta.Any]:
        raise NotImplementedError

    @abc.abstractmethod
    async def block_output(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def release_output(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def take_output(self) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:
        raise NotImplementedError


def _make_spec(
        handler: _ConformanceIoPipelineHandler,
        *,
        manual_input: bool,
        explicit_auto_input: bool,
) -> IoPipeline.Spec:
    services: ta.List[ta.Any] = []
    if manual_input or explicit_auto_input:
        services.append(StubIoPipelineFlowService(auto_read=not manual_input))
    return IoPipeline.Spec([handler], services=services)


def _fill_socket_send_buffer(sock: socket.socket) -> None:
    while True:
        try:
            sock.send(b'x' * (64 * 1024))
        except BlockingIOError:
            return


def _drain_socket(sock: socket.socket) -> bytes:
    timeout = sock.gettimeout()
    sock.setblocking(False)
    chunks: ta.List[bytes] = []
    try:
        while True:
            try:
                chunk = sock.recv(64 * 1024)
            except BlockingIOError:
                return b''.join(chunks)
            if not chunk:
                return b''.join(chunks)
            chunks.append(chunk)
    finally:
        sock.settimeout(timeout)


class _SyncConformanceDriverAdapter(_ConformanceDriverAdapter):
    NAME = 'sync'

    def __init__(self, handler: _ConformanceIoPipelineHandler, **kwargs: ta.Any) -> None:
        super().__init__(handler, **kwargs)

        self._sock, self._peer = socket.socketpair()
        self._sock.setblocking(False)
        self._peer.setblocking(False)
        self._driver = SyncSocketIoPipelineDriver(
            _make_spec(
                handler,
                manual_input=self._manual_input,
                explicit_auto_input=self._explicit_auto_input,
            ),
            self._sock,
            SyncSocketIoPipelineDriver.Config(
                read_chunk_size=self._read_chunk_size,
                read_batch_max_bytes=self._read_batch_max_bytes,
                read_batch_max_reads=self._read_batch_max_reads,
                write_high_watermark=self._write_high_watermark,
                write_low_watermark=self._write_low_watermark,
            ),
        )
        self._output_blocked = False

    @property
    def state(self) -> IoPipelineDriverState:
        return self._driver.state

    @property
    def pipeline(self) -> IoPipeline:
        return self._driver.pipeline

    async def start(self) -> None:
        assert self._driver.next(read=False) is None

    async def enqueue(self, *msgs: ta.Any) -> ta.Optional[ta.Any]:
        self._driver.enqueue(*msgs)
        return self._driver.next(read=False)

    async def feed_input(self, data: bytes) -> ta.Any:
        self._peer.sendall(data)
        return self._driver.next(read=True, raise_on_stall=False)

    async def feed_eof(self) -> ta.Any:
        self._peer.shutdown(socket.SHUT_WR)
        return self._driver.next(read=True, raise_on_stall=False)

    async def step_nonblocking(self) -> ta.Optional[ta.Any]:
        return self._driver.next(read=False)

    async def block_output(self) -> None:
        _fill_socket_send_buffer(self._sock)
        self._output_blocked = True

    async def release_output(self) -> None:
        if self._output_blocked:
            _drain_socket(self._peer)
            self._output_blocked = False
        if self._driver.state in (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING):
            assert self._driver.next(read=False) is None

    def take_output(self) -> bytes:
        return _drain_socket(self._peer)

    async def close(self) -> None:
        try:
            self._driver.close()
        finally:
            self._sock.close()
            self._peer.close()


class _FdioConformanceDriverAdapter(_ConformanceDriverAdapter):
    NAME = 'fdio'

    def __init__(self, handler: _ConformanceIoPipelineHandler, **kwargs: ta.Any) -> None:
        super().__init__(handler, **kwargs)

        self._sock, self._peer = socket.socketpair()
        self._peer.setblocking(False)
        self._driver = IoPipelineDriverSocketFdioHandler(
            self._sock,
            ('local', 0),
            _make_spec(
                handler,
                manual_input=self._manual_input,
                explicit_auto_input=self._explicit_auto_input,
            ),
            IoPipelineDriverSocketFdioHandler.Config(
                read_chunk_size=self._read_chunk_size,
                read_batch_max_bytes=self._read_batch_max_bytes,
                read_batch_max_reads=self._read_batch_max_reads,
                write_high_watermark=self._write_high_watermark,
                write_low_watermark=self._write_low_watermark,
            ),
        )
        self._output_blocked = False

    @property
    def state(self) -> IoPipelineDriverState:
        return self._driver.state

    @property
    def pipeline(self) -> IoPipeline:
        return self._driver.pipeline

    async def start(self) -> None:
        assert self._driver.next(read=False) is None

    async def enqueue(self, *msgs: ta.Any) -> ta.Optional[ta.Any]:
        self._driver.enqueue(*msgs)
        return self._driver.next(read=False)

    async def feed_input(self, data: bytes) -> ta.Any:
        self._peer.sendall(data)
        return self._driver.next(read=True, raise_on_stall=False)

    async def feed_eof(self) -> ta.Any:
        self._peer.shutdown(socket.SHUT_WR)
        return self._driver.next(read=True, raise_on_stall=False)

    async def step_nonblocking(self) -> ta.Optional[ta.Any]:
        return self._driver.next(read=False)

    async def block_output(self) -> None:
        _fill_socket_send_buffer(self._sock)
        self._output_blocked = True

    async def release_output(self) -> None:
        if self._output_blocked:
            _drain_socket(self._peer)
            self._output_blocked = False
        if self._driver.writable():
            self._driver.on_writable()

    def take_output(self) -> bytes:
        return _drain_socket(self._peer)

    async def close(self) -> None:
        try:
            self._driver.close()
        finally:
            self._peer.close()


class _ConformanceStreamWriter:
    class Transport:
        def __init__(self, owner: '_ConformanceStreamWriter') -> None:
            self._owner = owner
            self._size = 0
            self._limits: ta.Optional[ta.Tuple[int, int]] = None

        def set_write_buffer_limits(self, *, high: int, low: int) -> None:
            self._limits = (low, high)

        def get_write_buffer_size(self) -> int:
            return self._size

        def abort(self) -> None:
            self._owner.closed = True
            self._owner._release.set()

    def __init__(self) -> None:
        self.transport = self.Transport(self)
        self.output = bytearray()
        self.closed = False
        self.blocked = False
        self.drain_started = asyncio.Event()
        self._release = asyncio.Event()

    def write(self, data: ta.Any) -> None:
        b = bytes(data)
        self.output.extend(b)
        self.transport._size += len(b)

    async def drain(self) -> None:
        self.drain_started.set()
        if self.blocked:
            await self._release.wait()
        self.transport._size = 0

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        pass


class _AsyncioConformanceDriverAdapter(_ConformanceDriverAdapter):
    NAME = 'asyncio'

    def __init__(self, handler: _ConformanceIoPipelineHandler, **kwargs: ta.Any) -> None:
        super().__init__(handler, **kwargs)

        self._reader = asyncio.StreamReader()
        self._writer = _ConformanceStreamWriter()
        self._driver = PollAsyncioStreamIoPipelineDriver(
            _make_spec(
                handler,
                manual_input=self._manual_input,
                explicit_auto_input=self._explicit_auto_input,
            ),
            self._reader,
            ta.cast(asyncio.StreamWriter, self._writer),
            PollAsyncioStreamIoPipelineDriver.Config(
                read_chunk_size=self._read_chunk_size,
                read_batch_max_bytes=self._read_batch_max_bytes,
                read_batch_max_reads=self._read_batch_max_reads,
                write_high_watermark=self._write_high_watermark,
                write_low_watermark=self._write_low_watermark,
            ),
        )

    @property
    def state(self) -> IoPipelineDriverState:
        return self._driver.state

    @property
    def pipeline(self) -> IoPipeline:
        return self._driver.pipeline

    async def start(self) -> None:
        assert await self._driver.next(read=False) is None

    async def _settle(self) -> ta.Optional[ta.Any]:
        for _ in range(8):
            await asyncio.sleep(0)
            if self._driver.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED):
                break
            out = await self._driver.next(read=False)
            if out is not None:
                return out
            if (
                    self._driver._command_queue.empty() and
                    (self._driver._drain_task is None or not self._driver._drain_task.done())
            ):
                break
        return None

    async def enqueue(self, *msgs: ta.Any) -> ta.Optional[ta.Any]:
        self._driver.enqueue(*msgs)
        out = await self._driver.next(read=False)
        if out is not None:
            return out
        return await self._settle()

    async def feed_input(self, data: bytes) -> ta.Any:
        self._reader.feed_data(data)
        return await self._driver.next(read=True, raise_on_stall=False)

    async def feed_eof(self) -> ta.Any:
        self._reader.feed_eof()
        return await self._driver.next(read=True, raise_on_stall=False)

    async def step_nonblocking(self) -> ta.Optional[ta.Any]:
        return await self._driver.next(read=False)

    async def block_output(self) -> None:
        self._writer.blocked = True

    async def release_output(self) -> None:
        self._writer._release.set()
        if (drain_task := self._driver._drain_task) is not None:
            await drain_task
        assert await self._settle() is None

    def take_output(self) -> bytes:
        out = bytes(self._writer.output)
        self._writer.output.clear()
        return out

    async def close(self) -> None:
        self._writer._release.set()
        await self._driver.close()


class _PureConformanceDriverAdapter(_ConformanceDriverAdapter):
    NAME = 'pure'

    def __init__(self, handler: _ConformanceIoPipelineHandler, **kwargs: ta.Any) -> None:
        super().__init__(handler, **kwargs)

        self._driver = PureIoPipelineDriver(
            _make_spec(
                handler,
                manual_input=self._manual_input,
                explicit_auto_input=self._explicit_auto_input,
            ),
            PureIoPipelineDriver.Config(
                read_chunk_size=self._read_chunk_size,
                read_batch_max_bytes=self._read_batch_max_bytes,
                read_batch_max_reads=self._read_batch_max_reads,
                write_high_watermark=self._write_high_watermark,
                write_low_watermark=self._write_low_watermark,
            ),
        )
        self._output = bytearray()

    @property
    def state(self) -> IoPipelineDriverState:
        return self._driver.state

    @property
    def pipeline(self) -> IoPipeline:
        return self._driver.pipeline

    async def start(self) -> None:
        assert self._driver.next(read=False) is None

    async def enqueue(self, *msgs: ta.Any) -> ta.Optional[ta.Any]:
        self._driver.enqueue(*msgs)
        return self._driver.next(read=False)

    async def feed_input(self, data: bytes) -> ta.Any:
        self._driver.feed_input(data)
        return self._driver.next(read=True, raise_on_stall=False)

    async def feed_eof(self) -> ta.Any:
        self._driver.feed_eof()
        return self._driver.next(read=True, raise_on_stall=False)

    async def step_nonblocking(self) -> ta.Optional[ta.Any]:
        return self._driver.next(read=False)

    async def block_output(self) -> None:
        pass

    async def release_output(self) -> None:
        if self._driver.has_pending_output:
            self._output.extend(self._driver.drain_output())

    def take_output(self) -> bytes:
        out = bytes(self._output)
        self._output.clear()
        return out

    async def close(self) -> None:
        self._driver.close()


##


class TestIoPipelineDriverConformance(AsyncioIsolatedAsyncTestCase):
    ADAPTER_TYPES: ta.Tuple[ta.Type[_ConformanceDriverAdapter], ...] = (
        _SyncConformanceDriverAdapter,
        _AsyncioConformanceDriverAdapter,
        _FdioConformanceDriverAdapter,
        _PureConformanceDriverAdapter,
    )

    async def _with_adapters(
            self,
            fn: ta.Callable[[_ConformanceDriverAdapter], ta.Awaitable[None]],
            *,
            manual_input: bool = False,
            explicit_auto_input: bool = False,
            output_after_final_input: ta.Optional[bytes] = None,
            read_chunk_size: int = 64 * 1024,
            read_batch_max_bytes: int = 1024 * 1024,
            read_batch_max_reads: int = 16,
    ) -> None:
        for adapter_type in self.ADAPTER_TYPES:
            with self.subTest(driver=adapter_type.NAME):
                handler = _ConformanceIoPipelineHandler(output_after_final_input=output_after_final_input)
                adapter = adapter_type(
                    handler,
                    manual_input=manual_input,
                    explicit_auto_input=explicit_auto_input,
                    read_chunk_size=read_chunk_size,
                    read_batch_max_bytes=read_batch_max_bytes,
                    read_batch_max_reads=read_batch_max_reads,
                )
                try:
                    await fn(adapter)
                finally:
                    await adapter.close()

    async def test_initial_input_precedes_transport_input(self) -> None:
        async def run(adapter: _ConformanceDriverAdapter) -> None:
            self.assertIs(adapter.state, IoPipelineDriverState.NEW)
            await adapter.start()
            self.assertIs(adapter.state, IoPipelineDriverState.RUNNING)

            observed = await adapter.feed_input(b'input')

            self.assertIsInstance(observed, _ObservedInput)
            self.assertEqual(observed.msg, b'input')
            self.assertIsInstance(adapter.handler.inputs[0], IoPipelineMessages.InitialInput)
            self.assertEqual(adapter.handler.inputs[1], b'input')

        await self._with_adapters(run)

    async def test_read_false_is_a_non_waiting_step(self) -> None:
        async def run(adapter: _ConformanceDriverAdapter) -> None:
            await adapter.start()
            self.assertIsNone(await adapter.step_nonblocking())
            self.assertIs(adapter.state, IoPipelineDriverState.RUNNING)

        await self._with_adapters(run)

    async def test_manual_input_tokens_are_one_shot(self) -> None:
        async def run(adapter: _ConformanceDriverAdapter) -> None:
            await adapter.start()
            self.assertIsNone(await adapter.enqueue(_RequestInput()))
            first = await adapter.feed_input(b'first')
            self.assertEqual(first, _ObservedInput(b'first'))

            self.assertIsNone(await adapter.enqueue(_RequestInput()))
            second = await adapter.feed_input(b'second')
            self.assertEqual(second, _ObservedInput(b'second'))
            self.assertIsNone(await adapter.step_nonblocking())

            self.assertEqual(
                [msg for msg in adapter.handler.inputs if isinstance(msg, bytes)],
                [b'first', b'second'],
            )
            self.assertEqual(
                sum(isinstance(msg, IoPipelineFlowMessages.FlushInput) for msg in adapter.handler.inputs),
                2,
            )

        await self._with_adapters(run, manual_input=True)

    async def test_manual_input_token_reads_one_bounded_batch(self) -> None:
        async def run(adapter: _ConformanceDriverAdapter) -> None:
            await adapter.start()
            self.assertIsNone(await adapter.enqueue(_RequestInput()))

            self.assertIsInstance(await adapter.feed_input(b'abcdef'), _ObservedInput)
            while await adapter.step_nonblocking() is not None:
                pass

            input_bytes = [msg for msg in adapter.handler.inputs if isinstance(msg, bytes)]
            self.assertEqual(b''.join(input_bytes), b'abcd')
            self.assertEqual(
                sum(isinstance(msg, IoPipelineFlowMessages.FlushInput) for msg in adapter.handler.inputs),
                1,
            )
            self.assertIsNone(await adapter.step_nonblocking())

        await self._with_adapters(
            run,
            manual_input=True,
            read_chunk_size=2,
            read_batch_max_bytes=4,
            read_batch_max_reads=2,
        )

    async def test_explicit_auto_read_service_keeps_reading(self) -> None:
        async def run(adapter: _ConformanceDriverAdapter) -> None:
            await adapter.start()

            self.assertEqual(await adapter.feed_input(b'first'), _ObservedInput(b'first'))
            self.assertEqual(await adapter.feed_input(b'second'), _ObservedInput(b'second'))
            self.assertIsNone(await adapter.step_nonblocking())

            self.assertEqual(
                [msg for msg in adapter.handler.inputs if isinstance(msg, bytes)],
                [b'first', b'second'],
            )

        await self._with_adapters(run, explicit_auto_input=True)

    async def test_flush_completes_after_ordered_output_crosses_transport(self) -> None:
        async def run(adapter: _ConformanceDriverAdapter) -> None:
            await adapter.start()
            flush_output = IoPipelineFlowMessages.FlushOutput()

            self.assertIsNone(await adapter.enqueue(_Emit([b'ab', b'cd', flush_output])))
            await adapter.release_output()

            self.assertEqual(adapter.take_output(), b'abcd')
            self.assertTrue(flush_output.is_succeeded())

        await self._with_adapters(run)

    async def test_output_watermarks_are_edge_notified(self) -> None:
        async def run(adapter: _ConformanceDriverAdapter) -> None:
            await adapter.start()
            await adapter.block_output()
            flush_output = IoPipelineFlowMessages.FlushOutput()

            self.assertIsNone(await adapter.enqueue(_Emit([b'abcde', b'f', flush_output])))
            self.assertFalse(flush_output.is_done())
            self.assertEqual(
                [type(msg) for msg in adapter.handler.output_writability],
                [IoPipelineFlowMessages.PauseOutput],
            )

            await adapter.release_output()

            self.assertTrue(flush_output.is_succeeded())
            self.assertEqual(
                [type(msg) for msg in adapter.handler.output_writability],
                [IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput],
            )

        await self._with_adapters(run, manual_input=True)

    async def test_final_input_is_only_an_input_half_close(self) -> None:
        async def run(adapter: _ConformanceDriverAdapter) -> None:
            await adapter.start()

            observed = await adapter.feed_eof()
            self.assertIsInstance(observed, _ObservedInput)
            self.assertIsInstance(observed.msg, IoPipelineMessages.FinalInput)
            await adapter.release_output()

            self.assertEqual(adapter.take_output(), b'after-eof')
            self.assertIs(adapter.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(adapter.pipeline.is_ready)
            self.assertFalse(adapter.pipeline.saw_final_output)

        await self._with_adapters(run, output_after_final_input=b'after-eof')

    async def test_final_output_gracefully_drains_and_closes(self) -> None:
        async def run(adapter: _ConformanceDriverAdapter) -> None:
            await adapter.start()
            final_output = IoPipelineMessages.FinalOutput()

            self.assertIsNone(await adapter.enqueue(_Emit([b'payload', final_output])))
            await adapter.release_output()

            self.assertEqual(adapter.take_output(), b'payload')
            self.assertTrue(final_output.is_succeeded())
            self.assertIs(adapter.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(adapter.pipeline.is_ready)

        await self._with_adapters(run)

    async def test_close_is_abortive_for_pending_completables(self) -> None:
        async def run(adapter: _ConformanceDriverAdapter) -> None:
            await adapter.start()
            await adapter.block_output()
            flush_output = IoPipelineFlowMessages.FlushOutput()
            completion_errors: ta.List[ta.Optional[BaseException]] = []
            flush_output.add_listener(lambda msg: completion_errors.append(msg.get_exception()))
            self.assertIsNone(await adapter.enqueue(_Emit([b'payload', flush_output])))
            self.assertFalse(flush_output.is_done())

            await adapter.close()

            self.assertIs(adapter.state, IoPipelineDriverState.CLOSED)
            self.assertTrue(flush_output.is_failed())
            self.assertEqual(len(completion_errors), 1)
            self.assertIsInstance(completion_errors[0], AbortedIoPipelineError)

        await self._with_adapters(run, manual_input=True)

    async def test_due_timer_runs_without_a_waiting_read(self) -> None:
        marker = object()

        async def run(adapter: _ConformanceDriverAdapter) -> None:
            await adapter.start()
            out = await adapter.enqueue(_TimerOutput(0., marker))

            if out is None:
                out = await adapter.step_nonblocking()
            self.assertIs(out, marker)

        await self._with_adapters(run, manual_input=True)
