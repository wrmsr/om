# ruff: noqa: PT009
# @om-lite
import unittest

from ..bind import TcpSocketBinder


class TestTcpSocketBinder(unittest.TestCase):
    def test_default_ephemeral_port(self):
        config = TcpSocketBinder.Config()

        self.assertEqual(config.port, 0)
        with TcpSocketBinder(config) as binder:
            port = binder.port
            assert port is not None
            self.assertGreater(port, 0)
