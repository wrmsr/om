# ruff: noqa: UP006 UP007 UP045
import abc
import asyncio
import struct
import typing as ta

from omcore.lite.abstract import Abstract
from omcore.lite.check import check

from .errors import RpcConnectionClosedError
from .errors import RpcProtocolError
from .messages import JsonRpcMessageCodec
from .messages import RpcMessage
from .messages import RpcMessageCodec


##


DEFAULT_RPC_MAX_FRAME_BYTES = 16 * 1024 * 1024

_FRAME_HEADER = struct.Struct('!I')


class RpcStreamReader(ta.Protocol):
    def readexactly(self, size: int) -> ta.Awaitable[bytes]:
        raise NotImplementedError


class RpcStreamWriter(ta.Protocol):
    def write(self, data: bytes) -> None:
        raise NotImplementedError

    def drain(self) -> ta.Awaitable[None]:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def wait_closed(self) -> ta.Awaitable[None]:
        raise NotImplementedError


class RpcChannel(Abstract):
    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def send(self, message: RpcMessage) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def receive(self) -> ta.Awaitable[ta.Optional[RpcMessage]]:
        raise NotImplementedError

    @abc.abstractmethod
    def aclose(self) -> ta.Awaitable[None]:
        raise NotImplementedError


class AsyncioStreamRpcChannel(RpcChannel):
    def __init__(
            self,
            reader: RpcStreamReader,
            writer: RpcStreamWriter,
            *,
            codec: ta.Optional[RpcMessageCodec] = None,
            max_frame_bytes: int = DEFAULT_RPC_MAX_FRAME_BYTES,
    ) -> None:
        super().__init__()

        check.arg(max_frame_bytes > 0)

        self._reader = reader
        self._writer = writer
        self._codec = codec if codec is not None else JsonRpcMessageCodec()
        self._max_frame_bytes = max_frame_bytes

        self._read_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    async def send(self, message: RpcMessage) -> None:
        if self._closed:
            raise RpcConnectionClosedError('RPC channel is closed')

        payload = self._codec.encode(message)
        if len(payload) > self._max_frame_bytes:
            raise RpcProtocolError(
                f'RPC frame is {len(payload)} bytes, exceeding limit {self._max_frame_bytes}',
            )

        frame = _FRAME_HEADER.pack(len(payload)) + payload
        async with self._write_lock:
            if self._closed:
                raise RpcConnectionClosedError('RPC channel is closed')
            try:
                self._writer.write(frame)
                await self._writer.drain()
            except (BrokenPipeError, ConnectionError, OSError) as e:
                raise RpcConnectionClosedError('RPC channel write failed') from e

    async def _read_exactly(self, size: int, *, allow_eof: bool = False) -> ta.Optional[bytes]:
        try:
            return await self._reader.readexactly(size)
        except asyncio.IncompleteReadError as e:
            if allow_eof and not e.partial:
                return None
            raise RpcProtocolError(
                f'RPC connection closed within a frame: expected {size} bytes, received {len(e.partial)}',
            ) from e
        except (ConnectionError, OSError) as e:
            raise RpcConnectionClosedError('RPC channel read failed') from e

    async def receive(self) -> ta.Optional[RpcMessage]:
        async with self._read_lock:
            if self._closed:
                return None

            header = await self._read_exactly(_FRAME_HEADER.size, allow_eof=True)
            if header is None:
                return None
            size = _FRAME_HEADER.unpack(header)[0]
            if size > self._max_frame_bytes:
                raise RpcProtocolError(
                    f'RPC frame is {size} bytes, exceeding limit {self._max_frame_bytes}',
                )

            payload = ta.cast(bytes, await self._read_exactly(size))
            return self._codec.decode(payload)

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True

        try:
            self._writer.close()
            await self._writer.wait_closed()
        except (BrokenPipeError, ConnectionError, OSError):
            pass
