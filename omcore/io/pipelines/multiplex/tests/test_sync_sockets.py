# ruff: noqa: UP006 UP007 UP045
# @om-lite
import socket
import threading
import typing as ta
import unittest

from ...drivers.sync import FdSyncIoPipelineDriver
from ...drivers.sync import SocketSyncIoPipelineDriver
from ...drivers.sync import SyncIoPipelineDriver
from .test_sockets import _Session


##


class TestMultiplexOverSyncSockets(unittest.TestCase):
    def _run(self, *, tls, fd):
        session = _Session(tls=tls)
        sockets = socket.socketpair()
        drivers = []
        config = SyncIoPipelineDriver.Config(
            read_chunk_size=257,
            read_batch_max_bytes=1028,
            read_batch_max_reads=4,
            write_chunk_max=509,
            write_high_watermark=8192,
            write_low_watermark=2048,
        )
        for sock, spec in zip(sockets, (session.client_spec, session.server_spec)):
            sock.settimeout(10.)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
            if fd:
                driver: SyncIoPipelineDriver = FdSyncIoPipelineDriver(
                    spec, sock.fileno(), sock.fileno(), config, timeout_s=10.,
                )
            else:
                driver = SocketSyncIoPipelineDriver(spec, sock, config)
            drivers.append(driver)

        remaining = [len(session.client_apps)]

        def stream_done(msg):
            remaining[0] -= 1
            if not remaining[0]:
                drivers[0].enqueue(*session.shutdown_messages())

        for app in session.client_apps.values():
            app.final_output.add_listener(stream_done)
        drivers[0].enqueue(*session.open_messages())
        errors: ta.List[BaseException] = []

        def run(index):
            try:
                drivers[index].loop_until_done()
            except BaseException as exc:  # noqa
                errors.append(exc)
            finally:
                drivers[index].close()
                # The sync driver borrows the socket; its owner supplies the final transport close.
                sockets[index].close()

        threads = [threading.Thread(target=run, args=(index,), daemon=True) for index in range(2)]
        try:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(15.)
            self.assertFalse(any(thread.is_alive() for thread in threads))
            self.assertEqual(errors, [])
            session.check(self)
        finally:
            for sock in sockets:
                sock.close()
            for thread in threads:
                thread.join(12.)
            for driver in drivers:
                driver.close()

    def test_socket(self):
        self._run(tls=False, fd=False)

    def test_socket_tls(self):
        self._run(tls=True, fd=False)

    def test_fd(self):
        self._run(tls=False, fd=True)

    def test_fd_tls(self):
        self._run(tls=True, fd=True)
