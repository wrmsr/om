"""
An asyncio JSON-RPC server: accept connections on a unix or tcp endpoint and run one AsyncioJsonrpcConnection per
connection. Each connection is a full peer, so the server may call back into its clients (as MCP sampling and ACP
permission requests require) by way of the connection handed to its dispatcher and hooks.
"""
import asyncio
import typing as ta

from ..... import check
from ..... import dataclasses as dc
from .....logs import all as logs
from .....sockets.endpoints import SocketEndpoint
from .....sockets.transports.asyncio import DEFAULT_ASYNCIO_SOCKET_TRANSPORT
from .....sockets.transports.asyncio import AsyncioSocketListener
from .....sockets.transports.asyncio import AsyncioSocketTransport
from ...dispatch import AsyncJsonrpcDispatcher
from ...errors import JsonrpcTimeoutError
from ..asyncio import AsyncioJsonrpcConnection
from ..asyncio import AsyncioJsonrpcConnections
from ..asyncio import AsyncJsonrpcNotificationHandler
from ..configs import JsonrpcPipelineConfig


log = logs.get_module_logger(globals())


AsyncioJsonrpcConnectionFactory: ta.TypeAlias = ta.Callable[
    [asyncio.StreamReader, asyncio.StreamWriter],
    AsyncioJsonrpcConnection,
]

AsyncioJsonrpcConnectionHook: ta.TypeAlias = ta.Callable[
    [AsyncioJsonrpcConnection],
    ta.Awaitable[None],
]


##


@dc.dataclass(frozen=True, kw_only=True)
class AsyncioJsonrpcServerConfig:
    endpoint: SocketEndpoint

    backlog: int = 128
    unix_socket_mode: int = 0o600

    # Connections beyond this many are closed immediately on accept.
    max_connections: int | None = None

    # How long `close` waits for connections to finish gracefully before aborting them.
    drain_timeout_s: float | None = 10.

    pipeline: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT

    def __post_init__(self) -> None:
        check.arg(self.backlog > 0)
        check.arg(0 <= self.unix_socket_mode <= 0o777)
        if self.max_connections is not None:
            check.arg(self.max_connections > 0)
        if self.drain_timeout_s is not None:
            check.arg(self.drain_timeout_s > 0.)


class AsyncioJsonrpcServer:
    """
    Per connection, either `connection_factory` builds the connection (for custom connection classes), or one is built
    from `dispatcher`, `notification_handler`, and `connection_kwargs`. `on_connection` then runs once the connection
    has started, for per-connection setup such as server-initiated requests; the connection lives on after it returns
    until the peer closes or something calls its `close`.
    """

    def __init__(
            self,
            config: AsyncioJsonrpcServerConfig,
            *,
            dispatcher: AsyncJsonrpcDispatcher | None = None,
            notification_handler: AsyncJsonrpcNotificationHandler | None = None,
            connection_kwargs: ta.Mapping[str, ta.Any] | None = None,
            connection_factory: AsyncioJsonrpcConnectionFactory | None = None,
            on_connection: AsyncioJsonrpcConnectionHook | None = None,
            transport: AsyncioSocketTransport = DEFAULT_ASYNCIO_SOCKET_TRANSPORT,
    ) -> None:
        super().__init__()

        self._config = config
        self._dispatcher = dispatcher
        self._notification_handler = notification_handler
        self._connection_kwargs = dict(connection_kwargs or {})
        self._connection_factory = connection_factory
        self._on_connection = on_connection
        self._transport = transport

        self._listener: AsyncioSocketListener | None = None
        self._closing = False

        self._connection_tasks: dict[asyncio.Task, AsyncioJsonrpcConnection | None] = {}

    @property
    def config(self) -> AsyncioJsonrpcServerConfig:
        return self._config

    @property
    def is_started(self) -> bool:
        return self._listener is not None

    @property
    def bound_endpoint(self) -> SocketEndpoint:
        """The endpoint actually bound, which differs from the configured one when a tcp port of zero was asked for."""

        return check.not_none(self._listener).bound_endpoint

    @property
    def connections(self) -> ta.Sequence[AsyncioJsonrpcConnection]:
        return [c for c in self._connection_tasks.values() if c is not None]

    ##
    # lifecycle

    async def start(self) -> None:
        check.state(self._listener is None and not self._closing, 'already started or closed')

        self._listener = await self._transport.listen(
            self._config.endpoint,
            self._accept,
            backlog=self._config.backlog,
            unix_socket_mode=self._config.unix_socket_mode,
        )

    async def serve_forever(self) -> ta.NoReturn:
        await check.not_none(self._listener).serve_forever()
        raise RuntimeError('server stopped serving')

    async def close(self, *, graceful: bool = True) -> None:
        """
        Stop accepting, then close every connection, gracefully by default (bounded by the drain timeout, after which
        connections are aborted).
        """

        if self._closing:
            return
        self._closing = True

        # Connections first: since 3.12 an asyncio server's wait_closed waits for its accepted transports too, so
        # closing the listener before the connections would wait on the peers instead. New arrivals meanwhile are
        # refused by _accept.
        conns = [c for c in self._connection_tasks.values() if c is not None]
        if conns:
            await asyncio.gather(
                *[c.close(graceful=graceful, timeout_s=self._config.drain_timeout_s) for c in conns],
                return_exceptions=True,
            )

        pending: set[asyncio.Task] = set()
        if (tasks := list(self._connection_tasks)):
            _, pending = await asyncio.wait(tasks, timeout=self._config.drain_timeout_s)
            for t in pending:
                t.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

        if (listener := self._listener) is not None:
            self._listener = None
            await listener.close()

        if pending:
            raise JsonrpcTimeoutError('server connections did not drain before timeout')

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close(graceful=exc_type is None)

    ##
    # connections

    def _new_connection(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ) -> AsyncioJsonrpcConnection:
        if (f := self._connection_factory) is not None:
            return f(reader, writer)

        return AsyncioJsonrpcConnections.of_streams(
            reader,
            writer,
            self._config.pipeline,
            dispatcher=self._dispatcher,
            notification_handler=self._notification_handler,
            **self._connection_kwargs,
        )

    def _accept(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        if self._closing or (
                (mx := self._config.max_connections) is not None and
                len(self._connection_tasks) >= mx
        ):
            log.warning('Refusing connection: %s', 'closing' if self._closing else 'at connection limit')
            writer.close()
            return

        task = asyncio.create_task(
            self._run_connection(reader, writer),
            name=f'{type(self).__name__}._run_connection',
        )
        self._connection_tasks[task] = None
        task.add_done_callback(lambda t: self._connection_tasks.pop(t, None))

    async def _run_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        task = check.not_none(asyncio.current_task())

        try:
            conn = self._new_connection(reader, writer)
        except Exception:  # noqa
            log.exception('Error building connection')
            writer.close()
            return

        self._connection_tasks[task] = conn

        try:
            async with conn:
                if (hook := self._on_connection) is not None:
                    await hook(conn)
                await conn.wait_closed()

        except asyncio.CancelledError:
            raise

        except Exception:  # noqa
            log.exception('Unhandled connection error')

        finally:
            writer.close()
