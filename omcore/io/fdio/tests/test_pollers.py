# ruff: noqa: UP006 UP007 UP045
import socket
import typing as ta
import unittest

from ..kqueue import KqueueFdioPoller
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


class TestFdioPollers(unittest.TestCase):
    def test_readable_socket(self) -> None:
        for poller_type in poller_types():
            with self.subTest(poller_type=poller_type.__name__):
                sock, peer = socket.socketpair()
                poller = poller_type()
                try:
                    poller.update({sock.fileno()}, set())
                    peer.sendall(b'x')

                    result = poller.poll(.5)

                    self.assertIn(sock.fileno(), result.r)
                    self.assertNotIn(sock.fileno(), result.w)
                    self.assertEqual(sock.recv(1), b'x')
                finally:
                    poller.close()
                    sock.close()
                    peer.close()

    def test_writable_socket(self) -> None:
        for poller_type in poller_types():
            with self.subTest(poller_type=poller_type.__name__):
                sock, peer = socket.socketpair()
                poller = poller_type()
                try:
                    poller.update(set(), {sock.fileno()})

                    result = poller.poll(.5)

                    self.assertNotIn(sock.fileno(), result.r)
                    self.assertIn(sock.fileno(), result.w)
                finally:
                    poller.close()
                    sock.close()
                    peer.close()

    def test_removing_read_interest_preserves_write_interest(self) -> None:
        for poller_type in poller_types():
            with self.subTest(poller_type=poller_type.__name__):
                sock, peer = socket.socketpair()
                poller = poller_type()
                try:
                    fd = sock.fileno()
                    poller.update({fd}, {fd})
                    poller.update(set(), {fd})
                    peer.sendall(b'x')

                    result = poller.poll(.5)

                    self.assertNotIn(fd, result.r)
                    self.assertIn(fd, result.w)
                finally:
                    poller.close()
                    sock.close()
                    peer.close()

    def test_removing_write_interest_preserves_read_interest(self) -> None:
        for poller_type in poller_types():
            with self.subTest(poller_type=poller_type.__name__):
                sock, peer = socket.socketpair()
                poller = poller_type()
                try:
                    fd = sock.fileno()
                    poller.update({fd}, {fd})
                    poller.update({fd}, set())
                    peer.sendall(b'x')

                    result = poller.poll(.5)

                    self.assertIn(fd, result.r)
                    self.assertNotIn(fd, result.w)
                finally:
                    poller.close()
                    sock.close()
                    peer.close()
