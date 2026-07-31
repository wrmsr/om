# ruff: noqa: PT009
# @om-lite
import io
import socket
import unittest

from ..io import SocketIoPair
from ..io import SocketWriter


class TestSocketIoPair(unittest.TestCase):
    def test_writer_buffer_size(self):
        for buffer_size, writer_type in [
            (0, SocketWriter),
            (8192, io.BufferedWriter),
        ]:
            left, right = socket.socketpair()
            try:
                pair = SocketIoPair.from_socket(left, w_buf_size=buffer_size)
                try:
                    self.assertIsInstance(pair.w, writer_type)
                finally:
                    pair.r.close()
                    pair.w.close()
            finally:
                left.close()
                right.close()
