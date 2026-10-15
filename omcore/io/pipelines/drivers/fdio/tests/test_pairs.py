# ruff: noqa: SLF001 UP006 UP007 UP037 UP045
# @om-lite
import fcntl
import os
import select
import time
import typing as ta
import unittest

from .....fdio.manager import FdioManager
from .....fdio.pollers import SelectFdioPoller
from .....streambufs.utils import ByteStreamBuffers
from ....core import IoPipeline
from ....core import IoPipelineHandler
from ....core import IoPipelineHandlerContext
from ....core import IoPipelineMessages
from ....errors import UnsupportedIoPipelineError
from ....posting.types import IoPipelinePosting
from ...types import IoPipelineDriverState
from ..pairs import IoPipelineDriverFdPairFdioHandlers


##


class _Emit(IoPipelineMessages.AfterFinalInput):
    def __init__(self, *msgs: ta.Any) -> None:
        super().__init__()

        self.msgs = msgs


class _UpperEchoApp(IoPipelineHandler):
    """Echoes uppercased input back out, closes output on EOF, records errors, and emits what it is told to."""

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

        ctx.feed_in(msg)


class _Pipes:
    """Two pipes: the driver reads from `in` and writes to `out`; the test does the reverse."""

    def __init__(self) -> None:
        self.in_r, self.in_w = os.pipe()
        self.out_r, self.out_w = os.pipe()

    def close(self) -> None:
        for fd in (self.in_r, self.in_w, self.out_r, self.out_w):
            try:
                os.close(fd)
            except OSError:
                pass


def _read_available(fd: int, timeout_s: float = 5.) -> bytes:
    r, _, _ = select.select([fd], [], [], timeout_s)
    if not r:
        raise TimeoutError
    return os.read(fd, 65536)


def _is_nonblocking(fd: int) -> bool:
    return bool(fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_NONBLOCK)


def _outcome(msg: IoPipelineMessages.Completable) -> ta.List[ta.Optional[BaseException]]:
    out: ta.List[ta.Optional[BaseException]] = []
    msg.add_listener(lambda m: out.append(m.get_exception() if m.is_failed() else None))
    return out


def _poll_until(manager: FdioManager, cond: ta.Callable[[], bool], *, rounds: int = 100) -> None:
    for _ in range(rounds):
        if cond():
            return
        manager.poll(timeout=5.)
    raise RuntimeError('condition not reached')


class TestIoPipelineDriverFdPairFdioHandlers(unittest.TestCase):
    def test_echo_over_pipes_through_manager(self) -> None:
        pipes = _Pipes()
        try:
            app = _UpperEchoApp()
            pair = IoPipelineDriverFdPairFdioHandlers(pipes.in_r, pipes.out_w, IoPipeline.Spec([app]))
            manager = FdioManager(SelectFdioPoller())
            try:
                self.assertIsNone(pair.next(read=False))
                pair.register(manager)
                self.assertTrue(_is_nonblocking(pipes.in_r))
                self.assertTrue(_is_nonblocking(pipes.out_w))

                os.write(pipes.in_w, b'hello')
                _poll_until(manager, lambda: bytes(app.received) == b'hello')
                self.assertEqual(_read_available(pipes.out_r), b'HELLO')

                os.close(pipes.in_w)
                _poll_until(manager, lambda: pair.closed)

                self.assertTrue(app.saw_final_input)
                self.assertEqual(app.errors, [])
                self.assertIs(pair.state, IoPipelineDriverState.CLOSED)
                self.assertTrue(pair.read_handler.closed)
                self.assertTrue(pair.write_handler.closed)
            finally:
                pair.close()

            # Caller-owned: restored to blocking and still open.
            self.assertFalse(_is_nonblocking(pipes.in_r))
            self.assertFalse(_is_nonblocking(pipes.out_w))
            os.fstat(pipes.in_r)
            os.fstat(pipes.out_w)
        finally:
            pipes.close()

    def test_output_shutdown_closes_the_write_fd_when_permitted(self) -> None:
        pipes = _Pipes()
        try:
            app = _UpperEchoApp(echo=False)
            pair = IoPipelineDriverFdPairFdioHandlers(
                pipes.in_r,
                pipes.out_w,
                IoPipeline.Spec([app]),
                close_write_fd_on_output_shutdown=True,
            )
            manager = FdioManager(SelectFdioPoller())
            try:
                self.assertIsNone(pair.next(read=False))
                pair.register(manager)

                shutdown_output = IoPipelineMessages.ShutdownOutput()
                pair.enqueue(_Emit(b'request', shutdown_output))
                _poll_until(manager, lambda: shutdown_output.is_done())

                self.assertTrue(shutdown_output.is_succeeded())
                self.assertTrue(pair.output_shutdown)
                self.assertEqual(_read_available(pipes.out_r), b'request')
                self.assertEqual(_read_available(pipes.out_r), b'')
                with self.assertRaises(OSError):
                    os.fstat(pipes.out_w)
                self.assertTrue(pair.write_handler.closed)
                self.assertFalse(pair.read_handler.closed)
                self.assertFalse(pair.closed)

                # Reading continues.
                os.write(pipes.in_w, b'response')
                _poll_until(manager, lambda: bytes(app.received) == b'response')
                os.close(pipes.in_w)
                _poll_until(manager, lambda: pair.closed)
                self.assertTrue(app.saw_final_input)
                self.assertEqual(app.errors, [])
            finally:
                pair.close()
            self.assertFalse(_is_nonblocking(pipes.in_r))
        finally:
            pipes.close()

    def test_output_shutdown_on_caller_owned_pipe_fails_and_leaves_it_intact(self) -> None:
        pipes = _Pipes()
        try:
            app = _UpperEchoApp(echo=False)
            pair = IoPipelineDriverFdPairFdioHandlers(pipes.in_r, pipes.out_w, IoPipeline.Spec([app]))
            manager = FdioManager(SelectFdioPoller())
            try:
                self.assertIsNone(pair.next(read=False))
                pair.register(manager)

                shutdown_output = IoPipelineMessages.ShutdownOutput()
                outcome = _outcome(shutdown_output)
                pair.enqueue(_Emit(b'request', shutdown_output))
                _poll_until(manager, lambda: shutdown_output.is_done())

                self.assertTrue(shutdown_output.is_failed())
                self.assertIsInstance(outcome[0], UnsupportedIoPipelineError)
                self.assertFalse(pair.output_shutdown)
                self.assertEqual(_read_available(pipes.out_r), b'request')
                os.fstat(pipes.out_w)
                self.assertFalse(pair.write_handler.closed)

                # Still a working transport: input keeps arriving. (The pipeline itself rejects ordinary output after
                # a ShutdownOutput reached its terminal, whatever the transport made of it.)
                os.write(pipes.in_w, b'more')
                _poll_until(manager, lambda: bytes(app.received) == b'more')
                self.assertEqual(app.errors, [])
                os.close(pipes.in_w)
                _poll_until(manager, lambda: pair.closed)
                self.assertIs(pair.state, IoPipelineDriverState.CLOSED)
            finally:
                pair.close()
            os.fstat(pipes.out_w)
        finally:
            pipes.close()

    def test_closing_one_handler_closes_both(self) -> None:
        pipes = _Pipes()
        try:
            pair = IoPipelineDriverFdPairFdioHandlers(pipes.in_r, pipes.out_w, IoPipeline.Spec([_UpperEchoApp()]))
            self.assertIsNone(pair.next(read=False))
            self.assertTrue(_is_nonblocking(pipes.in_r))

            pair.read_handler.close()

            self.assertTrue(pair.closed)
            self.assertTrue(pair.write_handler.closed)
            self.assertIs(pair.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(pair.pipeline.is_ready)
            self.assertFalse(_is_nonblocking(pipes.in_r))
            self.assertFalse(_is_nonblocking(pipes.out_w))
            os.fstat(pipes.in_r)
            os.fstat(pipes.out_w)
        finally:
            pipes.close()

    def test_owned_descriptors_are_closed_on_close(self) -> None:
        pipes = _Pipes()
        try:
            pair = IoPipelineDriverFdPairFdioHandlers(
                pipes.in_r,
                pipes.out_w,
                IoPipeline.Spec([_UpperEchoApp()]),
                owned=True,
            )
            self.assertIsNone(pair.next(read=False))

            pair.close()

            with self.assertRaises(OSError):
                os.fstat(pipes.in_r)
            with self.assertRaises(OSError):
                os.fstat(pipes.out_w)
        finally:
            pipes.close()

    def test_post_wakes_the_manager(self) -> None:
        pipes = _Pipes()
        try:
            pair = IoPipelineDriverFdPairFdioHandlers(pipes.in_r, pipes.out_w, IoPipeline.Spec([_UpperEchoApp()]))
            manager = FdioManager(SelectFdioPoller())
            try:
                self.assertIsNone(pair.next(read=False))
                pair.register(manager)
                self.assertIsNone(pair.read_handler.next_deadline())

                ran: ta.List[int] = []
                post = pair.pipeline.services[IoPipelinePosting].post(lambda: ran.append(1))
                self.assertLessEqual(ta.cast(float, pair.read_handler.next_deadline()), time.monotonic())

                started = time.monotonic()
                manager.poll(timeout=5.)

                self.assertLess(time.monotonic() - started, 2.)
                self.assertEqual(ran, [1])
                self.assertTrue(post.is_succeeded())
                self.assertIsNone(pair.read_handler.next_deadline())
            finally:
                pair.close()
        finally:
            pipes.close()
