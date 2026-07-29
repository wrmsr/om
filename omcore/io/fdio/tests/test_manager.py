# ruff: noqa: SLF001 UP006 UP007 UP045
import socket
import threading
import time
import typing as ta
import unittest

from ..handlers import ServerSocketFdioHandler
from ..handlers import SocketFdioHandler
from ..kqueue import KqueueFdioPoller
from ..manager import FdioManager
from ..pollers import FdioPoller
from ..pollers import PollFdioPoller
from ..pollers import SelectFdioPoller


##


def poller_types() -> ta.List[ta.Type[FdioPoller]]:
    return [
        SelectFdioPoller,
        *([PollFdioPoller] if PollFdioPoller is not None else []),
        *([KqueueFdioPoller] if KqueueFdioPoller is not None else []),
    ]


class TestSocketFdioHandler(SocketFdioHandler):
    __test__ = False

    def __init__(self, sock: socket.socket) -> None:
        sock.setblocking(False)
        super().__init__(sock)

        self.read_interest = False
        self.write_interest = False
        self.deadline: ta.Optional[float] = None

        self.events: ta.List[ta.Any] = []
        self.close_on_timeout = False
        self.timeout_callback: ta.Optional[ta.Callable[[], None]] = None

    def readable(self) -> bool:
        return self.read_interest

    def writable(self) -> bool:
        return self.write_interest

    def next_deadline(self) -> ta.Optional[float]:
        return self.deadline

    def on_readable(self) -> None:
        self.events.append(('read', ta.cast(socket.socket, self._sock).recv(1024)))

    def on_writable(self) -> None:
        self.events.append(('write', None))
        self.write_interest = False

    def on_timeout(self) -> None:
        self.events.append(('timeout', None))
        self.deadline = None
        if self.close_on_timeout:
            self.close()
        if self.timeout_callback is not None:
            self.timeout_callback()


class RecordingSelectFdioPoller(SelectFdioPoller):
    def __init__(self) -> None:
        super().__init__()

        self.timeouts: ta.List[ta.Optional[float]] = []

    def poll(self, timeout: ta.Optional[float]) -> FdioPoller.PollResult:
        self.timeouts.append(timeout)
        return super().poll(timeout)


class TestFdioManager(unittest.TestCase):
    def test_dispatches_readable_and_writable_events(self) -> None:
        for poller_type in poller_types():
            with self.subTest(poller_type=poller_type.__name__):
                sock, peer = socket.socketpair()
                poller = poller_type()
                handler = TestSocketFdioHandler(sock)
                handler.read_interest = True
                handler.write_interest = True
                manager = FdioManager(poller)
                manager.register(handler)
                try:
                    peer.sendall(b'hello')

                    manager.poll(timeout=.5)

                    self.assertEqual(
                        handler.events,
                        [
                            ('read', b'hello'),
                            ('write', None),
                        ],
                    )
                finally:
                    handler.close()
                    peer.close()
                    poller.close()

    def test_deadline_shortens_caller_timeout(self) -> None:
        for poller_type in poller_types():
            with self.subTest(poller_type=poller_type.__name__):
                sock, peer = socket.socketpair()
                poller = poller_type()
                handler = TestSocketFdioHandler(sock)
                handler.deadline = time.monotonic() + .02
                manager = FdioManager(poller)
                manager.register(handler)
                try:
                    start = time.monotonic()
                    manager.poll(timeout=.5)
                    elapsed = time.monotonic() - start

                    self.assertEqual(handler.events, [('timeout', None)])
                    self.assertGreaterEqual(elapsed, .005)
                    self.assertLess(elapsed, .3)
                finally:
                    handler.close()
                    peer.close()
                    poller.close()

    def test_caller_timeout_precedes_deadline(self) -> None:
        sock, peer = socket.socketpair()
        poller = SelectFdioPoller()
        handler = TestSocketFdioHandler(sock)
        handler.deadline = time.monotonic() + .5
        manager = FdioManager(poller)
        manager.register(handler)
        try:
            start = time.monotonic()
            manager.poll(timeout=.01)
            elapsed = time.monotonic() - start

            self.assertEqual(handler.events, [])
            self.assertGreaterEqual(elapsed, .005)
            self.assertLess(elapsed, .3)
        finally:
            handler.close()
            peer.close()
            poller.close()

    def test_io_before_deadline_does_not_fire_timeout(self) -> None:
        for poller_type in poller_types():
            with self.subTest(poller_type=poller_type.__name__):
                sock, peer = socket.socketpair()
                poller = poller_type()
                handler = TestSocketFdioHandler(sock)
                handler.read_interest = True
                handler.deadline = time.monotonic() + .5
                manager = FdioManager(poller)
                manager.register(handler)
                try:
                    peer.sendall(b'hello')

                    manager.poll(timeout=.5)

                    self.assertEqual(handler.events, [('read', b'hello')])
                    self.assertIsNotNone(handler.deadline)
                finally:
                    handler.close()
                    peer.close()
                    poller.close()

    def test_earliest_handler_deadline_wins(self) -> None:
        first_sock, first_peer = socket.socketpair()
        second_sock, second_peer = socket.socketpair()
        poller = SelectFdioPoller()
        first = TestSocketFdioHandler(first_sock)
        second = TestSocketFdioHandler(second_sock)
        first.deadline = time.monotonic() + .02
        second.deadline = time.monotonic() + .5
        manager = FdioManager(poller)
        manager.register(first)
        manager.register(second)
        try:
            manager.poll()

            self.assertEqual(first.events, [('timeout', None)])
            self.assertEqual(second.events, [])
        finally:
            first.close()
            first_peer.close()
            second.close()
            second_peer.close()
            poller.close()

    def test_default_poll_is_tickless_until_io(self) -> None:
        sock, peer = socket.socketpair()
        poller = RecordingSelectFdioPoller()
        handler = TestSocketFdioHandler(sock)
        handler.read_interest = True
        manager = FdioManager(poller)
        manager.register(handler)

        send_errors: ta.List[BaseException] = []

        def send_later() -> None:
            try:
                time.sleep(.02)
                peer.sendall(b'wakeup')
            except BaseException as exc:  # noqa
                send_errors.append(exc)

        thread = threading.Thread(target=send_later)
        thread.start()
        try:
            manager.poll()

            self.assertEqual(poller.timeouts, [None])
            self.assertEqual(handler.events, [('read', b'wakeup')])
            self.assertEqual(send_errors, [])
        finally:
            thread.join()
            handler.close()
            peer.close()
            poller.close()

    def test_timeout_callback_can_close_handler(self) -> None:
        sock, peer = socket.socketpair()
        poller = SelectFdioPoller()
        handler = TestSocketFdioHandler(sock)
        handler.deadline = time.monotonic()
        handler.close_on_timeout = True
        manager = FdioManager(poller)
        manager.register(handler)
        try:
            manager.poll()

            self.assertEqual(handler.events, [('timeout', None)])
            self.assertTrue(handler.closed)
            self.assertEqual(manager._handlers, {})
        finally:
            handler.close()
            peer.close()
            poller.close()

    def test_timeout_callback_can_unregister_another_due_handler(self) -> None:
        first_sock, first_peer = socket.socketpair()
        second_sock, second_peer = socket.socketpair()
        poller = SelectFdioPoller()
        first = TestSocketFdioHandler(first_sock)
        second = TestSocketFdioHandler(second_sock)
        first.deadline = time.monotonic()
        second.deadline = time.monotonic()
        manager = FdioManager(poller)
        manager.register(first)
        manager.register(second)
        first.timeout_callback = lambda: manager.unregister(second)
        try:
            manager.poll()

            self.assertEqual(first.events, [('timeout', None)])
            self.assertEqual(second.events, [])
            self.assertEqual(list(manager._handlers.values()), [first])
        finally:
            first.close()
            first_peer.close()
            second.close()
            second_peer.close()
            poller.close()

    def test_server_socket_accepts_connection(self) -> None:
        accepted: ta.List[ta.Tuple[socket.socket, ta.Any]] = []
        server = ServerSocketFdioHandler(
            ('127.0.0.1', 0),
            lambda sock, addr: accepted.append((sock, addr)),
        )
        client = socket.create_connection(ta.cast(socket.socket, server._sock).getsockname())
        poller = SelectFdioPoller()
        manager = FdioManager(poller)
        manager.register(server)
        try:
            manager.poll(timeout=.5)

            self.assertEqual(len(accepted), 1)
            accepted_sock, accepted_addr = accepted[0]
            self.assertFalse(accepted_sock.getblocking())
            self.assertEqual(accepted_addr, client.getsockname())
        finally:
            for accepted_sock, _ in accepted:
                accepted_sock.close()
            client.close()
            server.close()
            poller.close()

    def test_invalid_caller_timeout(self) -> None:
        manager = FdioManager(SelectFdioPoller())

        with self.assertRaises(ValueError):
            manager.poll(timeout=-1.)

        with self.assertRaises(ValueError):
            manager.poll(timeout=float('inf'))
