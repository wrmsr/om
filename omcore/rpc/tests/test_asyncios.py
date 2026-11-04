# ruff: noqa: PT009 PT027 UP006 UP007 UP045
# @om-lite
import asyncio
import socket
import sys
import textwrap
import typing as ta

from ...testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ..asyncios import AsyncioRpcConnections
from ..asyncios import AsyncioRpcRuntime
from ..asyncios import AsyncioSerializingRpcHandler
from ..configs import RpcConfig
from ..connection import RpcConnection
from ..dispatch import RpcHandler
from ..dispatch import RpcMethodTableHandler
from ..dispatch import rpc_async_method
from ..errors import RpcConnectionClosedError
from ..errors import RpcErrorCodes
from ..errors import RpcRemoteCancelledError
from ..errors import RpcRemoteError
from ..errors import RpcTimeoutError


##


async def _rpc_test_pair(
        a_handler: ta.Optional[RpcHandler] = None,
        b_handler: ta.Optional[RpcHandler] = None,
        *,
        a_config: RpcConfig = RpcConfig.DEFAULT,
        b_config: ta.Optional[RpcConfig] = None,
) -> ta.Tuple[RpcConnection, RpcConnection]:
    s1, s2 = socket.socketpair()
    r1, w1 = await asyncio.open_connection(sock=s1)
    r2, w2 = await asyncio.open_connection(sock=s2)
    a = AsyncioRpcConnections.of_streams(r1, w1, a_config, handler=a_handler)
    b = AsyncioRpcConnections.of_streams(r2, w2, b_config if b_config is not None else a_config, handler=b_handler)
    await a.start()
    await b.start()
    return a, b


def _runtime(c: RpcConnection) -> AsyncioRpcRuntime:
    rt = c.runtime
    assert isinstance(rt, AsyncioRpcRuntime)
    return rt


class _Base(AsyncioIsolatedAsyncTestCase):
    async def _close_and_check(self, *conns: RpcConnection) -> None:
        for c in conns:
            await c.close()
        for c in conns:
            await c.wait_closed()
            self.assertTrue(c.is_closed)
            self.assertEqual(_runtime(c).num_tasks, 0)

        cur = asyncio.current_task()
        leftover = [t for t in asyncio.all_tasks() if t is not cur]
        if leftover:
            await asyncio.sleep(0)
            leftover = [t for t in asyncio.all_tasks() if t is not cur and not t.done()]
        self.assertEqual(leftover, [])


class TestAsyncioBasics(_Base):
    async def test_roundtrip_and_concurrency(self):
        async def echo(p):
            await asyncio.sleep(0)
            return p

        a, b = await _rpc_test_pair(b_handler=RpcMethodTableHandler({'echo': echo}))
        self.assertEqual(await a.request('echo', 'x'), 'x')
        res = await asyncio.gather(*[a.request('echo', i) for i in range(300)])
        self.assertEqual(res, list(range(300)))
        await a.ping()
        await self._close_and_check(a, b)

    async def test_handlers_run_concurrently(self):
        gate = asyncio.Event()
        entered = 0

        async def wait(p):
            nonlocal entered
            entered += 1
            await gate.wait()
            return p

        a, b = await _rpc_test_pair(b_handler=RpcMethodTableHandler({'wait': wait}))
        futs = [asyncio.ensure_future(a.request('wait', i)) for i in range(10)]
        for _ in range(100):
            if entered == 10:
                break
            await asyncio.sleep(.01)
        self.assertEqual(entered, 10)
        self.assertEqual(_runtime(b).num_tasks, 10)
        gate.set()
        self.assertEqual(await asyncio.gather(*futs), list(range(10)))
        await self._close_and_check(a, b)

    async def test_serializing_handler(self):
        active = 0
        max_active = 0

        async def work(p):
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(.001)
            active -= 1
            return p

        h = AsyncioSerializingRpcHandler(RpcMethodTableHandler({'work': work}))
        a, b = await _rpc_test_pair(b_handler=h)
        self.assertEqual(await asyncio.gather(*[a.request('work', i) for i in range(20)]), list(range(20)))
        self.assertEqual(max_active, 1)
        await self._close_and_check(a, b)

    async def test_inline_notifications_in_wire_order(self):
        got: ta.List[int] = []
        conns: ta.Dict[str, RpcConnection] = {}

        async def produce(n):
            for i in range(n):
                await conns['b'].notify('chunk', i)
            return 'done'

        a, b = await _rpc_test_pair(
            a_handler=RpcMethodTableHandler(inline_notifications={'chunk': got.append}),
            b_handler=RpcMethodTableHandler({'produce': produce}),
        )
        conns['b'] = b
        self.assertEqual(await a.request('produce', 200), 'done')
        self.assertEqual(got, list(range(200)))
        await self._close_and_check(a, b)


class TestAsyncioCancellation(_Base):
    async def test_caller_cancel_cancels_peer_handler(self):
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def forever(p):
            started.set()
            try:
                await asyncio.sleep(1000.)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        a, b = await _rpc_test_pair(b_handler=RpcMethodTableHandler({'forever': forever}))
        t = asyncio.ensure_future(a.request('forever'))
        await asyncio.wait_for(started.wait(), 5.)
        t.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await t
        await asyncio.wait_for(cancelled.wait(), 5.)
        await self._close_and_check(a, b)

    async def test_request_timeout_cancels_peer_handler(self):
        cancelled = asyncio.Event()

        async def forever(p):
            try:
                await asyncio.sleep(1000.)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        a, b = await _rpc_test_pair(b_handler=RpcMethodTableHandler({'forever': forever}))
        with self.assertRaises(RpcTimeoutError):
            await a.request('forever', timeout_s=.05)
        await asyncio.wait_for(cancelled.wait(), 5.)
        await self._close_and_check(a, b)

    async def test_handling_timeout(self):
        cancelled = asyncio.Event()

        async def forever(p):
            try:
                await asyncio.sleep(1000.)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        a, b = await _rpc_test_pair(
            b_handler=RpcMethodTableHandler({'forever': forever}),
            b_config=RpcConfig(inbound_handling_timeout_s=.05),
        )
        with self.assertRaises(RpcRemoteError) as cm:
            await a.request('forever')
        self.assertEqual(cm.exception.code, RpcErrorCodes.HANDLING_TIMEOUT)
        await asyncio.wait_for(cancelled.wait(), 5.)
        await self._close_and_check(a, b)

    async def test_handler_cancelled_elsewhere_answers_cancelled(self):
        tasks: ta.List[asyncio.Task] = []

        async def cancellable(p):
            tasks.append(ta.cast(asyncio.Task, asyncio.current_task()))
            await asyncio.sleep(1000.)

        a, b = await _rpc_test_pair(b_handler=RpcMethodTableHandler({'c': cancellable}))
        fut = asyncio.ensure_future(a.request('c'))
        for _ in range(100):
            if tasks:
                break
            await asyncio.sleep(.01)
        tasks[0].cancel()
        with self.assertRaises(RpcRemoteCancelledError) as cm:
            await fut
        self.assertEqual(cm.exception.code, RpcErrorCodes.CANCELLED)
        await self._close_and_check(a, b)

    async def test_abortive_close_cancels_handlers(self):
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def forever(p):
            started.set()
            try:
                await asyncio.sleep(1000.)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        a, b = await _rpc_test_pair(b_handler=RpcMethodTableHandler({'forever': forever}))
        fut = asyncio.ensure_future(a.request('forever'))
        await asyncio.wait_for(started.wait(), 5.)
        await b.close(graceful=False)
        self.assertTrue(cancelled.is_set())
        with self.assertRaises(RpcRemoteError) as cm:
            await fut
        self.assertEqual(cm.exception.code, RpcErrorCodes.SHUTTING_DOWN)
        await self._close_and_check(a, b)

    async def test_graceful_close_waits_for_pending(self):
        gate = asyncio.Event()

        async def slow(p):
            await gate.wait()
            return 'finished'

        a, b = await _rpc_test_pair(b_handler=RpcMethodTableHandler({'slow': slow}))
        fut = asyncio.ensure_future(a.request('slow'))
        await asyncio.sleep(.05)
        close = asyncio.ensure_future(a.close())
        await asyncio.sleep(.05)
        self.assertFalse(close.done())
        gate.set()
        self.assertEqual(await fut, 'finished')
        await close
        await self._close_and_check(a, b)

    async def test_pump_cancelled_fails_waiters(self):
        gate = asyncio.Event()

        async def slow(p):
            await gate.wait()

        a, b = await _rpc_test_pair(b_handler=RpcMethodTableHandler({'slow': slow}))
        fut = asyncio.ensure_future(a.request('slow'))
        await asyncio.sleep(.05)
        pump = _runtime(a)._pump_task  # noqa
        assert pump is not None
        pump.cancel()
        with self.assertRaises(RpcConnectionClosedError):
            await fut
        await a.wait_closed()
        self.assertTrue(a.is_closed)
        self.assertIsInstance(a.close_exception, RpcConnectionClosedError)
        gate.set()
        await self._close_and_check(a, b)

    async def test_peer_vanishes(self):
        a, b = await _rpc_test_pair(b_handler=RpcMethodTableHandler({'never': rpc_async_method(lambda p: None)}))
        await _runtime(b).close()
        with self.assertRaises(RpcConnectionClosedError):
            await a.request('never')
        await self._close_and_check(a, b)


class TestAsyncioMisc(_Base):
    async def test_keepalive_with_live_peer(self):
        cfg = RpcConfig(keepalive_interval_s=.02, keepalive_timeout_s=.5)
        a, b = await _rpc_test_pair(a_config=cfg)
        await asyncio.sleep(.3)
        self.assertFalse(a.is_closed)
        self.assertFalse(b.is_closed)
        await self._close_and_check(a, b)

    async def test_close_from_other_side_is_seen(self):
        a, b = await _rpc_test_pair()
        await b.close()
        await asyncio.wait_for(a.wait_closed(), 5.)
        self.assertTrue(a.is_closed)
        self.assertIsNone(a.close_exception)
        await self._close_and_check(a, b)

    async def test_not_started_close(self):
        s1, s2 = socket.socketpair()
        r1, w1 = await asyncio.open_connection(sock=s1)
        c = AsyncioRpcConnections.of_streams(r1, w1)
        await c.close()
        self.assertTrue(c.is_closed)
        await c.wait_closed()
        s2.close()


##


_ASYNCIO_CHILD_SERVER_SRC = textwrap.dedent("""
    import asyncio
    from omcore.rpc.asyncios import AsyncioRpcConnections
    from omcore.rpc.dispatch import RpcMethodTableHandler

    async def mul(p):
        await asyncio.sleep(0)
        return p[0] * p[1]

    async def main():
        c = await AsyncioRpcConnections.of_stdio(handler=RpcMethodTableHandler({'mul': mul}))
        async with c:
            await c.serve()

    asyncio.run(main())
""")


class TestAsyncioSubprocess(_Base):
    async def test_stdio_child(self):
        proc = await asyncio.create_subprocess_exec(
            sys.executable, '-c', _ASYNCIO_CHILD_SERVER_SRC,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        try:
            c = AsyncioRpcConnections.of_subprocess(proc)
            async with c:
                self.assertEqual(await c.request('mul', [6, 7]), 42)
                res = await asyncio.gather(*[c.request('mul', [i, i]) for i in range(50)])
                self.assertEqual(res, [i * i for i in range(50)])
            self.assertEqual(await asyncio.wait_for(proc.wait(), 10.), 0)
        finally:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
