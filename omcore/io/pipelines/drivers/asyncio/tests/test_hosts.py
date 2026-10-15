# ruff: noqa: SLF001 UP006 UP007 UP037 UP045
# @om-lite
import asyncio
import fcntl
import os
import socket
import tempfile
import tty
import typing as ta

from ......sockets.endpoints import TcpSocketEndpoint
from ......testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from .....streambufs.utils import ByteStreamBuffers
from ....core import IoPipeline
from ....core import IoPipelineHandler
from ....core import IoPipelineHandlerContext
from ....core import IoPipelineMessages
from ....errors import UnsupportedIoPipelineError
from ....hosts.base import BlockingIoPipelineHostResolver
from ....hosts.types import IoPipelineHostedDriver
from ...types import IoPipelineDriverState
from ..hosts import AsyncioHostedIoPipelineDriver
from ..hosts import AsyncioIoPipelineHost
from ..hosts import LoopAsyncioIoPipelineHostResolver
from ..hosts import SyncAsyncioIoPipelineHostResolver


##


class _Emit(IoPipelineMessages.AfterFinalInput):
    def __init__(self, *msgs: ta.Any) -> None:
        super().__init__()

        self.msgs = msgs


class _UpperEchoApp(IoPipelineHandler):
    def __init__(self, *, echo: bool = True) -> None:
        super().__init__()

        self._echo = echo
        self.received = bytearray()
        self.errors: ta.List[BaseException] = []
        self.saw_final_input = False

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Emit):
            for m in msg.msgs:
                ctx.feed_out(m)
            return
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True
            ctx.feed_in(msg)
            ctx.feed_final_output()
            return
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            return
        if ByteStreamBuffers.can_bytes(msg):
            data = ByteStreamBuffers.to_bytes(msg, strict=True)
            self.received.extend(data)
            if self._echo:
                ctx.feed_out(data.upper())
            return
        if isinstance(msg, IoPipelineMessages.MayPropagate):
            ctx.feed_in(msg)


async def _until(cond: ta.Callable[[], bool], timeout_s: float = 5.) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    for _ in range(100_000):
        if cond():
            return
        if loop.time() > deadline:
            break
        await asyncio.sleep(.001)
    raise TimeoutError('condition not reached')


async def _read_available(fd: int, timeout_s: float = 5.) -> bytes:
    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()

    def ready() -> None:
        if not fut.done():
            fut.set_result(None)

    loop.add_reader(fd, ready)
    try:
        await asyncio.wait_for(fut, timeout_s)
    finally:
        loop.remove_reader(fd)
    return os.read(fd, 65536)


def _is_nonblocking(fd: int) -> bool:
    return bool(fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_NONBLOCK)


def _enqueue(handle: IoPipelineHostedDriver, *msgs: ta.Any) -> None:
    ta.cast(ta.Any, ta.cast(AsyncioHostedIoPipelineDriver, handle).driver).enqueue(*msgs)


def _outcome(msg: IoPipelineMessages.Completable) -> ta.List[ta.Optional[BaseException]]:
    out: ta.List[ta.Optional[BaseException]] = []
    msg.add_listener(lambda m: out.append(m.get_exception() if m.is_failed() else None))
    return out


class TestAsyncioIoPipelineHostAdoption(AsyncioIsolatedAsyncTestCase):
    async def test_adopts_a_caller_owned_socket_without_closing_it(self) -> None:
        host = AsyncioIoPipelineHost()
        a, b = socket.socketpair()
        try:
            echo = _UpperEchoApp()
            handle = host.adopt(a, IoPipeline.Spec([echo]))
            await ta.cast(AsyncioHostedIoPipelineDriver, handle).wait_started()
            self.assertIs(handle.state, IoPipelineDriverState.RUNNING)

            b.setblocking(False)
            b.sendall(b'hi')
            await _until(lambda: bytes(echo.received) == b'hi')
            self.assertEqual(await _read_available(b.fileno()), b'HI')

            handle.close()
            await ta.cast(AsyncioHostedIoPipelineDriver, handle).wait_closed()
            os.fstat(a.fileno())
            self.assertIsNone(a.gettimeout())
            self.assertFalse(_is_nonblocking(a.fileno()))
        finally:
            host.close()
            await host.wait_closed()
            a.close()
            b.close()

    async def test_closing_an_owned_adoption_before_its_task_runs_closes_the_socket(self) -> None:
        """An owned socket is the host's to close from the adoption on - even one whose task never got to run."""

        host = AsyncioIoPipelineHost()
        a, b = socket.socketpair()
        try:
            hosted = ta.cast(AsyncioHostedIoPipelineDriver, host.adopt(a, IoPipeline.Spec([_UpperEchoApp()]), owned=True))  # noqa
            hosted.close()
            await hosted.wait_closed()
            await host.wait_closed()

            self.assertTrue(hosted.closed)
            self.assertEqual(a.fileno(), -1)
        finally:
            host.close()
            await host.wait_closed()
            a.close()
            b.close()

    async def test_closing_an_owned_descriptor_adoption_before_its_task_runs_closes_the_descriptors(self) -> None:
        host = AsyncioIoPipelineHost()
        r, w = os.pipe()
        try:
            hosted = ta.cast(AsyncioHostedIoPipelineDriver, host.adopt((r, w), IoPipeline.Spec(), owned=True))
            hosted.close()
            await hosted.wait_closed()
            await host.wait_closed()

            self.assertTrue(hosted.closed)
            for fd in (r, w):
                with self.assertRaises(OSError):
                    os.fstat(fd)
        finally:
            host.close()
            await host.wait_closed()

    async def test_failed_descriptor_start_closes_each_duplicate_once(self) -> None:
        """
        A descriptor pair which cannot be served - a regular file is no pipe transport - is released with each
        duplicate closed exactly once: a number closed early and then again later, by a transport's own deferred close,
        would close whatever had reused it in between.
        """

        host = AsyncioIoPipelineHost()
        r, w = os.pipe()
        try:
            with tempfile.TemporaryFile() as f:
                hosted = ta.cast(AsyncioHostedIoPipelineDriver, host.adopt((r, f.fileno()), IoPipeline.Spec()))
                with self.assertRaises(ValueError):
                    await hosted.wait_started()
                await hosted.wait_closed()
                self.assertTrue(hosted.closed)

                # Whatever takes the duplicates' freed numbers now must survive the deferred closes.
                probe_r, probe_w = os.pipe()
                try:
                    for _ in range(5):
                        await asyncio.sleep(0)
                    os.fstat(probe_r)
                    os.fstat(probe_w)
                finally:
                    os.close(probe_r)
                    os.close(probe_w)

            # The caller's descriptors are intact, and back in blocking mode.
            os.fstat(r)
            self.assertFalse(fcntl.fcntl(r, fcntl.F_GETFL) & os.O_NONBLOCK)
        finally:
            host.close()
            await host.wait_closed()
            os.close(r)
            os.close(w)

    async def test_owned_pipe_pair_half_closes_by_closing_the_write_end(self) -> None:
        host = AsyncioIoPipelineHost()
        in_r, in_w = os.pipe()
        out_r, out_w = os.pipe()
        try:
            app = _UpperEchoApp(echo=False)
            handle = host.adopt((in_r, out_w), IoPipeline.Spec([app]), owned=True)
            await ta.cast(AsyncioHostedIoPipelineDriver, handle).wait_started()

            shutdown_output = IoPipelineMessages.ShutdownOutput()
            _enqueue(handle, _Emit(b'request', shutdown_output))
            await _until(lambda: shutdown_output.is_done())

            self.assertTrue(shutdown_output.is_succeeded())
            self.assertEqual(await _read_available(out_r), b'request')
            self.assertEqual(await _read_available(out_r), b'')

            os.write(in_w, b'response')
            await _until(lambda: bytes(app.received) == b'response')
            os.close(in_w)
            await _until(lambda: handle.closed)
            self.assertTrue(app.saw_final_input)
            self.assertEqual(app.errors, [])
        finally:
            host.close()
            await host.wait_closed()
            for fd in (in_w, out_r):
                try:
                    os.close(fd)
                except OSError:
                    pass

    async def test_caller_owned_pipe_pair_cannot_half_close_and_is_restored(self) -> None:
        host = AsyncioIoPipelineHost()
        in_r, in_w = os.pipe()
        out_r, out_w = os.pipe()
        try:
            app = _UpperEchoApp()
            handle = host.adopt((in_r, out_w), IoPipeline.Spec([app]))
            await ta.cast(AsyncioHostedIoPipelineDriver, handle).wait_started()
            self.assertTrue(_is_nonblocking(in_r))

            os.write(in_w, b'hello')
            await _until(lambda: bytes(app.received) == b'hello')
            self.assertEqual(await _read_available(out_r), b'HELLO')

            shutdown_output = IoPipelineMessages.ShutdownOutput()
            outcome = _outcome(shutdown_output)
            _enqueue(handle, _Emit(shutdown_output))
            await _until(lambda: shutdown_output.is_done())
            self.assertTrue(shutdown_output.is_failed())
            self.assertIsInstance(outcome[0], UnsupportedIoPipelineError)

            handle.close()
            await ta.cast(AsyncioHostedIoPipelineDriver, handle).wait_closed()
            os.fstat(in_r)
            os.fstat(out_w)
            self.assertFalse(_is_nonblocking(in_r))
            self.assertFalse(_is_nonblocking(out_w))
        finally:
            host.close()
            await host.wait_closed()
            for fd in (in_r, in_w, out_r, out_w):
                try:
                    os.close(fd)
                except OSError:
                    pass

    async def test_duplex_terminal_master(self) -> None:
        host = AsyncioIoPipelineHost()
        master, slave = os.openpty()
        try:
            tty.setraw(slave)
            app = _UpperEchoApp()
            handle = host.adopt(master, IoPipeline.Spec([app]))
            await ta.cast(AsyncioHostedIoPipelineDriver, handle).wait_started()

            os.write(slave, b'tty')
            await _until(lambda: bytes(app.received) == b'tty')
            self.assertEqual(await _read_available(slave), b'TTY')

            shutdown_output = IoPipelineMessages.ShutdownOutput()
            outcome = _outcome(shutdown_output)
            _enqueue(handle, _Emit(shutdown_output))
            await _until(lambda: shutdown_output.is_done())
            self.assertIsInstance(outcome[0], UnsupportedIoPipelineError)

            handle.close()
            await ta.cast(AsyncioHostedIoPipelineDriver, handle).wait_closed()
            os.fstat(master)
            self.assertFalse(_is_nonblocking(master))
        finally:
            host.close()
            await host.wait_closed()
            os.close(master)
            os.close(slave)


class TestAsyncioIoPipelineHostResolution(AsyncioIsolatedAsyncTestCase):
    async def test_loop_resolver(self) -> None:
        addrs = await LoopAsyncioIoPipelineHostResolver().resolve('127.0.0.1', 80)
        self.assertEqual(addrs[0][3][:2], ('127.0.0.1', 80))

    async def test_sync_resolver_is_adapted(self) -> None:
        addrs = await SyncAsyncioIoPipelineHostResolver(BlockingIoPipelineHostResolver()).resolve('127.0.0.1', 81)
        self.assertEqual(addrs[0][3][:2], ('127.0.0.1', 81))

    async def test_host_name_is_resolved_for_a_connect(self) -> None:
        host = AsyncioIoPipelineHost()
        try:
            with socket.create_server(('127.0.0.1', 0)) as listener:
                port = listener.getsockname()[1]
                connected: ta.List[IoPipelineHostedDriver] = []
                failed: ta.List[BaseException] = []
                host.connect(
                    TcpSocketEndpoint('localhost', port),
                    lambda info: IoPipeline.Spec([_UpperEchoApp()]),
                    on_connected=lambda c, h: connected.append(h),
                    on_failed=lambda c, e: failed.append(e),
                    timeout_s=5.,
                )
                await _until(lambda: bool(connected or failed))
                self.assertEqual(failed, [])
                self.assertIs(connected[0].state, IoPipelineDriverState.RUNNING)
        finally:
            host.close()
            await host.wait_closed()


class TestAsyncioIoPipelineHostTasks(AsyncioIsolatedAsyncTestCase):
    async def test_one_task_per_hosted_pipeline(self) -> None:
        host = AsyncioIoPipelineHost()
        try:
            before = len(asyncio.all_tasks())
            accepted: ta.List[IoPipelineHostedDriver] = []
            connected: ta.List[IoPipelineHostedDriver] = []
            listener = host.listen(
                TcpSocketEndpoint('127.0.0.1', 0),
                lambda info: IoPipeline.Spec([_UpperEchoApp()]),
                on_accepted=lambda c, h: accepted.append(h),
            )
            for _ in range(3):
                host.connect(
                    listener.bound_endpoint,
                    lambda info: IoPipeline.Spec([_UpperEchoApp()]),
                    on_connected=lambda c, h: connected.append(h),
                    on_failed=lambda c, e: None,
                    timeout_s=5.,
                )
            await _until(lambda: len(accepted) == 3 and len(connected) == 3)

            # Three connections and three accepted peers: six pipelines, each its driving task plus the driver's own
            # two long-lived tasks (reading and draining), and nothing else.
            self.assertEqual(len(asyncio.all_tasks()), before + 6 * 3)
        finally:
            host.close()
            await host.wait_closed()
