# ruff: noqa: PT009 PT027 UP006 UP007 UP045
# @om-lite
"""Seeded randomized exercises of both runtimes, checking invariants rather than specific outcomes."""
import asyncio
import random
import socket
import typing as ta
import unittest

from ...testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ..asyncio import AsyncioRpcConnections
from ..asyncio import AsyncioRpcRuntime
from ..configs import RpcConfig
from ..connection import RpcConnection
from ..dispatch import RpcHandler
from ..dispatch import RpcMethodTableHandler
from ..errors import RpcConnectionClosedError
from ..errors import RpcError
from ..errors import RpcRemoteError
from ..errors import RpcTimeoutError
from ..pure import pure_rpc_connection_pair


##


class _RpcStressRecorder:
    def __init__(self) -> None:
        super().__init__()

        self.notes: ta.List[ta.Any] = []
        self.outcomes: ta.Dict[str, int] = {}

    def outcome(self, kind: str) -> None:
        self.outcomes[kind] = self.outcomes.get(kind, 0) + 1


def _rpc_stress_handler(
        name: str,
        conns: ta.Dict[str, RpcConnection],
        rec: _RpcStressRecorder,
        sleep: ta.Optional[ta.Callable[[float], ta.Awaitable[None]]] = None,
) -> RpcHandler:
    async def op(p: ta.Any) -> ta.Any:
        kind, depth, seed = p
        rng = random.Random(seed)

        if sleep is not None and rng.random() < .3:
            await sleep(rng.random() * .002)

        if kind == 'fail':
            raise ValueError(f'fail at {depth}')

        if kind == 'notify':
            await conns[name].notify('note', [name, depth])

        if kind == 'nest' and depth > 0:
            sub = rng.choice(['echo', 'fail', 'nest', 'notify'])
            try:
                inner = await conns[name].request('op', [sub, depth - 1, rng.randrange(1 << 30)])
            except RpcRemoteError:
                inner = 'remote-error'
            return [name, inner]

        return [name, kind, depth]

    return RpcMethodTableHandler(
        {'op': op},
        inline_notifications={'note': rec.notes.append},
    )


class TestPureStress(unittest.TestCase):
    def test_random_nested_traffic(self):
        for seed in range(20):
            with self.subTest(seed=seed):
                self._run(seed)

    def _run(self, seed: int) -> None:
        rng = random.Random(seed)
        rec = _RpcStressRecorder()
        conns: ta.Dict[str, RpcConnection] = {}

        pair = pure_rpc_connection_pair(
            RpcConfig(max_frame_bytes=4096),
            a_kwargs=dict(handler=_rpc_stress_handler('a', conns, rec)),
            b_kwargs=dict(handler=_rpc_stress_handler('b', conns, rec)),
            capacity=rng.choice([None, 64, 512]),
        )
        conns['a'] = pair.a.connection
        conns['b'] = pair.b.connection

        for _ in range(60):
            side = rng.choice([pair.a, pair.b])
            kind = rng.choice(['echo', 'fail', 'nest', 'notify', 'big', 'ping'])
            try:
                if kind == 'ping':
                    side.ping()
                    rec.outcome('pong')
                elif kind == 'big':
                    side.request('op', ['echo', 0, 'x' * 5000])
                    rec.outcome('unexpected')
                else:
                    side.request('op', [kind, rng.randrange(6), rng.randrange(1 << 30)])
                    rec.outcome('ok')
            except RpcRemoteError:
                rec.outcome('remote')
            except ValueError:
                rec.outcome('too-big')

        self.assertEqual(rec.outcomes.get('unexpected', 0), 0)
        self.assertFalse(pair.a.is_closed)
        self.assertFalse(pair.b.is_closed)

        rng.choice([pair.a, pair.b]).close()
        pair.a.wait_closed()
        pair.b.wait_closed()
        self.assertIsNone(pair.a.close_exception)
        self.assertIsNone(pair.b.close_exception)


class TestAsyncioStress(AsyncioIsolatedAsyncTestCase):
    async def test_random_concurrent_traffic_with_cancellation(self):
        for seed in range(3):
            await self._run(seed)

    async def _run(self, seed: int) -> None:
        rng = random.Random(seed)
        rec = _RpcStressRecorder()
        conns: ta.Dict[str, RpcConnection] = {}

        s1, s2 = socket.socketpair()
        r1, w1 = await asyncio.open_connection(sock=s1)
        r2, w2 = await asyncio.open_connection(sock=s2)
        cfg = RpcConfig(max_frame_bytes=1 << 20)
        a = AsyncioRpcConnections.of_streams(r1, w1, cfg, handler=_rpc_stress_handler('a', conns, rec, asyncio.sleep))
        b = AsyncioRpcConnections.of_streams(r2, w2, cfg, handler=_rpc_stress_handler('b', conns, rec, asyncio.sleep))
        conns['a'] = a
        conns['b'] = b
        await a.start()
        await b.start()

        async def one() -> str:
            side = rng.choice([a, b])
            kind = rng.choice(['echo', 'fail', 'nest', 'notify'])
            try:
                await side.request(
                    'op',
                    [kind, rng.randrange(5), rng.randrange(1 << 30)],
                    timeout_s=rng.choice([None, None, .001, .05]),
                )
                return 'ok'
            except RpcRemoteError:
                return 'remote'
            except RpcTimeoutError:
                return 'timeout'

        tasks = [asyncio.ensure_future(one()) for _ in range(200)]
        await asyncio.sleep(.001)
        for t in rng.sample(tasks, 30):
            t.cancel()

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, BaseException):
                self.assertIsInstance(r, asyncio.CancelledError)
            else:
                self.assertIn(r, ('ok', 'remote', 'timeout'))

        # Still healthy after all that.
        self.assertEqual(await a.request('op', ['echo', 0, 0]), ['b', 'echo', 0])
        self.assertEqual(await b.request('op', ['echo', 0, 0]), ['a', 'echo', 0])

        await rng.choice([a, b]).close()
        await a.wait_closed()
        await b.wait_closed()
        for c in (a, b):
            rt = c.runtime
            assert isinstance(rt, AsyncioRpcRuntime)
            self.assertEqual(rt.num_tasks, 0)
            self.assertIsNone(c.close_exception)

        cur = asyncio.current_task()
        await asyncio.sleep(0)
        self.assertEqual([t for t in asyncio.all_tasks() if t is not cur and not t.done()], [])

    async def test_close_racing_traffic(self):
        for seed in (0, 1, 2, 58):
            rng = random.Random(seed)
            rec = _RpcStressRecorder()
            conns: ta.Dict[str, RpcConnection] = {}

            s1, s2 = socket.socketpair()
            r1, w1 = await asyncio.open_connection(sock=s1)
            r2, w2 = await asyncio.open_connection(sock=s2)
            a = AsyncioRpcConnections.of_streams(r1, w1, handler=_rpc_stress_handler('a', conns, rec, asyncio.sleep))
            b = AsyncioRpcConnections.of_streams(r2, w2, handler=_rpc_stress_handler('b', conns, rec, asyncio.sleep))
            conns['a'] = a
            conns['b'] = b
            await a.start()
            await b.start()

            async def one() -> None:
                side = rng.choice([a, b])
                try:
                    await side.request('op', [rng.choice(['echo', 'nest', 'notify']), 3, rng.randrange(1 << 30)])
                except (RpcError, ConnectionError):
                    pass

            tasks = [asyncio.ensure_future(one()) for _ in range(100)]
            await asyncio.sleep(rng.random() * .01)
            for t in rng.sample(tasks, 10):
                t.cancel()

            closer = rng.choice([a, b])
            mode = rng.random()
            if mode < .4:
                await closer.close(graceful=True)
            elif mode < .8:
                await closer.close(graceful=False)
            else:
                # Abrupt: the transport just goes away.
                await closer.runtime.close()

            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), 10.)
            for t in tasks:
                self.assertTrue(t.done())
                if not t.cancelled():
                    self.assertIsNone(t.exception())

            await asyncio.wait_for(a.wait_closed(), 10.)
            await asyncio.wait_for(b.wait_closed(), 10.)
            for c in (a, b):
                rt = c.runtime
                assert isinstance(rt, AsyncioRpcRuntime)
                self.assertEqual(rt.num_tasks, 0)

            with self.assertRaises(RpcConnectionClosedError):
                await a.request('op', ['echo', 0, 0])
