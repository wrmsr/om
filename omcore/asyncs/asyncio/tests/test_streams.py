# ruff: noqa: UP006 UP007 UP045
# @om-lite
import asyncio
import os
import unittest

from ..streams import asyncio_open_stream_reader
from ..streams import asyncio_open_stream_writer


class TestAsyncioStreams(unittest.IsolatedAsyncioTestCase):
    async def test_writer_wait_closed(self) -> None:
        # StreamWriter.wait_closed awaits a close waiter from the writer's protocol; a bare FlowControlMixin raises
        # NotImplementedError instead of providing one.
        r, w = os.pipe()
        reader = await asyncio_open_stream_reader(os.fdopen(r, 'rb', 0))
        writer = await asyncio_open_stream_writer(os.fdopen(w, 'wb', 0))

        writer.write(b'hello')
        await writer.drain()
        writer.close()
        await asyncio.wait_for(writer.wait_closed(), 5.)

        self.assertEqual(await asyncio.wait_for(reader.read(), 5.), b'hello')

    async def test_writer_wait_closed_reports_a_failed_close(self) -> None:
        r, w = os.pipe()
        writer = await asyncio_open_stream_writer(os.fdopen(w, 'wb', 0))
        os.close(r)

        # Fails synchronously, before the loop runs: the write is attempted immediately and hits EPIPE.
        writer.write(b'hello')
        writer.close()
        with self.assertRaises(BrokenPipeError):
            await asyncio.wait_for(writer.wait_closed(), 5.)
