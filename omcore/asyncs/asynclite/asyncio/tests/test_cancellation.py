# @om-lite
import asyncio

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ..cancellation import AsyncioAsyncliteCancellation


class TestAsyncioCancellation(AsyncioIsolatedAsyncTestCase):
    async def test_is_cancelled_error(self):
        api = AsyncioAsyncliteCancellation()

        self.assertTrue(api.is_cancelled_exception(asyncio.CancelledError()))
        self.assertFalse(api.is_cancelled_exception(ValueError()))
        self.assertFalse(api.is_cancelled_exception(KeyboardInterrupt()))

    async def test_is_cancelling_tells_own_cancellation_from_a_stray_one(self):
        api = AsyncioAsyncliteCancellation()
        seen = []

        # Before 3.11 there is no telling, and every cancellation error is taken as the task's own.
        can_tell = hasattr(asyncio.Task, 'cancelling')

        self.assertEqual(api.is_self_cancelling(), not can_tell)

        async def own():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                seen.append(('own', api.is_self_cancelling()))
                raise

        task = asyncio.create_task(own())
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        fut = asyncio.get_running_loop().create_future()

        async def stray():
            try:
                await fut
            except asyncio.CancelledError:
                seen.append(('stray', api.is_self_cancelling()))

        task = asyncio.create_task(stray())
        await asyncio.sleep(0)
        fut.cancel()
        await task

        self.assertEqual(seen, [('own', True), ('stray', not can_tell)])

    async def test_shield_runs_to_completion_then_delivers_the_cancellation(self):
        api = AsyncioAsyncliteCancellation()
        started = asyncio.Event()
        release = asyncio.Event()
        done = []

        async def fn():
            started.set()
            await release.wait()
            done.append(True)
            return 'ok'

        async def body():
            return await api.cancellation_shield(fn)

        task = asyncio.create_task(body())
        await started.wait()

        task.cancel()
        await asyncio.sleep(0)
        self.assertFalse(task.done())
        self.assertEqual(done, [])

        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(done, [True])

    async def test_shield_survives_repeated_cancellation(self):
        api = AsyncioAsyncliteCancellation()
        started = asyncio.Event()
        release = asyncio.Event()

        async def fn():
            started.set()
            await release.wait()
            return 'ok'

        async def body():
            return await api.cancellation_shield(fn)

        task = asyncio.create_task(body())
        await started.wait()

        for _ in range(3):
            task.cancel()
            await asyncio.sleep(0)
        self.assertFalse(task.done())

        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await task

    async def test_shield_returns_the_result_when_not_cancelled(self):
        api = AsyncioAsyncliteCancellation()

        async def fn():
            await asyncio.sleep(0)
            return 42

        self.assertEqual(await api.cancellation_shield(fn), 42)

    async def test_shield_propagates_the_functions_own_error(self):
        api = AsyncioAsyncliteCancellation()

        async def fn():
            await asyncio.sleep(0)
            raise ValueError('boom')

        with self.assertRaises(ValueError):
            await api.cancellation_shield(fn)

    async def test_shield_timeout_cancels_the_function(self):
        api = AsyncioAsyncliteCancellation()
        seen = []

        async def fn():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                seen.append('cancelled')
                raise

        with self.assertRaises(TimeoutError):
            await api.cancellation_shield(fn, timeout=.05)
        self.assertEqual(seen, ['cancelled'])

    async def test_shield_timeout_yields_to_a_deferred_cancellation(self):
        api = AsyncioAsyncliteCancellation()
        started = asyncio.Event()

        async def fn():
            started.set()
            await asyncio.sleep(10)

        async def body():
            return await api.cancellation_shield(fn, timeout=.05)

        task = asyncio.create_task(body())
        await started.wait()
        task.cancel()

        with self.assertRaises(asyncio.CancelledError):
            await task
