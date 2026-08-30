import contextlib
import typing as ta

from ...... import check
from ......resources import SimpleResource
from .....api.adapters import Adapter
from .....api.columns import Columns
from .....api.core import Conn
from .....api.core import Db
from .....api.core import Rows
from .....api.core import Txn
from .....api.queries import ManyParams
from .....api.queries import NoParams
from .....api.queries import Query
from .....api.queries import Queryable
from .....api.queries import RowParams
from .....api.rows import Row
from .....drivers.omysql.core.sync import SyncConnection
from .....drivers.omysql.cursors.formatting import mogrify
from .....drivers.omysql.protocol.session import QueryResult
from .....drivers.omysql.protocol.session import UnbufferedResult
from .base import OmysqlAdapter
from .base import build_omysql_columns
from .base import omysql_row_args


OmysqlConnector: ta.TypeAlias = ta.Callable[[], SyncConnection]


##


class OmysqlRows(Rows):
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

    def __next__(self) -> Row:
        return Row(self._columns, tuple(next(self._it)))


#


class OmysqlTxn(Txn, SimpleResource):
    def __init__(self, conn: OmysqlConn) -> None:
        super().__init__()

        self._conn = conn

    _state: ta.Literal['new', 'open', 'committed', 'aborted'] = 'new'

    def _enter(self) -> None:
        check.state(self._state == 'new')
        self._conn._conn.begin()  # noqa: SLF001
        self._state = 'open'

    def _commit_internal(self) -> None:
        check.state(self._state == 'open')
        self._conn._conn.commit()  # noqa: SLF001
        self._state = 'committed'

    def _rollback_internal(self) -> None:
        check.state(self._state == 'open')
        self._conn._conn.rollback()  # noqa: SLF001
        self._state = 'aborted'

    def _close(self, reason: BaseException | None) -> None:
        if self._state == 'open':
            if reason is not None:
                self._rollback_internal()
            else:
                self._commit_internal()

        super()._close(reason)

    @property
    def adapter(self) -> Adapter:
        return self._conn.adapter

    def query(self, query: Queryable) -> ta.ContextManager[Rows]:
        self._check_entered()
        check.state(self._state == 'open')
        return self._conn.query(query)

    def commit(self) -> None:
        self._check_entered()
        self._commit_internal()

    def rollback(self) -> None:
        self._check_entered()
        self._rollback_internal()


#


class OmysqlConn(Conn):
    def __init__(
            self,
            conn: SyncConnection,
            *,
            adapter: Adapter | None = None,
    ) -> None:
        super().__init__()

        self._conn = conn
        if adapter is None:
            adapter = OmysqlAdapter()
        self._adapter = adapter

        if not self._conn.get_autocommit():
            self._conn.autocommit(True)
        check.state(self._conn.get_autocommit())

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

    def query(self, query: Queryable) -> ta.ContextManager[Rows]:
        @contextlib.contextmanager
        def inner():
            q = check.isinstance(query, Query)
            p = q.params

            if isinstance(p, ManyParams):
                for sql in self._mogrify(q):
                    self._conn.query(sql)
                yield OmysqlRows(Columns.empty(), ())

            else:
                [sql] = self._mogrify(q)
                self._conn.query(sql)
                result: QueryResult | UnbufferedResult = check.isinstance(
                    self._conn.result,
                    (QueryResult, UnbufferedResult),
                )

                yield OmysqlRows(build_omysql_columns(result.fields), result.rows or ())

        return inner()

    def begin(self) -> ta.ContextManager[Txn]:
        return OmysqlTxn(self)


#


class OmysqlDb(Db):
    def __init__(
            self,
            connector: OmysqlConnector,
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

    def _connect(self, es: contextlib.ExitStack) -> OmysqlConn:
        return OmysqlConn(
            es.enter_context(self._connector()),
            adapter=self._adapter,
        )

    def connect(self) -> ta.ContextManager[Conn]:
        @contextlib.contextmanager
        def inner():
            with contextlib.ExitStack() as es:
                yield self._connect(es)

        return inner()

    def query(self, query: Queryable) -> ta.ContextManager[Rows]:
        @contextlib.contextmanager
        def inner():
            with self.connect() as conn:
                with conn.query(query) as rows:
                    yield rows

        return inner()
