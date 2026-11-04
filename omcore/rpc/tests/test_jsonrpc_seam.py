"""
The JSON-RPC connection (`omcore.specs.jsonrpc.pipelines`) is a `BaseRpcConnection` subclass over its own session. These
run it on each of the toolbox's runtimes unchanged - including the pure link, which JSON-RPC gets deterministic,
virtual-time tests from - so a change to the base or the runtimes which breaks the other vocabulary shows up here.
Standard code, as JSON-RPC is.
"""
import asyncio
import socket
import threading
import typing as ta
import unittest

from ...io.pipelines.drivers.asyncio.streams import PollAsyncioStreamIoPipelineDriver
from ...lite.asyncs import sync_await
from ...specs.jsonrpc.dispatch import AsyncDictJsonrpcDispatcher
from ...specs.jsonrpc.errors import JsonrpcConnectionClosedError
from ...specs.jsonrpc.errors import JsonrpcRemoteError
from ...specs.jsonrpc.errors import JsonrpcTimeoutError
from ...specs.jsonrpc.errors import KnownErrors
from ...specs.jsonrpc.pipelines.base import BaseJsonrpcConnection
from ...specs.jsonrpc.pipelines.configs import JsonrpcPipelineConfig
from ...specs.jsonrpc.pipelines.specs import build_jsonrpc_pipeline_spec
from ...specs.jsonrpc.pipelines.sync import SyncJsonrpcConnections
from ...specs.jsonrpc.types import notification
from ...specs.jsonrpc.types import request
from ...testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ..asyncios import AsyncioRpcRuntime
from ..pure import PureRpcLink


##


def _dispatcher() -> AsyncDictJsonrpcDispatcher:
    async def add(a: int, b: int) -> int:
        return a + b

    def fail() -> None:
        raise ValueError('nope')

    return AsyncDictJsonrpcDispatcher({'add': add, 'fail': fail})


class TestJsonrpcOnPureLink(unittest.TestCase):
    def _pair(self, config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT) -> ta.Any:
        link = PureRpcLink(build_jsonrpc_pipeline_spec(config), build_jsonrpc_pipeline_spec(config))
        a = BaseJsonrpcConnection(link.a, config)
        b = BaseJsonrpcConnection(link.b, config, dispatcher=_dispatcher())
        sync_await(a.start())
        sync_await(b.start())
        return link, a, b

    def test_requests_errors_batches(self):
        link, a, b = self._pair()

        self.assertEqual(sync_await(a.request('add', {'a': 2, 'b': 3})), 5)

        with self.assertRaises(JsonrpcRemoteError) as cm:
            sync_await(a.request('fail'))
        self.assertEqual(cm.exception.error.code, KnownErrors.INTERNAL_ERROR.code)

        with self.assertRaises(JsonrpcRemoteError) as cm:
            sync_await(a.request('nope'))
        self.assertEqual(cm.exception.error.code, KnownErrors.METHOD_NOT_FOUND.code)

        responses = sync_await(a.send_batch([
            request(100, 'add', {'a': 1, 'b': 1}),
            notification('whatever'),
            request(101, 'add', {'a': 2, 'b': 2}),
        ]))
        self.assertEqual([r.result if r is not None else None for r in responses], [2, None, 4])

        sync_await(a.close())
        sync_await(b.wait_closed())
        self.assertTrue(b.is_closed)
        self.assertEqual(link.now, 0.)

    def test_timeout_on_virtual_clock(self):
        config = JsonrpcPipelineConfig(default_request_timeout_s=7.)
        link = PureRpcLink(build_jsonrpc_pipeline_spec(config), build_jsonrpc_pipeline_spec(config))
        a = BaseJsonrpcConnection(link.a, config)
        sync_await(a.start())

        # The far end never starts, so never answers.
        with self.assertRaises(JsonrpcTimeoutError):
            sync_await(a.request('add', [1, 2]))
        self.assertEqual(link.now, 7.)

        sync_await(a.close(graceful=False))
        with self.assertRaises(JsonrpcConnectionClosedError):
            sync_await(a.request('add', [1, 2]))


class TestJsonrpcOnSyncRuntime(unittest.TestCase):
    def test_sync_sockets(self):
        s1, s2 = socket.socketpair()

        srv = SyncJsonrpcConnections.of_socket(s2, dispatcher=_sync_dispatcher())

        def serve() -> None:
            with srv:
                srv.serve()

        th = threading.Thread(target=serve)
        th.start()
        with SyncJsonrpcConnections.of_socket(s1) as c:
            for i in range(50):
                self.assertEqual(c.request('add', [i, i]), 2 * i)
        th.join(10.)
        self.assertFalse(th.is_alive())
        self.assertTrue(srv.is_closed)


def _sync_dispatcher() -> ta.Any:
    from ...specs.jsonrpc.dispatch import DictJsonrpcDispatcher

    return DictJsonrpcDispatcher({'add': lambda a, b: a + b})


class TestJsonrpcOnAsyncioRuntime(AsyncioIsolatedAsyncTestCase):
    async def test_asyncio_runtime(self):
        s1, s2 = socket.socketpair()
        r1, w1 = await asyncio.open_connection(sock=s1)
        r2, w2 = await asyncio.open_connection(sock=s2)

        def runtime(r: asyncio.StreamReader, w: asyncio.StreamWriter) -> AsyncioRpcRuntime:
            return AsyncioRpcRuntime(PollAsyncioStreamIoPipelineDriver(build_jsonrpc_pipeline_spec(), r, w))

        a = BaseJsonrpcConnection(runtime(r1, w1))
        b = BaseJsonrpcConnection(runtime(r2, w2), dispatcher=_dispatcher())
        async with a, b:
            res = await asyncio.gather(*[a.request('add', [i, 1]) for i in range(100)])
            self.assertEqual(res, [i + 1 for i in range(100)])
            await a.notify('n')
