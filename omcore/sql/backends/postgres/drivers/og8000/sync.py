import contextlib
import typing as ta

from ...... import check
from ......resources import SimpleResource
from .....api import querierfuncs as qf
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
from .....drivers.og8000.core.sync import SyncCoreConnection
from .base import Og8000Adapter
from .base import build_og8000_columns
from .base import positional_og8000_params


Og8000Connector: ta.TypeAlias = ta.Callable[[], SyncCoreConnection]


##


class Og8000Rows(Rows):
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


class Og8000Txn(Txn, SimpleResource):
    def __init__(self, conn: Og8000Conn) -> None:
        super().__init__()

        self._conn = conn

    _state: ta.Literal['new', 'open', 'committed', 'aborted'] = 'new'

    def _enter(self) -> None:
        check.state(self._state == 'new')
        qf.exec(self._conn, 'begin')
        self._state = 'open'

    def _commit_internal(self) -> None:
        check.state(self._state == 'open')
        qf.exec(self._conn, 'commit')
        self._state = 'committed'

    def _rollback_internal(self) -> None:
        check.state(self._state == 'open')
        qf.exec(self._conn, 'rollback')
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


class Og8000Conn(Conn):
    def __init__(
            self,
            conn: SyncCoreConnection,
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

    def query(self, query: Queryable) -> ta.ContextManager[Rows]:
        @contextlib.contextmanager
        def inner():
            q = check.isinstance(query, Query)
            p = q.params

            if isinstance(p, ManyParams):
                for row in p.rows:
                    self._conn.execute_unnamed(q.text, positional_og8000_params(row))
                yield Og8000Rows(Columns.empty(), ())

            elif isinstance(p, RowParams):
                context = self._conn.execute_unnamed(q.text, positional_og8000_params(p.values))
                yield Og8000Rows(build_og8000_columns(context.columns), context.rows or ())

            elif isinstance(p, NoParams):
                context = self._conn.execute_simple(q.text)
                yield Og8000Rows(build_og8000_columns(context.columns), context.rows or ())

            else:
                raise TypeError(p)

        return inner()

    def begin(self) -> ta.ContextManager[Txn]:
        return Og8000Txn(self)


#


class Og8000Db(Db):
    def __init__(
            self,
            connector: Og8000Connector,
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

    def _connect(self, es: contextlib.ExitStack) -> Og8000Conn:
        return Og8000Conn(
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
