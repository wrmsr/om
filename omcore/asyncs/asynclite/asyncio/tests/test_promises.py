# ruff: noqa: SLF001
# @om-lite
import asyncio

from .....lite.asyncs import SyncAwaitCoroutineNotTerminatedError
from .....lite.asyncs import sync_await
from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...eventpromises import EventAsynclitePromise
from ...promises import AsynclitePromiseWaitTimeoutError
from ..api import AsyncioAsynclite


class TestAsyncioPromises(AsyncioIsolatedAsyncTestCase):
    async def test_value(self):
        p = AsyncioAsynclite().make_promise()

        self.assertFalse(p.is_done())
        self.assertFalse(p.poll().present)

        p.set_value(420)
        self.assertTrue(p.is_done())
        self.assertEqual(p.poll().must(), 420)
        self.assertEqual(await p.wait(), 420)

    async def test_error(self):
        class FooError(Exception):
            pass

        p = AsyncioAsynclite().make_promise()

        p.set_error(FooError())
        self.assertTrue(p.is_done())

        for _ in range(2):
            with self.assertRaises(FooError):
                p.poll()
            with self.assertRaises(FooError):
                await p.wait()

    async def test_multiple_waiters(self):
        p = AsyncioAsynclite().make_promise()

        t1: asyncio.Future = asyncio.ensure_future(p.wait())
        t2: asyncio.Future = asyncio.ensure_future(p.wait())
        await asyncio.sleep(0.01)

        p.set_value(420)
        self.assertEqual(await t1, 420)
        self.assertEqual(await t2, 420)

    async def test_cancel_does_not_affect_promise(self):
        p = AsyncioAsynclite().make_promise()

        task: asyncio.Future = asyncio.ensure_future(p.wait())
        await asyncio.sleep(0.01)

        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        p.set_value(420)
        self.assertEqual(await p.wait(), 420)

    async def test_done_promise_sheds_machinery(self):
        p = AsyncioAsynclite().make_promise()
        assert isinstance(p, EventAsynclitePromise)

        # A mid-wait waiter holds its own ref to the event and is unaffected by the shedding.
        task: asyncio.Future = asyncio.ensure_future(p.wait())
        await asyncio.sleep(0.01)

        p.set_value(420)
        self.assertIsNone(p._ev)
        self.assertIsNone(p._mtx)

        self.assertEqual(await task, 420)
        self.assertEqual(await p.wait(), 420)

    async def test_timeout(self):
        p = AsyncioAsynclite().make_promise()

        with self.assertRaises(AsynclitePromiseWaitTimeoutError):
            await p.wait(timeout=0)

        p.set_value(420)
        self.assertEqual(await p.wait(timeout=0), 420)

    async def test_sync_await_leak(self):
        p = AsyncioAsynclite().make_promise()

        with self.assertRaises(SyncAwaitCoroutineNotTerminatedError):
            sync_await(p.wait())
