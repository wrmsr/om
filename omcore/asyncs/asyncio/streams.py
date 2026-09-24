# ruff: noqa: UP006 UP007 UP045
# @om-lite
import asyncio
import typing as ta


##


ASYNCIO_DEFAULT_BUFFER_LIMIT = 2 ** 16


async def asyncio_open_stream_reader(
        f: ta.IO,
        loop: ta.Any = None,
        *,
        limit: int = ASYNCIO_DEFAULT_BUFFER_LIMIT,
) -> asyncio.StreamReader:
    if loop is None:
        loop = asyncio.get_running_loop()

    reader = asyncio.StreamReader(limit=limit, loop=loop)
    await loop.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(reader, loop=loop),
        f,
    )

    return reader


class AsyncioWritePipeProtocol(asyncio.streams.FlowControlMixin):
    """
    The protocol behind `asyncio_open_stream_writer`: flow control, plus the close waiter that
    `StreamWriter.wait_closed` awaits through the protocol's `_get_close_waiter` hook. A bare `FlowControlMixin` raises
    NotImplementedError there.
    """

    def __init__(self, loop: ta.Any = None) -> None:
        super().__init__(loop=loop)

        self._close_waiter: asyncio.Future = self._loop.create_future()  # type: ignore[attr-defined]

    def connection_lost(self, exc: ta.Optional[Exception]) -> None:
        if not self._close_waiter.done():
            if exc is None:
                self._close_waiter.set_result(None)
            else:
                self._close_waiter.set_exception(exc)
                # Marked retrieved: a failed close nobody waits for is not an unhandled error.
                self._close_waiter.exception()
        super().connection_lost(exc)

    def _get_close_waiter(self, stream: asyncio.StreamWriter) -> asyncio.Future:
        return self._close_waiter


async def asyncio_open_stream_writer(
        f: ta.IO,
        loop: ta.Any = None,
) -> asyncio.StreamWriter:
    if loop is None:
        loop = asyncio.get_running_loop()

    writer_transport, writer_protocol = await loop.connect_write_pipe(
        lambda: AsyncioWritePipeProtocol(loop=loop),
        f,
    )

    return asyncio.streams.StreamWriter(
        writer_transport,
        writer_protocol,
        None,
        loop,
    )
