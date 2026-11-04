"""
The asyncio connection: the JSON-RPC connection (`base.py`) on an `omcore.rpc` asyncio runtime over a
PollAsyncioStreamDriver.

One pump task owns the driver, looping on `next()` and handing every event to the connection. Callers of `request` await
a promise the pump resolves; inbound requests each run in a tracked task, cancelled if the session gives up on them or
the connection closes. The session enforces every timeout, so nothing here needs its own, other than the optional bound
on `close`.
"""
import asyncio
import errno
import socket
import sys
import typing as ta

from .... import check
from .... import lang
from ....asyncs.asyncio.streams import asyncio_open_stream_reader
from ....asyncs.asyncio.streams import asyncio_open_stream_writer
from ....asyncs.asyncio.timeouts import asyncio_maybe_timeout
from ....io.pipelines import all as ipl
from ....rpc import all as rpc
from ..dispatch import AsyncJsonrpcDispatcher
from ..ids import JsonrpcIdCreatorLike
from .base import AsyncJsonrpcNotificationHandler
from .base import BaseJsonrpcConnection
from .configs import JsonrpcPipelineConfig
from .specs import build_jsonrpc_pipeline_spec


##


class AsyncioJsonrpcConnection(BaseJsonrpcConnection):
    """
    Must be started (via `start` or `async with`) before use, and pumps only while its task runs: a connection which
    is never started never reads its transport.
    """

    def __init__(
            self,
            driver: ipl.PollAsyncioStreamDriver,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            dispatcher: AsyncJsonrpcDispatcher | None = None,
            notification_handler: AsyncJsonrpcNotificationHandler | None = None,
            id_creator: JsonrpcIdCreatorLike | None = None,
            include_error_details: bool = False,
            send_timeout_s: float | None = None,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
    ) -> None:
        super().__init__(
            rpc.AsyncioRuntime(driver, closers=closers),
            config,
            dispatcher=dispatcher,
            notification_handler=notification_handler,
            id_creator=id_creator,
            include_error_details=include_error_details,
            send_timeout_s=send_timeout_s,
        )

        self._driver = driver

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._driver!r}>'

    @property
    def driver(self) -> ipl.PollAsyncioStreamDriver:
        return self._driver


##
# construction helpers


def _try_set_nodelay(sock: socket.socket) -> None:
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError as e:
        if e.errno != errno.ENOPROTOOPT:
            raise


class AsyncioJsonrpcConnections(lang.Namespace):
    """Factories taping the connection onto the transports in use: sockets, a subprocess's stdio, or our own."""

    @staticmethod
    def of_streams(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            driver_config: ipl.PollAsyncioStreamDriver.Config | None = None,
            ssl_kwargs: ta.Mapping[str, ta.Any] | None = None,
            spec_kwargs: ta.Mapping[str, ta.Any] | None = None,
            **kwargs: ta.Any,
    ) -> AsyncioJsonrpcConnection:
        spec = build_jsonrpc_pipeline_spec(
            config,
            ssl_kwargs=ssl_kwargs,
            **(spec_kwargs or {}),
        )
        driver = ipl.PollAsyncioStreamDriver(spec, reader, writer, driver_config)
        return AsyncioJsonrpcConnection(driver, config, **kwargs)

    @classmethod
    async def connect_tcp(
            cls,
            host: str,
            port: int,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            connect_timeout_s: float | None = 10.,
            ssl: bool | ta.Mapping[str, ta.Any] = False,
            **kwargs: ta.Any,
    ) -> AsyncioJsonrpcConnection:
        reader, writer = await asyncio_maybe_timeout(
            asyncio.open_connection(host, port),
            connect_timeout_s,
        )

        try:
            if (sock := writer.get_extra_info('socket')) is not None:
                _try_set_nodelay(sock)

            ssl_kwargs: ta.Mapping[str, ta.Any] | None
            if ssl is True:
                ssl_kwargs = dict(server_side=False, server_hostname=host)
            elif ssl is False:
                ssl_kwargs = None
            else:
                ssl_kwargs = ssl

            return cls.of_streams(reader, writer, config, ssl_kwargs=ssl_kwargs, **kwargs)

        except BaseException:
            writer.close()
            raise

    @classmethod
    async def connect_unix(
            cls,
            path: str,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            connect_timeout_s: float | None = 10.,
            **kwargs: ta.Any,
    ) -> AsyncioJsonrpcConnection:
        reader, writer = await asyncio_maybe_timeout(
            asyncio.open_unix_connection(path),
            connect_timeout_s,
        )

        try:
            return cls.of_streams(reader, writer, config, **kwargs)
        except BaseException:
            writer.close()
            raise

    @classmethod
    def of_subprocess(
            cls,
            proc: asyncio.subprocess.Process,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            **kwargs: ta.Any,
    ) -> AsyncioJsonrpcConnection:
        """Talk to a child process over its stdio. The process must have been created with piped stdin and stdout."""

        return cls.of_streams(
            check.not_none(proc.stdout),
            check.not_none(proc.stdin),
            config,
            **kwargs,
        )

    @classmethod
    async def of_stdio(
            cls,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            stdin: ta.IO | None = None,
            stdout: ta.IO | None = None,
            **kwargs: ta.Any,
    ) -> AsyncioJsonrpcConnection:
        """Serve or talk over this process's own stdio, as a stdio MCP or ACP server does."""

        reader = await asyncio_open_stream_reader(stdin if stdin is not None else sys.stdin.buffer)
        writer = await asyncio_open_stream_writer(stdout if stdout is not None else sys.stdout.buffer)

        return cls.of_streams(reader, writer, config, **kwargs)
