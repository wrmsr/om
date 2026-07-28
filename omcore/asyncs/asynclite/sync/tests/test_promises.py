# ruff: noqa: SLF001
# @om-lite
import threading

from .....testing.unittest.asyncs import SyncIsolatedAsyncTestCase
from ...eventpromises import EventAsynclitePromise
from ...promises import AsynclitePromiseAlreadySetError
from ...promises import AsynclitePromiseWaitTimeoutError
from ..api import SyncAsynclite


class TestSyncPromises(SyncIsolatedAsyncTestCase):
    async def test_value(self):
        p = SyncAsynclite().make_promise()

        self.assertFalse(p.is_done())
        self.assertFalse(p.poll().present)

        p.set_value(420)
        self.assertTrue(p.is_done())
        self.assertEqual(p.poll().must(), 420)
        self.assertEqual(await p.wait(), 420)

    async def test_none_value(self):
        p = SyncAsynclite().make_promise()

        p.set_value(None)
        self.assertTrue(p.is_done())
        self.assertTrue(p.poll().present)
        self.assertIsNone(p.poll().must())
        self.assertIsNone(await p.wait())

    async def test_already_set(self):
        p = SyncAsynclite().make_promise()

        p.set_value(420)
        with self.assertRaises(AsynclitePromiseAlreadySetError):
            p.set_value(421)
        with self.assertRaises(AsynclitePromiseAlreadySetError):
            p.set_error(RuntimeError())

    async def test_error(self):
        class FooError(Exception):
            pass

        p = SyncAsynclite().make_promise()

        p.set_error(FooError())
        self.assertTrue(p.is_done())

        for _ in range(2):
            with self.assertRaises(FooError):
                p.poll()
            with self.assertRaises(FooError):
                await p.wait()

    async def test_timeout(self):
        p = SyncAsynclite().make_promise()

        with self.assertRaises(AsynclitePromiseWaitTimeoutError):
            await p.wait(timeout=0)

        p.set_value(420)
        self.assertEqual(await p.wait(timeout=0), 420)

    async def test_done_promise_sheds_machinery(self):
        p = SyncAsynclite().make_promise()
        assert isinstance(p, EventAsynclitePromise)

        self.assertIsNotNone(p._ev)
        self.assertIsNotNone(p._mtx)

        p.set_value(420)
        self.assertIsNone(p._ev)
        self.assertIsNone(p._mtx)

        self.assertTrue(p.is_done())
        self.assertEqual(p.poll().must(), 420)
        self.assertEqual(await p.wait(), 420)
        with self.assertRaises(AsynclitePromiseAlreadySetError):
            p.set_value(421)

    async def test_error_promise_sheds_machinery(self):
        class FooError(Exception):
            pass

        p = SyncAsynclite().make_promise()
        assert isinstance(p, EventAsynclitePromise)

        p.set_error(FooError())
        self.assertIsNone(p._ev)
        self.assertIsNone(p._mtx)

        with self.assertRaises(FooError):
            await p.wait()
        with self.assertRaises(AsynclitePromiseAlreadySetError):
            p.set_value(420)

    async def test_cross_thread(self):
        p = SyncAsynclite().make_promise()
        entered = threading.Event()

        def setter():
            entered.wait(30)
            p.set_value(420)

        t = threading.Thread(target=setter)
        t.start()
        try:
            entered.set()
            self.assertEqual(await p.wait(timeout=30), 420)
        finally:
            t.join(30)
