import socket
import types
import typing as ta

from omcore.io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from omcore.io.pipelines.drivers.types import IoPipelineDriverState

from ..converters import InAdapter
from ..errors import InterfaceError
from ..protocol import messages as msgs
from ..protocol.session import Columns
from ..protocol.session import Context
from ..protocol.session import CopyStream
from ..protocol.session import Operation
from ..protocol.session import PreparedStatementInfo
from .base import BaseCoreConnection
from .handlers import OperationRequest
from .sockets import SslContextArg
from .sockets import connect_socket


T = ta.TypeVar('T')


##


class SyncCoreConnection(BaseCoreConnection):
    def __init__(
            self,
            user: str | bytes,
            host: str | None = 'localhost',
            database: str | bytes | None = None,
            port: int = 5432,
            password: str | bytes | None = None,
            source_address: tuple[str, int] | None = None,
            unix_sock: str | None = None,
            ssl_context: SslContextArg = None,
            connect_timeout: float | None = None,
            read_timeout: float | None = None,
            write_timeout: float | None = None,
            tcp_keepalive: bool = True,
            application_name: str | bytes | None = None,
            replication: str | bytes | None = None,
            startup_params: ta.Mapping[str, str | bytes] | None = None,
            sock: socket.socket | None = None,
    ) -> None:
        super().__init__(
            user=user,
            password=password,
            database=database,
            application_name=application_name,
            replication=replication,
            startup_params=startup_params,
            ssl_context=ssl_context,
            server_hostname=host,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
        )

        self._sock = connect_socket(
            unix_sock=unix_sock,
            sock=sock,
            host=host,
            port=port,
            connect_timeout=connect_timeout,
            source_address=source_address,
            tcp_keepalive=tcp_keepalive,
        )

        self._driver = SyncSocketIoPipelineDriver(self._make_pipeline_spec(), self._sock)

        try:
            if self._wants_ssl():
                accepted = self._run(self._session.negotiate_ssl())
                if (ssl_handler := self._on_ssl_response(accepted)) is not None:
                    self._driver.pipeline.add_outermost(ssl_handler)

            self._run(self._session.startup())

        except BaseException:
            self._driver.close()
            raise

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: types.TracebackType | None,
    ) -> None:
        self.close()

    @property
    def is_closed(self) -> bool:
        return self._driver.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)

    def _run(self, op: Operation[T]) -> T:
        if self.is_closed:
            raise InterfaceError('connection is closed')

        self._driver.enqueue(OperationRequest(op))
        while True:
            try:
                out = self._driver.next()
            except OSError as e:
                raise InterfaceError('network error') from e
            if self._check_output(op, out, running=not self.is_closed):
                break
        return op.result()

    def close(self) -> None:
        if self.is_closed:
            raise InterfaceError('connection is closed')

        try:
            self._driver.enqueue(msgs.Terminate())
            self._driver.next(read=False)
        finally:
            self._driver.close()

    def execute_simple(self, statement: str) -> Context:
        return self._run(self._session.execute_simple(statement))

    def execute_unnamed(
            self,
            statement: str,
            vals: ta.Iterable[ta.Any] = (),
            oids: ta.Sequence[int] = (),
            stream: CopyStream | None = None,
    ) -> Context:
        return self._run(self._session.execute_unnamed(statement, vals, oids, stream))

    def prepare_statement(
            self,
            statement: str,
            oids: ta.Sequence[int] | None = None,
    ) -> PreparedStatementInfo:
        return self._run(self._session.prepare_statement(statement, oids))

    def execute_named(
            self,
            name: str,
            params: ta.Sequence[str | None],
            columns: Columns | None,
            input_funcs: ta.Sequence[InAdapter],
            statement: str,
    ) -> Context:
        return self._run(self._session.execute_named(name, params, columns, input_funcs, statement))

    def close_prepared_statement(self, name: str) -> None:
        self._run(self._session.close_prepared_statement(name))
