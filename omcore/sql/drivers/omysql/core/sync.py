# Copyright (c) 2010, 2013 PyMySQL contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import socket
import types
import typing as ta
import warnings

from ..... import check
from .....io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from .....io.pipelines.drivers.types import IoPipelineDriverState
from ..constants import COMMAND
from ..errors import Error
from ..protocol.session import Operation
from ..protocol.session import QueryResult
from ..protocol.session import Row
from ..protocol.session import UnbufferedResult
from .base import BaseConnection
from .handlers import OperationRequest
from .sockets import connect_socket


T = ta.TypeVar('T')


##


class SyncConnection(BaseConnection):
    def __init__(
            self,
            *,
            host: str | None = None,
            port: int = 3306,
            unix_socket: str | None = None,
            connect_timeout: float | None = 10,
            bind_address: str | None = None,
            sock: socket.socket | None = None,
            defer_connect: bool = False,
            **kwargs: ta.Any,
    ) -> None:
        super().__init__(server_hostname=host, connect_timeout=connect_timeout, **kwargs)

        self._host = host
        self._port = port
        self._unix_socket = unix_socket
        self._bind_address = bind_address
        self._driver: SyncSocketIoPipelineDriver | None = None

        if not defer_connect:
            self.connect(sock)

    def connect(self, sock: socket.socket | None = None) -> None:
        """Establishes (or re-establishes) the connection, building a fresh session and pipeline driver."""

        self._reset_session()

        if sock is not None:
            self._sock = sock
        else:
            self._sock = connect_socket(
                unix_socket=self._unix_socket,
                host=self._host or 'localhost',
                port=self._port,
                connect_timeout=self._connect_timeout,
                bind_address=self._bind_address,
            )
        if self._unix_socket is not None or (sock is not None and sock.family == socket.AF_UNIX):
            self._mark_secure_transport()

        self._driver = SyncSocketIoPipelineDriver(self._make_pipeline_spec(), self._sock)

        try:
            self._run(self._session.read_handshake())
            if self._wants_ssl():
                self._run(self._session.send_ssl_request())
                self._driver.pipeline.add_outermost(self._make_ssl_handler())
                self._session.mark_secure()
            self._run(self._session.authenticate())
            self._after_connect()
        except BaseException:
            if self._driver is not None:
                self._driver.close()
            self._driver = None
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
    def open(self) -> bool:
        return (
            self._driver is not None and
            self._driver.state not in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)
        )

    def _run(self, op: Operation[T]) -> T:
        if not self.open:
            raise Error('Already closed')
        driver = check.not_none(self._driver)
        driver.enqueue(OperationRequest(op))
        while True:
            try:
                out = driver.next()
            except OSError as e:
                raise Error(f'Lost connection to MySQL server during query ({e})') from e
            if self._check_output(op, out, running=self.open):
                break
        return op.result()

    def close(self) -> None:
        if not self.open:
            raise Error('Already closed')
        driver = check.not_none(self._driver)
        try:
            # A failed session means the pipeline is already dead or dying (the transport hit EOF, or an error tore it
            # down), and would reject the courtesy COM_QUIT.
            if self._session.fatal_error is None:
                driver.enqueue(OperationRequest(self._session.quit()))
                driver.next(read=False)
        except BaseException:  # noqa: BLE001,S110  # A broken transport must not prevent teardown.
            pass
        finally:
            try:
                driver.close()
            except BaseException:  # noqa: BLE001,S110
                pass

    #
    # Query interface used by cursors

    def _drain_pending_results(self) -> None:
        result = self._result
        if isinstance(result, UnbufferedResult) and result.active:
            # Warned, as pymysql does, because the discarded rows are silently read and thrown away, which is rarely
            # what the caller meant to do. Explicitly finishing a result (as SSCursor.close does) does not warn.
            warnings.warn('Previous unbuffered result was left incomplete', stacklevel=2)
            self.finish_unbuffered()
        while (result := self._result) is not None and result.has_next:
            self.next_result(unbuffered=isinstance(result, UnbufferedResult))
        self._result = None

    def query(self, sql: bytes | str, *, unbuffered: bool = False) -> int:
        self._drain_pending_results()
        if isinstance(sql, str):
            sql = sql.encode(self._encoding, 'surrogateescape')
        reader = self._local_infile_reader()
        self._result = None
        if unbuffered:
            self._result = self._run(self._session.start_unbuffered(sql, local_infile=reader))
        else:
            self._result = self._run(self._session.query(sql, local_infile=reader))
        return self._affected_rows()

    def next_result(self, *, unbuffered: bool = False) -> int:
        self._result = None
        self._result = self._run(self._session.next_result(unbuffered=unbuffered))
        return self._affected_rows()

    def _affected_rows(self) -> int:
        result = self._result
        if isinstance(result, QueryResult):
            return result.affected_rows
        return 18446744073709551615  # unbuffered: unknown, per MySQLdb convention

    def fetch_unbuffered_row(self) -> Row | None:
        result = self._result
        if not isinstance(result, UnbufferedResult) or not result.active:
            return None
        return self._run(self._session.fetch_row(result))

    def finish_unbuffered(self) -> None:
        result = self._result
        if isinstance(result, UnbufferedResult):
            while result.active:
                self._run(self._session.fetch_row(result))

    def command(self, command: int, payload: bytes = b'') -> None:
        self._run(self._session.command(command, payload))

    def ping(self, reconnect: bool = False) -> None:  # noqa: FBT001,FBT002
        if not self.open:
            if reconnect:
                self.connect()
                return
            raise Error('Already closed')
        try:
            self._run(self._session.command(COMMAND.COM_PING))
        except Exception:
            if reconnect:
                self.connect()
            else:
                raise

    def select_db(self, db: str) -> None:
        self._run(self._session.command(COMMAND.COM_INIT_DB, db.encode(self._encoding)))

    def autocommit(self, value: bool) -> None:  # noqa: FBT001
        if bool(value) != self.get_autocommit():
            self.query(f'SET AUTOCOMMIT = {1 if value else 0}')

    def begin(self) -> None:
        self.query('BEGIN')

    def commit(self) -> None:
        self.query('COMMIT')

    def rollback(self) -> None:
        self.query('ROLLBACK')
