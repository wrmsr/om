# @om-lite
import fcntl
import os
import pty
import resource
import socket
import tty
import unittest

from ...core import IoPipeline
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ...handlers.feedback import FeedbackInboundIoPipelineHandler
from ...ssl.tests.test_halfclose import _App
from ..sync import FdSyncIoPipelineDriver
from ..sync import SocketSyncIoPipelineDriver
from ..sync import SyncIoPipelineDriver


##


class TestFdOwnership(unittest.TestCase):
    def test_valid_high_numbered_descriptors_transfer_and_half_close(self):
        soft_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        if soft_limit != resource.RLIM_INFINITY and soft_limit <= 1024:
            self.skipTest('process descriptor limit does not permit a descriptor above FD_SETSIZE')
        for fd in (False, True):
            for high in (False, True):
                with self.subTest(fd=fd, high=high):
                    sock, peer = socket.socketpair()
                    transport = socket.socket(fileno=fcntl.fcntl(sock.fileno(), fcntl.F_DUPFD, 1024)) if high else sock
                    transport.settimeout(2.)
                    peer.settimeout(2.)
                    app = _App(respond=b'response')
                    spec = IoPipeline.Spec([app], services=[StubIoPipelineFlowService(auto_read=True)])
                    driver: SyncIoPipelineDriver
                    if fd:
                        driver = FdSyncIoPipelineDriver(spec, transport.fileno(), transport.fileno(), timeout_s=2.)
                    else:
                        driver = SocketSyncIoPipelineDriver(spec, transport)
                    try:
                        peer.sendall(b'request')
                        peer.shutdown(socket.SHUT_WR)
                        driver.loop_until_done()
                        self.assertEqual(bytes(app.received), b'request')
                        received = bytearray()
                        while chunk := peer.recv(128):
                            received.extend(chunk)
                        self.assertEqual(received, b'response')
                        self.assertTrue(app.shutdown_output.is_succeeded())
                        self.assertTrue(app.final_output.is_succeeded())
                    finally:
                        driver.close()
                        transport.close()
                        sock.close()
                        peer.close()

    def test_duplicate_socket_descriptors_restore_original_flags(self):
        for graceful in (False, True):
            with self.subTest(graceful=graceful):
                sock, peer = socket.socketpair()
                read_fd = os.dup(sock.fileno())
                write_fd = os.dup(sock.fileno())
                original = fcntl.fcntl(read_fd, fcntl.F_GETFL)
                feedback = FeedbackInboundIoPipelineHandler()
                driver = FdSyncIoPipelineDriver(
                    IoPipeline.Spec([feedback], services=[StubIoPipelineFlowService(auto_read=False)]),
                    read_fd,
                    write_fd,
                )
                try:
                    driver.next(read=False)
                    self.assertTrue(fcntl.fcntl(read_fd, fcntl.F_GETFL) & os.O_NONBLOCK)
                    if graceful:
                        final = IoPipelineMessages.FinalOutput()
                        driver.enqueue(feedback.wrap(final))
                        driver.next(read=False)
                        self.assertTrue(final.is_succeeded())
                    driver.close()
                    self.assertEqual(fcntl.fcntl(read_fd, fcntl.F_GETFL), original)
                    self.assertEqual(fcntl.fcntl(write_fd, fcntl.F_GETFL), original)
                finally:
                    driver.close()
                    os.close(read_fd)
                    os.close(write_fd)
                    sock.close()
                    peer.close()

    def test_terminal_read_descriptor_restores_flags_after_write_half_close(self):
        master, write_fd = pty.openpty()
        tty.setraw(write_fd)
        read_fd = os.dup(write_fd)
        original = fcntl.fcntl(read_fd, fcntl.F_GETFL)
        feedback = FeedbackInboundIoPipelineHandler()
        driver = FdSyncIoPipelineDriver(
            IoPipeline.Spec([feedback], services=[StubIoPipelineFlowService(auto_read=False)]),
            read_fd,
            write_fd,
            close_write_fd_on_output_shutdown=True,
        )
        shutdown = IoPipelineMessages.ShutdownOutput()
        try:
            driver.next(read=False)
            driver.enqueue(feedback.wrap(shutdown))
            driver.next(read=False)
            self.assertTrue(shutdown.is_succeeded())
            self.assertTrue(fcntl.fcntl(read_fd, fcntl.F_GETFL) & os.O_NONBLOCK)
            driver.close()
            self.assertEqual(fcntl.fcntl(read_fd, fcntl.F_GETFL), original)
        finally:
            driver.close()
            if not shutdown.is_succeeded():
                os.close(write_fd)
            os.close(read_fd)
            os.close(master)
