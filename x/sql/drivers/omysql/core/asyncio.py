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
import asyncio
import types
import typing as ta

from omcore.io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from omcore.io.pipelines.drivers.types import IoPipelineDriverState

from ..constants import COMMAND
from ..errors import Error
from ..protocol.session import Operation
from ..protocol.session import QueryResult
from ..protocol.session import Row
from ..protocol.session import UnbufferedResult
from .base import BaseConnection
from .handlers import OperationRequest
from .handlers import make_pipeline_spec


T = ta.TypeVar('T')


##


class AsyncioConnection(BaseConnection):
    """Constructed via `connect`, as establishing the connection requires awaiting."""

    def __init__(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            **kwargs: ta.Any,
    ) -> None:
        super().__init__(**kwargs)

        self._driver = PollAsyncioStreamIoPipelineDriver(make_pipeline_spec(self._session), reader, writer)

    @classmethod
    async def connect(
            cls,
            *,
            host: str | None = None,
            port: int = 3306,
            unix_socket: str | None = None,
            **kwargs: ta.Any,
    ) -> ta.Self:
        if unix_socket is not None:
            reader, writer = await asyncio.open_unix_connection(unix_socket)
        else:
            reader, writer = await asyncio.open_connection(host or 'localhost', port)

        conn = cls(reader, writer, server_hostname=host, **kwargs)
        if unix_socket is not None:
            conn._mark_secure_transport()  # noqa: SLF001

        try:
            await conn._start()  # noqa: SLF001
        except BaseException:
            await conn._driver.close()  # noqa: SLF001
            raise
        return conn

    async def _start(self) -> None:
        await self._run(self._session.read_handshake())
        if self._wants_ssl():
            await self._run(self._session.send_ssl_request())
            self._driver.pipeline.add_outermost(self._make_ssl_handler())
            self._session.mark_secure()
        await self._run(self._session.authenticate())

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
    def open(self) -> bool:
        return self._driver.state not in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)

    async def _run(self, op: Operation[T]) -> T:
        if not self.open:
            raise Error('Already closed')
        self._driver.enqueue(OperationRequest(op))
        while True:
            try:
                out = await self._driver.next()
            except OSError as e:
                raise Error(f'Lost connection to MySQL server during query ({e})') from e
            if self._check_output(op, out, running=self.open):
                break
        return op.result()

    async def close(self) -> None:
        if not self.open:
            raise Error('Already closed')
        try:
            self._driver.enqueue(OperationRequest(self._session.quit()))
            await self._driver.next(read=False)
        except BaseException:  # noqa: BLE001,S110  # A broken transport must not prevent teardown.
            pass
        finally:
            try:
                await self._driver.close()
            except BaseException:  # noqa: BLE001,S110
                pass

    #
    # Query interface

    async def _drain_pending_results(self) -> None:
        result = self._result
        if isinstance(result, UnbufferedResult) and result.active:
            await self.finish_unbuffered()
        while (result := self._result) is not None and result.has_next:
            await self.next_result(unbuffered=isinstance(result, UnbufferedResult))
        self._result = None

    async def query(self, sql: bytes | str, *, unbuffered: bool = False) -> int:
        await self._drain_pending_results()
        if isinstance(sql, str):
            sql = sql.encode(self._encoding, 'surrogateescape')
        reader = self._local_infile_reader()
        self._result = None
        if unbuffered:
            self._result = await self._run(self._session.start_unbuffered(sql, local_infile=reader))
        else:
            self._result = await self._run(self._session.query(sql, local_infile=reader))
        return self._affected_rows()

    async def next_result(self, *, unbuffered: bool = False) -> int:
        self._result = None
        self._result = await self._run(self._session.next_result(unbuffered=unbuffered))
        return self._affected_rows()

    def _affected_rows(self) -> int:
        result = self._result
        if isinstance(result, QueryResult):
            return result.affected_rows
        return 18446744073709551615

    async def fetch_unbuffered_row(self) -> Row | None:
        result = self._result
        if not isinstance(result, UnbufferedResult) or not result.active:
            return None
        return await self._run(self._session.fetch_row(result))

    async def finish_unbuffered(self) -> None:
        result = self._result
        if isinstance(result, UnbufferedResult):
            while result.active:
                await self._run(self._session.fetch_row(result))

    async def ping(self) -> None:
        if not self.open:
            raise Error('Already closed')
        await self._run(self._session.command(COMMAND.COM_PING))

    async def select_db(self, db: str) -> None:
        await self._run(self._session.command(COMMAND.COM_INIT_DB, db.encode(self._encoding)))

    async def autocommit(self, value: bool) -> None:  # noqa: FBT001
        if bool(value) != self.get_autocommit():
            await self.query(f'SET AUTOCOMMIT = {1 if value else 0}')

    async def begin(self) -> None:
        await self.query('BEGIN')

    async def commit(self) -> None:
        await self.query('COMMIT')

    async def rollback(self) -> None:
        await self.query('ROLLBACK')
