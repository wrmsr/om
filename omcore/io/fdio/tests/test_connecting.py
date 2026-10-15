# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import errno
import socket
import time
import typing as ta
import unittest

from ..connecting import ConnectingSocketFdioHandler
from ..connecting import FdioConnectAddress
from ..connecting import FdioConnectClosedError
from ..connecting import FdioConnectError
from ..connecting import FdioConnectTimeoutError
from ..manager import FdioManager
from ..pollers import SelectFdioPoller


##


def _tcp(port: int) -> FdioConnectAddress:
    return (socket.AF_INET, socket.SOCK_STREAM, 0, ('127.0.0.1', port))


def _refused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class _Outcome:
    def __init__(self) -> None:
        self.connected: ta.Optional[socket.socket] = None
        self.failed: ta.Optional[FdioConnectError] = None

    def on_connected(self, sock: socket.socket) -> None:
        self.connected = sock

    def on_failed(self, exc: FdioConnectError) -> None:
        self.failed = exc

    @property
    def done(self) -> bool:
        return self.connected is not None or self.failed is not None

    def close(self) -> None:
        if self.connected is not None:
            self.connected.close()


def _poll_until(manager: FdioManager, cond: ta.Callable[[], bool]) -> float:
    started = time.monotonic()
    for _ in range(100):
        if cond():
            return time.monotonic() - started
        manager.poll(timeout=5.)
    raise RuntimeError('condition not reached')


class _FullListener:
    """A listener whose backlog is full, so further connection attempts stay in progress: never accepted or refused."""

    def __init__(self) -> None:
        self.sock = socket.create_server(('127.0.0.1', 0), backlog=1)
        self.port = self.sock.getsockname()[1]
        self.fillers: ta.List[socket.socket] = []
        for _ in range(8):
            f = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            f.setblocking(False)
            f.connect_ex(('127.0.0.1', self.port))
            self.fillers.append(f)

    def close(self) -> None:
        for f in self.fillers:
            f.close()
        self.sock.close()


class TestConnectingSocketFdioHandler(unittest.TestCase):
    def test_connects(self) -> None:
        with socket.create_server(('127.0.0.1', 0)) as listener:
            port = listener.getsockname()[1]
            outcome = _Outcome()
            handler = ConnectingSocketFdioHandler([_tcp(port)], outcome.on_connected, outcome.on_failed, timeout_s=5.)
            manager = FdioManager(SelectFdioPoller())
            manager.register(handler)
            try:
                elapsed = _poll_until(manager, lambda: outcome.done)

                self.assertLess(elapsed, 4.)
                self.assertIsNone(outcome.failed)
                sock = outcome.connected
                if sock is None:
                    self.fail('not connected')
                self.assertEqual(sock.getpeername()[1], port)
                self.assertEqual(sock.gettimeout(), 0.)
                self.assertTrue(handler.closed)
                self.assertTrue(handler.done)
                accepted, _ = listener.accept()
                accepted.close()
            finally:
                outcome.close()
                handler.close()

    def test_refused_address_is_skipped_for_the_next(self) -> None:
        with socket.create_server(('127.0.0.1', 0)) as listener:
            port = listener.getsockname()[1]
            outcome = _Outcome()
            handler = ConnectingSocketFdioHandler(
                [_tcp(_refused_port()), _tcp(port)],
                outcome.on_connected,
                outcome.on_failed,
                timeout_s=5.,
            )
            manager = FdioManager(SelectFdioPoller())
            manager.register(handler)
            try:
                _poll_until(manager, lambda: outcome.done)

                self.assertIsNone(outcome.failed)
                self.assertIsNotNone(outcome.connected)
                self.assertEqual(len(handler.errors), 1)
                self.assertEqual(ta.cast(OSError, handler.errors[0]).errno, errno.ECONNREFUSED)
            finally:
                outcome.close()
                handler.close()

    def test_all_refused_fails(self) -> None:
        outcome = _Outcome()
        handler = ConnectingSocketFdioHandler([_tcp(_refused_port())], outcome.on_connected, outcome.on_failed)
        manager = FdioManager(SelectFdioPoller())
        manager.register(handler)
        try:
            _poll_until(manager, lambda: outcome.done)

            self.assertIsNone(outcome.connected)
            failed = outcome.failed
            if failed is None:
                self.fail('not failed')
            self.assertIsInstance(failed, FdioConnectError)
            self.assertNotIsInstance(failed, FdioConnectTimeoutError)
            self.assertEqual(len(failed.errors), 1)
            self.assertEqual(ta.cast(OSError, failed.errors[0]).errno, errno.ECONNREFUSED)
            self.assertTrue(handler.closed)
        finally:
            handler.close()

    def test_timeout_fails_the_attempt(self) -> None:
        full = _FullListener()
        try:
            outcome = _Outcome()
            handler = ConnectingSocketFdioHandler(
                [_tcp(full.port)],
                outcome.on_connected,
                outcome.on_failed,
                timeout_s=.05,
            )
            try:
                if not handler.writable():
                    self.skipTest('connect completed at once: backlog overflow not observable here')
                self.assertIsNotNone(handler.next_deadline())

                manager = FdioManager(SelectFdioPoller())
                manager.register(handler)
                elapsed = _poll_until(manager, lambda: outcome.done)

                self.assertLess(elapsed, 4.)
                failed = outcome.failed
                if failed is None:
                    self.fail('not failed')
                self.assertIsInstance(failed, FdioConnectTimeoutError)
                self.assertIsInstance(failed.errors[0], TimeoutError)
                self.assertTrue(handler.closed)
            finally:
                handler.close()
        finally:
            full.close()

    def test_close_while_connecting_reports_closed(self) -> None:
        full = _FullListener()
        try:
            outcome = _Outcome()
            handler = ConnectingSocketFdioHandler([_tcp(full.port)], outcome.on_connected, outcome.on_failed)
            if not handler.writable():
                self.skipTest('connect completed at once: backlog overflow not observable here')
            fd = handler.fd()

            handler.close()

            self.assertTrue(handler.closed)
            self.assertIsInstance(outcome.failed, FdioConnectClosedError)
            self.assertIsNone(outcome.connected)
            with self.assertRaises(OSError):
                socket.socket(fileno=fd).getsockname()
            handler.close()
        finally:
            full.close()
