import asyncio
import types
import typing as ta

from omcore.io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from omcore.io.pipelines.drivers.types import IoPipelineDriverState

from ..converters import InAdapter
from ..exceptions import InterfaceError
from ..protocol import messages as msgs
from ..protocol.session import Columns
from ..protocol.session import Context
from ..protocol.session import CopyStream
from ..protocol.session import Operation
from ..protocol.session import PreparedStatementInfo
from .base import BaseCoreConnection
from .handlers import OperationRequest
from .handlers import make_pipeline_spec
from .sockets import SslContextArg


T = ta.TypeVar('T')


##


class AsyncCoreConnection(BaseCoreConnection):
    """Constructed via `connect`, as establishing the connection requires awaiting."""

    def __init__(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            *,
            user: str | bytes,
            password: str | bytes | None = None,
            database: str | bytes | None = None,
            application_name: str | bytes | None = None,
            replication: str | bytes | None = None,
            startup_params: ta.Mapping[str, str | bytes] | None = None,
            ssl_context: SslContextArg = None,
            server_hostname: str | None = None,
    ) -> None:
        super().__init__(
            user=user,
            password=password,
            database=database,
            application_name=application_name,
            replication=replication,
            startup_params=startup_params,
            ssl_context=ssl_context,
            server_hostname=server_hostname,
        )

        self._driver = PollAsyncioStreamIoPipelineDriver(make_pipeline_spec(self._session), reader, writer)

    @classmethod
    async def connect(
            cls,
            user: str | bytes,
            host: str | None = 'localhost',
            database: str | bytes | None = None,
            port: int = 5432,
            password: str | bytes | None = None,
            unix_sock: str | None = None,
            ssl_context: SslContextArg = None,
            application_name: str | bytes | None = None,
            replication: str | bytes | None = None,
            startup_params: ta.Mapping[str, str | bytes] | None = None,
    ) -> ta.Self:
        if unix_sock is not None:
            reader, writer = await asyncio.open_unix_connection(unix_sock)
        elif host is not None:
            reader, writer = await asyncio.open_connection(host, port)
        else:
            raise InterfaceError('one of host or unix_sock must be provided')

        conn = cls(
            reader,
            writer,
            user=user,
            password=password,
            database=database,
            application_name=application_name,
            replication=replication,
            startup_params=startup_params,
            ssl_context=ssl_context,
            server_hostname=host,
        )

        try:
            await conn._start()  # noqa: SLF001
        except BaseException:
            await conn._driver.close()  # noqa: SLF001
            raise

        return conn

    async def _start(self) -> None:
        if self._wants_ssl():
            accepted = await self._run(self._session.negotiate_ssl())
            if (ssl_handler := self._on_ssl_response(accepted)) is not None:
                self._driver.pipeline.add_outermost(ssl_handler)

        await self._run(self._session.startup())

    async def __aenter__(self) -> ta.Self:
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: types.TracebackType | None,
    ) -> None:
        await self.close()

    @property
    def is_closed(self) -> bool:
        return self._driver.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)

    async def _run(self, op: Operation[T]) -> T:
        if self.is_closed:
            raise InterfaceError('connection is closed')

        self._driver.enqueue(OperationRequest(op))
        while True:
            try:
                out = await self._driver.next()
            except OSError as e:
                raise InterfaceError('network error') from e
            if self._check_output(op, out, running=not self.is_closed):
                break
        return op.result()

    async def close(self) -> None:
        if self.is_closed:
            raise InterfaceError('connection is closed')

        try:
            self._driver.enqueue(msgs.Terminate())
            await self._driver.next(read=False)
        finally:
            await self._driver.close()

    async def execute_simple(self, statement: str) -> Context:
        return await self._run(self._session.execute_simple(statement))

    async def execute_unnamed(
            self,
            statement: str,
            vals: ta.Iterable[ta.Any] = (),
            oids: ta.Sequence[int] = (),
            stream: CopyStream | None = None,
    ) -> Context:
        return await self._run(self._session.execute_unnamed(statement, vals, oids, stream))

    async def prepare_statement(
            self,
            statement: str,
            oids: ta.Sequence[int] | None = None,
    ) -> PreparedStatementInfo:
        return await self._run(self._session.prepare_statement(statement, oids))

    async def execute_named(
            self,
            name: str,
            params: ta.Sequence[str | None],
            columns: Columns | None,
            input_funcs: ta.Sequence[InAdapter],
            statement: str,
    ) -> Context:
        return await self._run(self._session.execute_named(name, params, columns, input_funcs, statement))

    async def close_prepared_statement(self, name: str) -> None:
        await self._run(self._session.close_prepared_statement(name))
