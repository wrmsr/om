# @om-lite
import socket
import unittest

from ....io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from ....io.pipelines.drivers.types import IoPipelineDriverState
from ..pipelines.handlers import SimpleHttpHandlerServerIoPipelineHandler


##


class TestSimpleHttpHandlerServerIoPipelineHandler(unittest.TestCase):
    def test_empty_connection_closes_without_stalling(self):
        def fail_handler(req):
            self.fail(f'Unexpected request: {req!r}')

        sock, peer = socket.socketpair()
        with sock, peer:
            drv = SyncSocketIoPipelineDriver(
                SimpleHttpHandlerServerIoPipelineHandler.build_standard_pipeline_spec(
                    sock,
                    peer.getsockname(),
                    fail_handler,
                ),
                sock,
            )
            peer.shutdown(socket.SHUT_WR)

            drv.loop_until_done()

            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
