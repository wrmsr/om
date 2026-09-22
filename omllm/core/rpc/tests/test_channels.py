# ruff: noqa: UP006 UP007 UP045
import asyncio
import struct
import unittest

from ..channels import AsyncioStreamRpcChannel
from ..errors import RpcProtocolError
from ..messages import JsonRpcMessageCodec
from ..messages import RpcPingMessage
from .support import memory_rpc_stream


##


class TestAsyncioStreamRpcChannel(unittest.IsolatedAsyncioTestCase):
    async def test_roundtrip(self) -> None:
        reader, writer = memory_rpc_stream()
        channel = AsyncioStreamRpcChannel(reader, writer)
        message = RpcPingMessage(1)

        await channel.send(message)
        self.assertEqual(await channel.receive(), message)
        await channel.aclose()

    async def test_clean_eof(self) -> None:
        reader, writer = memory_rpc_stream()
        channel = AsyncioStreamRpcChannel(reader, writer)

        writer.close()
        self.assertIsNone(await channel.receive())

    async def test_partial_header(self) -> None:
        reader, writer = memory_rpc_stream()
        channel = AsyncioStreamRpcChannel(reader, writer)

        writer.write(b'\x00\x00')
        writer.close()
        with self.assertRaises(RpcProtocolError):
            await channel.receive()

    async def test_partial_payload(self) -> None:
        reader, writer = memory_rpc_stream()
        channel = AsyncioStreamRpcChannel(reader, writer)

        writer.write(struct.pack('!I', 10) + b'abc')
        writer.close()
        with self.assertRaises(RpcProtocolError):
            await channel.receive()

    async def test_oversized_inbound_frame(self) -> None:
        reader, writer = memory_rpc_stream()
        channel = AsyncioStreamRpcChannel(reader, writer, max_frame_bytes=10)

        writer.write(struct.pack('!I', 11))
        with self.assertRaises(RpcProtocolError):
            await channel.receive()
        await channel.aclose()

    async def test_oversized_outbound_frame(self) -> None:
        reader, writer = memory_rpc_stream()
        channel = AsyncioStreamRpcChannel(reader, writer, max_frame_bytes=10)

        with self.assertRaises(RpcProtocolError):
            await channel.send(RpcPingMessage(1))
        await channel.aclose()

    async def test_fragmented_frame(self) -> None:
        reader, writer = memory_rpc_stream()
        channel = AsyncioStreamRpcChannel(reader, writer)
        payload = JsonRpcMessageCodec().encode(RpcPingMessage(1))
        frame = struct.pack('!I', len(payload)) + payload

        receive = asyncio.create_task(channel.receive())
        loop = asyncio.get_running_loop()
        for byte in frame:
            loop.call_soon(writer.write, bytes([byte]))

        self.assertEqual(await receive, RpcPingMessage(1))
        await channel.aclose()
