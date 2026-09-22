# ruff: noqa: UP006 UP007 UP045
import asyncio
import typing as ta

from ..channels import RpcStreamReader
from ..channels import RpcStreamWriter


##


class MemoryRpcStreamWriter(RpcStreamWriter):
    def __init__(self, target: asyncio.StreamReader) -> None:
        super().__init__()

        self._target = target
        self._closed = asyncio.Event()

    def write(self, data: bytes) -> None:
        if self._closed.is_set():
            raise BrokenPipeError
        self._target.feed_data(data)

    async def drain(self) -> None:
        if self._closed.is_set():
            raise BrokenPipeError

    def close(self) -> None:
        if self._closed.is_set():
            return
        self._closed.set()
        self._target.feed_eof()

    async def wait_closed(self) -> None:
        await self._closed.wait()


def memory_rpc_stream() -> ta.Tuple[RpcStreamReader, RpcStreamWriter]:
    reader = asyncio.StreamReader()
    return reader, MemoryRpcStreamWriter(reader)


def memory_rpc_stream_pair() -> ta.Tuple[
        ta.Tuple[RpcStreamReader, RpcStreamWriter],
        ta.Tuple[RpcStreamReader, RpcStreamWriter],
]:
    left_reader = asyncio.StreamReader()
    right_reader = asyncio.StreamReader()
    return (
        (left_reader, MemoryRpcStreamWriter(right_reader)),
        (right_reader, MemoryRpcStreamWriter(left_reader)),
    )
