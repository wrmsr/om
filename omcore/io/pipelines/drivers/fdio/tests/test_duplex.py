# ruff: noqa: SLF001 UP006 UP007 UP037 UP045
# @om-lite
import fcntl
import os
import select
import socket
import tty
import unittest

from .....fdio.manager import FdioManager
from .....fdio.pollers import SelectFdioPoller
from ....core import IoPipeline
from ....core import IoPipelineMessages
from ....errors import UnsupportedIoPipelineError
from ...types import IoPipelineDriverState
from ..duplex import IoPipelineDriverDuplexFdioHandler
from .test_pairs import _Emit
from .test_pairs import _is_nonblocking
from .test_pairs import _outcome
from .test_pairs import _poll_until
from .test_pairs import _read_available
from .test_pairs import _UpperEchoApp


##


class TestIoPipelineDriverDuplexFdioHandler(unittest.TestCase):
    def test_echo_over_a_terminal_master(self) -> None:
        master, slave = os.openpty()
        try:
            # Raw mode: no echo, no line buffering, so bytes cross the terminal unchanged.
            tty.setraw(slave)
            app = _UpperEchoApp()
            drv = IoPipelineDriverDuplexFdioHandler(master, IoPipeline.Spec([app]))
            manager = FdioManager(SelectFdioPoller())
            try:
                self.assertIsNone(drv.next(read=False))
                manager.register(drv)
                self.assertTrue(_is_nonblocking(master))

                os.write(slave, b'hello')
                _poll_until(manager, lambda: bytes(app.received) == b'hello')
                self.assertEqual(_read_available(slave), b'HELLO')

                os.write(slave, b'more')
                _poll_until(manager, lambda: bytes(app.received) == b'hellomore')
                self.assertEqual(_read_available(slave), b'MORE')
                self.assertEqual(app.errors, [])
            finally:
                drv.close()

            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(_is_nonblocking(master))
            os.fstat(master)
        finally:
            os.close(master)
            os.close(slave)

    def test_shutdown_on_a_terminal_master_fails_and_leaves_it_intact(self) -> None:
        master, slave = os.openpty()
        try:
            tty.setraw(slave)
            app = _UpperEchoApp(echo=False)
            drv = IoPipelineDriverDuplexFdioHandler(master, IoPipeline.Spec([app]))
            manager = FdioManager(SelectFdioPoller())
            try:
                self.assertIsNone(drv.next(read=False))
                manager.register(drv)

                shutdown_output = IoPipelineMessages.ShutdownOutput()
                outcome = _outcome(shutdown_output)
                drv.enqueue(_Emit(b'out', shutdown_output))
                _poll_until(manager, lambda: shutdown_output.is_done())

                self.assertTrue(shutdown_output.is_failed())
                self.assertIsInstance(outcome[0], UnsupportedIoPipelineError)
                self.assertFalse(drv.output_shutdown)
                self.assertEqual(_read_available(slave), b'out')

                # The terminal is intact and input keeps arriving.
                os.write(slave, b'more')
                _poll_until(manager, lambda: bytes(app.received) == b'more')
                self.assertEqual(app.errors, [])
                self.assertFalse(drv.closed)
            finally:
                drv.close()
            os.fstat(master)
        finally:
            os.close(master)
            os.close(slave)

    def test_socket_by_number_half_closes_and_keeps_reading(self) -> None:
        sock, peer = socket.socketpair()
        try:
            app = _UpperEchoApp(echo=False)
            drv = IoPipelineDriverDuplexFdioHandler(sock.fileno(), IoPipeline.Spec([app]))
            manager = FdioManager(SelectFdioPoller())
            try:
                self.assertIsNone(drv.next(read=False))
                manager.register(drv)

                shutdown_output = IoPipelineMessages.ShutdownOutput()
                drv.enqueue(_Emit(b'request', shutdown_output))
                _poll_until(manager, lambda: shutdown_output.is_done())

                self.assertTrue(shutdown_output.is_succeeded())
                self.assertTrue(drv.output_shutdown)
                peer.settimeout(5.)
                self.assertEqual(peer.recv(64), b'request')
                self.assertEqual(peer.recv(64), b'')

                # The caller's descriptor stays open, and the read half still works.
                os.fstat(sock.fileno())
                peer.sendall(b'response')
                peer.shutdown(socket.SHUT_WR)
                _poll_until(manager, lambda: drv.closed)
                self.assertEqual(bytes(app.received), b'response')
                self.assertTrue(app.saw_final_input)
                self.assertEqual(app.errors, [])
                self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            finally:
                drv.close()
            os.fstat(sock.fileno())
            self.assertFalse(_is_nonblocking(sock.fileno()))
        finally:
            sock.close()
            peer.close()

    def test_owned_descriptor_is_closed_on_close(self) -> None:
        master, slave = os.openpty()
        try:
            drv = IoPipelineDriverDuplexFdioHandler(master, IoPipeline.Spec([_UpperEchoApp()]), owned=True)
            self.assertIsNone(drv.next(read=False))

            drv.close()

            with self.assertRaises(OSError):
                os.fstat(master)
            self.assertTrue(drv.closed)
        finally:
            try:
                os.close(master)
            except OSError:
                pass
            os.close(slave)

    def test_reads_and_writes_through_one_registration(self) -> None:
        a, b = socket.socketpair()
        try:
            app = _UpperEchoApp()
            drv = IoPipelineDriverDuplexFdioHandler(a.fileno(), IoPipeline.Spec([app]))
            manager = FdioManager(SelectFdioPoller())
            try:
                self.assertIsNone(drv.next(read=False))
                manager.register(drv)
                self.assertEqual(drv.fd(), a.fileno())

                b.sendall(b'abc')
                _poll_until(manager, lambda: bytes(app.received) == b'abc')
                r, _, _ = select.select([b], [], [], 5.)
                self.assertTrue(r)
                self.assertEqual(b.recv(64), b'ABC')
            finally:
                drv.close()
            self.assertFalse(bool(fcntl.fcntl(a.fileno(), fcntl.F_GETFL) & os.O_NONBLOCK))
        finally:
            a.close()
            b.close()
