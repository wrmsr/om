import contextlib
import typing as ta

from ...... import check
from ......resources import AsyncSimpleResource
from .....api.adapters import Adapter
from .....api.columns import Columns
from .....api.core import AsyncConn
from .....api.core import AsyncDb
from .....api.core import AsyncRows
from .....api.core import AsyncTxn
from .....api.queries import ManyParams
from .....api.queries import NoParams
from .....api.queries import Query
from .....api.queries import Queryable
from .....api.queries import RowParams
from .....api.rows import Row
from .....drivers.omysql.core.asyncio import AsyncioConnection
from .....drivers.omysql.cursors.formatting import mogrify
from .....drivers.omysql.protocol.session import QueryResult
from .....drivers.omysql.protocol.session import UnbufferedResult
from .base import OmysqlAdapter
from .base import build_omysql_columns
from .base import omysql_row_args


AsyncioOmysqlConnector: ta.TypeAlias = ta.Callable[[], ta.Awaitable[AsyncioConnection]]


##


class AsyncioOmysqlRows(AsyncRows):
    def __init__(
            self,
            columns: Columns,
            rows: ta.Iterable[ta.Sequence[ta.Any]],
    ) -> None:
        super().__init__()

        self._columns = columns
        self._it = iter(rows)

    @property
    def columns(self) -> Columns:
        return self._columns

    async def __anext__(self) -> Row:
        try:
            values = next(self._it)
        except StopIteration:
            raise StopAsyncIteration from None
        return Row(self._columns, tuple(values))


#


class AsyncioOmysqlTxn(AsyncTxn, AsyncSimpleResource):
    def __init__(self, conn: AsyncioOmysqlConn) -> None:
        super().__init__()

        self._conn = conn

    _state: ta.Literal['new', 'open', 'committed', 'aborted'] = 'new'

    async def _enter(self) -> None:
        check.state(self._state == 'new')
        await self._conn._conn.begin()  # noqa: SLF001
        self._state = 'open'

    async def _commit_internal(self) -> None:
        check.state(self._state == 'open')
        await self._conn._conn.commit()  # noqa: SLF001
        self._state = 'committed'

    async def _rollback_internal(self) -> None:
        check.state(self._state == 'open')
        await self._conn._conn.rollback()  # noqa: SLF001
        self._state = 'aborted'

    async def _close(self, reason: BaseException | None) -> None:
        if self._state == 'open':
            if reason is not None:
                await self._rollback_internal()
            else:
                await self._commit_internal()

        await super()._close(reason)

    @property
    def adapter(self) -> Adapter:
        return self._conn.adapter

    def query(self, query: Queryable) -> ta.AsyncContextManager[AsyncRows]:
        self._check_entered()
        check.state(self._state == 'open')
        return self._conn.query(query)

    async def commit(self) -> None:
        self._check_entered()
        await self._commit_internal()

    async def rollback(self) -> None:
        self._check_entered()
        await self._rollback_internal()


#


class AsyncioOmysqlConn(AsyncConn):
    def __init__(
            self,
            conn: AsyncioConnection,
            *,
            adapter: Adapter | None = None,
    ) -> None:
        super().__init__()

        # Autocommit must already be on - `AsyncioOmysqlDb._connect` ensures it, but enabling it takes an await, which
        # a constructor can't do.
        check.state(conn.get_autocommit())

        self._conn = conn
        if adapter is None:
            adapter = OmysqlAdapter()
        self._adapter = adapter

    @property
    def adapter(self) -> Adapter:
        return self._adapter

    def _mogrify(self, q: Query) -> ta.Sequence[str]:
        p = q.params

        if isinstance(p, NoParams):
            return [q.text]
        elif isinstance(p, RowParams):
            return [mogrify(q.text, omysql_row_args(p.values), self._conn)]
        elif isinstance(p, ManyParams):
            return [mogrify(q.text, omysql_row_args(row), self._conn) for row in p.rows]
        else:
            raise TypeError(p)

    def query(self, query: Queryable) -> ta.AsyncContextManager[AsyncRows]:
        @contextlib.asynccontextmanager
        async def inner():
            q = check.isinstance(query, Query)
            p = q.params

            if isinstance(p, ManyParams):
                for sql in self._mogrify(q):
                    await self._conn.query(sql)
                yield AsyncioOmysqlRows(Columns.empty(), ())

            else:
                [sql] = self._mogrify(q)
                await self._conn.query(sql)
                result: QueryResult | UnbufferedResult = check.isinstance(
                    self._conn.result,
                    (QueryResult, UnbufferedResult),
                )

                yield AsyncioOmysqlRows(build_omysql_columns(result.fields), result.rows or ())

        return inner()

    def begin(self) -> ta.AsyncContextManager[AsyncTxn]:
        return AsyncioOmysqlTxn(self)


#


class AsyncioOmysqlDb(AsyncDb):
    def __init__(
            self,
            connector: AsyncioOmysqlConnector,
            *,
            adapter: Adapter | None = None,
    ) -> None:
        super().__init__()

        self._connector = connector
        if adapter is None:
            adapter = OmysqlAdapter()
        self._adapter = adapter

    @property
    def adapter(self) -> Adapter:
        return self._adapter

    async def _connect(self, es: contextlib.AsyncExitStack) -> AsyncioOmysqlConn:
        conn = await es.enter_async_context(await self._connector())
        if not conn.get_autocommit():
            await conn.autocommit(True)
        return AsyncioOmysqlConn(conn, adapter=self._adapter)

    def connect(self) -> ta.AsyncContextManager[AsyncConn]:
        @contextlib.asynccontextmanager
        async def inner():
            async with contextlib.AsyncExitStack() as es:
                yield await self._connect(es)

        return inner()

    def query(self, query: Queryable) -> ta.AsyncContextManager[AsyncRows]:
        @contextlib.asynccontextmanager
        async def inner():
            async with self.connect() as conn:
                async with conn.query(query) as rows:
                    yield rows

        return inner()
