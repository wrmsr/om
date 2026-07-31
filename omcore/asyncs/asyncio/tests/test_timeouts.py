# ruff: noqa: PT027
# @om-lite
import asyncio
import unittest

from ..timeouts import asyncio_maybe_timeout


class TestAsyncioMaybeTimeout(unittest.IsolatedAsyncioTestCase):
    async def test_no_timeout(self):
        future = asyncio.get_running_loop().create_future()
        self.assertIs(asyncio_maybe_timeout(future), future)

        future.set_result(42)
        self.assertEqual(await future, 42)

    async def test_timeout(self):
        event = asyncio.Event()

        with self.assertRaises(TimeoutError):
            await asyncio_maybe_timeout(event.wait(), 0.)

        future = asyncio.get_running_loop().create_future()
        with self.assertRaises(TimeoutError):
            asyncio_maybe_timeout(future, 0.)
        self.assertTrue(future.cancelled())
