# ruff: noqa: PT009
# @om-lite
import socket
import unittest

from ..addresses import SocketAndAddress
from ..handlers.simple import StandardSocketHandler


class TestStandardSocketHandler(unittest.TestCase):
    def test_no_close(self):
        left, right = socket.socketpair()
        try:
            StandardSocketHandler(lambda conn: None, no_close=True)(SocketAndAddress(left, None))

            self.assertNotEqual(left.fileno(), -1)
        finally:
            left.close()
            right.close()

    def test_close(self):
        left, right = socket.socketpair()
        try:
            StandardSocketHandler(lambda conn: None)(SocketAndAddress(left, None))

            self.assertEqual(left.fileno(), -1)
        finally:
            left.close()
            right.close()
