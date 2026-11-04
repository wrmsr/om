# ruff: noqa: PT009 PT027 UP006 UP007 UP045
# @om-lite
import socket
import subprocess
import sys
import textwrap
import threading
import time
import typing as ta
import unittest

from ..configs import RpcConfig
from ..connection import RpcConnection
from ..connection import SyncRpcConnection
from ..dispatch import RpcMethodTableHandler
from ..dispatch import rpc_async_method
from ..errors import RpcConnectionClosedError
from ..errors import RpcRemoteError
from ..errors import RpcTimeoutError
from ..sync import SyncRpcConnections


##


class _Server:
    """A sync connection served on a thread until its peer goes away."""

    def __init__(self, sock: socket.socket, handler: ta.Any, config: RpcConfig = RpcConfig.DEFAULT) -> None:
        self.conn = SyncRpcConnections.of_socket(sock, config, handler=handler)
        self.exc: ta.Optional[BaseException] = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        try:
            with self.conn:
                self.conn.serve()
        except BaseException as e:  # noqa
            self.exc = e

    def join(self, timeout: float = 10.) -> None:
        self.thread.join(timeout)
        if self.thread.is_alive():
            raise RuntimeError('server thread did not finish')
        if self.exc is not None:
            raise self.exc


def _echo_table(**extra: ta.Any) -> RpcMethodTableHandler:
    return RpcMethodTableHandler({
        'echo': rpc_async_method(lambda p: p),
        **extra,
    })


class TestSyncSockets(unittest.TestCase):
    def test_roundtrip(self):
        s1, s2 = socket.socketpair()
        srv = _Server(s2, _echo_table())
        with SyncRpcConnections.of_socket(s1) as c:
            for i in range(100):
                self.assertEqual(c.request('echo', {'i': i}), {'i': i})
            c.ping()
            c.notify('whatever')
        srv.join()
        self.assertTrue(srv.conn.is_closed)
        self.assertIsNone(srv.conn.close_exception)

    def test_large_payloads(self):
        s1, s2 = socket.socketpair()
        srv = _Server(s2, _echo_table())
        payload = 'x' * (4 * 1024 * 1024)
        with SyncRpcConnections.of_socket(s1) as c:
            for _ in range(3):
                self.assertEqual(c.request('echo', payload), payload)
        srv.join()

    def test_server_calls_back_during_request(self):
        s1, s2 = socket.socketpair()
        conns: ta.Dict[str, RpcConnection] = {}

        async def ask_back(p):
            return 'server got ' + await conns['srv'].request('whoami')

        srv = _Server(s2, RpcMethodTableHandler({'ask_back': ask_back}))
        conns['srv'] = srv.conn.connection

        client_handler = RpcMethodTableHandler({'whoami': rpc_async_method(lambda p: 'client')})
        with SyncRpcConnections.of_socket(s1, handler=client_handler) as c:
            self.assertEqual(c.request('ask_back'), 'server got client')
        srv.join()

    def test_request_timeout_against_slow_handler(self):
        s1, s2 = socket.socketpair()
        release = threading.Event()

        def slow(p):
            release.wait(10.)
            return 'late'

        srv = _Server(s2, _echo_table(slow=rpc_async_method(slow)))
        with SyncRpcConnections.of_socket(s1) as c:
            t0 = time.monotonic()
            with self.assertRaises(RpcTimeoutError):
                c.request('slow', timeout_s=.2)
            self.assertLess(time.monotonic() - t0, 5.)
            release.set()

            # The late answer is dropped, and the connection carries on.
            self.assertEqual(c.request('echo', 1), 1)
        srv.join()

    def test_remote_error(self):
        s1, s2 = socket.socketpair()

        def boom(p):
            raise FileNotFoundError(p)

        srv = _Server(s2, _echo_table(boom=rpc_async_method(boom)))
        with SyncRpcConnections.of_socket(s1) as c:
            with self.assertRaises(RpcRemoteError) as cm:
                c.request('boom', '/nope')
            self.assertEqual(cm.exception.remote_type, 'builtins.FileNotFoundError')
        srv.join()

    def test_peer_disappears(self):
        s1, s2 = socket.socketpair()
        c = SyncRpcConnections.of_socket(s1)
        c.start()
        s2.close()
        with self.assertRaises(RpcConnectionClosedError):
            c.request('echo', 1)
        c.close()
        self.assertTrue(c.is_closed)

    def test_thread_guard(self):
        s1, s2 = socket.socketpair()
        entered = threading.Event()
        release = threading.Event()

        def block(p):
            entered.set()
            release.wait(10.)
            return 'ok'

        srv = _Server(s2, _echo_table(block=rpc_async_method(block)))
        c = SyncRpcConnections.of_socket(s1)
        c.start()

        results: ta.List[ta.Any] = []
        t = threading.Thread(target=lambda: results.append(c.request('block')))
        t.start()
        self.assertTrue(entered.wait(10.))
        try:
            with self.assertRaises(RuntimeError):
                c.request('echo', 1)
        finally:
            release.set()
            t.join(10.)

        self.assertEqual(results, ['ok'])
        c.close()
        srv.join()


##


_CHILD_SERVER_SRC = textwrap.dedent("""
    from omcore.rpc.dispatch import RpcMethodTableHandler, rpc_async_method
    from omcore.rpc.syncs import SyncRpcConnections

    h = RpcMethodTableHandler({'add': rpc_async_method(lambda p: p[0] + p[1])})
    with SyncRpcConnections.of_stdio(handler=h) as c:
        c.serve()
""")


class TestSyncSubprocess(unittest.TestCase):
    def test_stdio_child(self):
        proc = subprocess.Popen(
            [sys.executable, '-c', _CHILD_SERVER_SRC],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        try:
            with SyncRpcConnections.of_subprocess(proc) as c:
                self.assertIsInstance(c, SyncRpcConnection)
                self.assertEqual(c.request('add', [2, 3]), 5)
                self.assertEqual(c.request('add', ['a', 'b']), 'ab')
            self.assertEqual(proc.wait(10.), 0)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            if proc.stdout is not None:
                proc.stdout.close()
