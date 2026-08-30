import contextlib
import typing as ta

from ...... import check
from ......resources import AsyncSimpleResource
from .....api import querierfuncs as qf
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
from .....drivers.og8000.core.asyncio import AsyncioCoreConnection
from .base import Og8000Adapter
from .base import build_og8000_columns
from .base import positional_og8000_params


AsyncioOg8000Connector: ta.TypeAlias = ta.Callable[[], ta.Awaitable[AsyncioCoreConnection]]


##


class AsyncioOg8000Rows(AsyncRows):
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


class AsyncioOg8000Txn(AsyncTxn, AsyncSimpleResource):
    def __init__(self, conn: AsyncioOg8000Conn) -> None:
        super().__init__()

        self._conn = conn

    _state: ta.Literal['new', 'open', 'committed', 'aborted'] = 'new'

    async def _enter(self) -> None:
        check.state(self._state == 'new')
        await qf.async_exec(self._conn, 'begin')
        self._state = 'open'

    async def _commit_internal(self) -> None:
        check.state(self._state == 'open')
        await qf.async_exec(self._conn, 'commit')
        self._state = 'committed'

    async def _rollback_internal(self) -> None:
        check.state(self._state == 'open')
        await qf.async_exec(self._conn, 'rollback')
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


class AsyncioOg8000Conn(AsyncConn):
    def __init__(
            self,
            conn: AsyncioCoreConnection,
            *,
            adapter: Adapter | None = None,
    ) -> None:
        super().__init__()

        self._conn = conn
        if adapter is None:
            adapter = Og8000Adapter()
        self._adapter = adapter

    @property
    def adapter(self) -> Adapter:
        return self._adapter

    def query(self, query: Queryable) -> ta.AsyncContextManager[AsyncRows]:
        @contextlib.asynccontextmanager
        async def inner():
            q = check.isinstance(query, Query)
            p = q.params

            if isinstance(p, ManyParams):
                for row in p.rows:
                    await self._conn.execute_unnamed(q.text, positional_og8000_params(row))
                yield AsyncioOg8000Rows(Columns.empty(), ())

            elif isinstance(p, RowParams):
                context = await self._conn.execute_unnamed(q.text, positional_og8000_params(p.values))
                yield AsyncioOg8000Rows(build_og8000_columns(context.columns), context.rows or ())

            elif isinstance(p, NoParams):
                context = await self._conn.execute_simple(q.text)
                yield AsyncioOg8000Rows(build_og8000_columns(context.columns), context.rows or ())

            else:
                raise TypeError(p)

        return inner()

    def begin(self) -> ta.AsyncContextManager[AsyncTxn]:
        return AsyncioOg8000Txn(self)


#


class AsyncioOg8000Db(AsyncDb):
    def __init__(
            self,
            connector: AsyncioOg8000Connector,
            *,
            adapter: Adapter | None = None,
    ) -> None:
        super().__init__()

        self._connector = connector
        if adapter is None:
            adapter = Og8000Adapter()
        self._adapter = adapter

    @property
    def adapter(self) -> Adapter:
        return self._adapter

    async def _connect(self, es: contextlib.AsyncExitStack) -> AsyncioOg8000Conn:
        return AsyncioOg8000Conn(
            await es.enter_async_context(await self._connector()),
            adapter=self._adapter,
        )

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
