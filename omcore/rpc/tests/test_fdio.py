# ruff: noqa: PT009 PT027 UP006 UP007 UP045
# @om-lite
import socket
import threading
import typing as ta
import unittest

from ...io.fdio.handlers import ServerSocketFdioHandler
from ...io.fdio.manager import FdioManager
from ...io.fdio.pollers import SelectFdioPoller
from ...lite.asyncs import sync_await
from ..closing import RpcCloseAfterRequestsIoPipelineHandler
from ..connection import RpcConnection
from ..dispatch import RpcMethodTableHandler
from ..dispatch import rpc_async_method
from ..errors import RpcRemoteError
from ..fdio import RpcSocketFdioHandler
from ..specs import rpc_build_pipeline_spec
from ..sync import SyncRpcConnections


##


class _FdioRpcTestServer:
    """An fdio manager on one thread, hosting an rpc connection per accepted socket."""

    def __init__(self, *, one_request: bool = False) -> None:
        super().__init__()

        self.manager = FdioManager(SelectFdioPoller())
        self.connections: ta.List[RpcConnection] = []
        self.notes: ta.List[ta.Any] = []
        self._one_request = one_request
        self._stop = threading.Event()

        lsock = socket.create_server(('127.0.0.1', 0))
        self.port = lsock.getsockname()[1]
        self.manager.register(ServerSocketFdioHandler(lsock, self._on_connect))

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _handler(self, conn_ref: ta.List[RpcConnection]) -> RpcMethodTableHandler:
        def fail(p: ta.Any) -> ta.Any:
            raise ValueError(p)

        def notify_back(p: ta.Any) -> ta.Any:
            conn_ref[0].notify_nowait('note', p)
            return 'notified'

        return RpcMethodTableHandler(
            {
                'echo': rpc_async_method(lambda p: p),
                'fail': rpc_async_method(fail),
                'notify_back': rpc_async_method(notify_back),
            },
            inline_notifications={'note': self.notes.append},
        )

    def _on_connect(self, sock: socket.socket, addr: ta.Any) -> None:
        spec = rpc_build_pipeline_spec(
            between_handlers=[RpcCloseAfterRequestsIoPipelineHandler()] if self._one_request else [],
        )
        h = RpcSocketFdioHandler(sock, addr, spec)
        conn_ref: ta.List[RpcConnection] = []
        conn = RpcConnection(h.runtime, handler=self._handler(conn_ref))
        conn_ref.append(conn)
        sync_await(conn.start())
        self.connections.append(conn)
        self.manager.register(h)

    def _run(self) -> None:
        while not self._stop.is_set():
            self.manager.poll(timeout=.02)

    def stop(self) -> None:
        self._stop.set()
        self.thread.join(5.)


class TestFdioRuntime(unittest.TestCase):
    def test_serve_many_clients_on_one_thread(self):
        srv = _FdioRpcTestServer()
        try:
            clients = [SyncRpcConnections.connect_tcp('127.0.0.1', srv.port) for _ in range(5)]
            for c in clients:
                c.start()

            for i in range(20):
                for j, c in enumerate(clients):
                    self.assertEqual(c.request('echo', [i, j]), [i, j])

            with self.assertRaises(RpcRemoteError) as cm:
                clients[0].request('fail', 'x')
            self.assertEqual(cm.exception.remote_type, 'builtins.ValueError')

            # The server notifying back from inside a handler, where nothing may wait.
            got: ta.List[ta.Any] = []
            clients[1].set_handler(RpcMethodTableHandler(inline_notifications={'note': got.append}))
            self.assertEqual(clients[1].request('notify_back', 'hey'), 'notified')
            self.assertEqual(got, ['hey'])

            clients[2].notify('note', 'from client')
            clients[2].ping()

            for c in clients:
                c.close()

            for _ in range(200):
                if all(sc.is_closed for sc in srv.connections):
                    break
                threading.Event().wait(.01)
            self.assertTrue(all(sc.is_closed for sc in srv.connections))
            self.assertEqual(srv.notes, ['from client'])

        finally:
            srv.stop()

    def test_one_request_per_connection(self):
        srv = _FdioRpcTestServer(one_request=True)
        try:
            for i in range(10):
                with SyncRpcConnections.connect_tcp('127.0.0.1', srv.port) as c:
                    self.assertEqual(c.request('echo', i), i)
                    c.wait_closed()
                    self.assertIsNone(c.close_exception)
        finally:
            srv.stop()
