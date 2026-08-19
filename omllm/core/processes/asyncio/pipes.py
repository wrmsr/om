"""
Pipe plumbing without asyncio's subprocess transport (which would hand reaping to its child watcher). The manager
creates the pipes, and uses `loop.connect_read_pipe` / `loop.connect_write_pipe` on our ends. Note the transports take
ownership of (and close) the file objects handed to them.
"""
import asyncio
import typing as ta

from ..managers.process import ProcessStdinWriter


##


class ReadPipeProtocol(asyncio.Protocol):
    def __init__(
            self,
            on_data: ta.Callable[[bytes], None],
            on_eof: ta.Callable[[BaseException | None], None],
    ) -> None:
        super().__init__()

        self._on_data = on_data
        self._on_eof = on_eof
        self._transport: asyncio.ReadTransport | None = None
        self._eof = False

    @property
    def transport(self) -> asyncio.ReadTransport | None:
        return self._transport

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._transport = ta.cast(asyncio.ReadTransport, transport)

    def data_received(self, data: bytes) -> None:
        if data:
            self._on_data(data)

    def eof_received(self) -> None:
        pass

    def connection_lost(self, exc: BaseException | None) -> None:
        if self._eof:
            return
        self._eof = True
        self._on_eof(exc)


class WritePipeProtocol(asyncio.BaseProtocol):
    def __init__(self) -> None:
        super().__init__()

        self._paused: bool = False
        self._closed: bool = False
        self._exc: BaseException | None = None
        self._waiters: list[asyncio.Future[None]] = []

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def exc(self) -> BaseException | None:
        return self._exc

    def _wake(self) -> None:
        waiters, self._waiters = self._waiters, []
        for w in waiters:
            if not w.done():
                w.set_result(None)

    def pause_writing(self) -> None:
        self._paused = True

    def resume_writing(self) -> None:
        self._paused = False
        self._wake()

    def connection_lost(self, exc: BaseException | None) -> None:
        self._closed = True
        self._exc = exc
        self._wake()

    async def drain(self) -> None:
        if self._closed:
            if self._exc is not None:
                raise self._exc
            raise BrokenPipeError('stdin closed')
        if not self._paused:
            return
        fut = asyncio.get_running_loop().create_future()
        self._waiters.append(fut)
        await fut
        if self.closed and self._exc is not None:
            raise self._exc


class StdinWriter(ProcessStdinWriter):
    def __init__(self, transport: asyncio.WriteTransport, protocol: WritePipeProtocol) -> None:
        super().__init__()

        self._transport = transport
        self._protocol = protocol
        self._eof = False

    @property
    def closed(self) -> bool:
        return self._eof or self._protocol.closed

    async def write(self, data: bytes) -> None:
        if self.closed:
            raise BrokenPipeError('stdin closed')
        if not data:
            return
        self._transport.write(data)
        await self._protocol.drain()

    async def write_eof(self) -> None:
        if self._eof:
            return
        self._eof = True
        # For pipe transports close() flushes buffered data then closes - i.e. EOF to the child.
        self._transport.close()

    def abort(self) -> None:
        self._eof = True
        if not self._transport.is_closing():
            self._transport.abort()


##


class StatusPipeProtocol(asyncio.Protocol):
    """Collects the exec-status pipe: EOF with nothing == exec happened; any bytes == a marshal'd shim error."""

    def __init__(self, fut: asyncio.Future[bytes]) -> None:
        super().__init__()

        self._fut = fut
        self._buf = bytearray()

    def data_received(self, data: bytes) -> None:
        self._buf += data

    def connection_lost(self, exc: BaseException | None) -> None:
        if not self._fut.done():
            self._fut.set_result(bytes(self._buf))
