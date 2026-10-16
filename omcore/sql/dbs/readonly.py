"""
TODO:
 - move to api
 - also wtf
"""
import contextlib
import typing as ta

from ..api.adapters import Adapter
from ..api.core import AsyncConn
from ..api.core import AsyncDb
from ..api.core import AsyncRows
from ..api.core import AsyncTxn
from ..api.core import Conn
from ..api.core import Db
from ..api.core import Rows
from ..api.core import Txn
from ..api.queries import Queryable


##


class _DefaultReadonlyConn(Conn):
    def __init__(self, conn: Conn, readonly: bool, *, cannot_write: bool = False) -> None:
        super().__init__()

        self._conn = conn
        self._readonly = readonly
        self._cannot_write = cannot_write
        self._active_txns = 0

    @property
    def adapter(self) -> Adapter:
        return self._conn.adapter

    @contextlib.contextmanager
    def query(self, query: Queryable) -> ta.Iterator[Rows]:
        if self._readonly and not self._active_txns:
            with self._conn.begin(readonly=True) as txn:
                self._active_txns += 1

                try:
                    with txn.query(query) as rows:
                        yield rows

                finally:
                    self._active_txns -= 1

        else:
            with self._conn.query(query) as rows:
                yield rows

    @contextlib.contextmanager
    def begin(self, *, readonly: bool | None = None) -> ta.Iterator[Txn]:
        resolved = self._readonly if readonly is None else readonly

        if self._cannot_write and not resolved:
            raise ValueError('Database endpoint is read-only')

        with self._conn.begin(readonly=resolved) as txn:
            self._active_txns += 1

            try:
                yield txn

            finally:
                self._active_txns -= 1


class _DefaultReadonlyDb(Db):
    def __init__(self, db: Db, readonly: bool, *, cannot_write: bool = False) -> None:
        super().__init__()

        self._db = db
        self._readonly = readonly
        self._cannot_write = cannot_write

    @property
    def adapter(self) -> Adapter:
        return self._db.adapter

    @contextlib.contextmanager
    def connect(self) -> ta.Iterator[Conn]:
        with self._db.connect() as conn:
            yield _DefaultReadonlyConn(conn, self._readonly, cannot_write=self._cannot_write)

    @contextlib.contextmanager
    def query(self, query: Queryable) -> ta.Iterator[Rows]:
        if not self._readonly:
            with self._db.query(query) as rows:
                yield rows

            return

        with self.connect() as conn:
            with conn.begin() as txn:
                with txn.query(query) as rows:
                    yield rows


##


class _DefaultReadonlyAsyncConn(AsyncConn):
    def __init__(self, conn: AsyncConn, readonly: bool, *, cannot_write: bool = False) -> None:
        super().__init__()

        self._conn = conn
        self._readonly = readonly
        self._cannot_write = cannot_write
        self._active_txns = 0

    @property
    def adapter(self) -> Adapter:
        return self._conn.adapter

    @contextlib.asynccontextmanager
    async def query(self, query: Queryable) -> ta.AsyncIterator[AsyncRows]:
        if self._readonly and not self._active_txns:
            async with self._conn.begin(readonly=True) as txn:
                self._active_txns += 1

                try:
                    async with txn.query(query) as rows:
                        yield rows

                finally:
                    self._active_txns -= 1

        else:
            async with self._conn.query(query) as rows:
                yield rows

    @contextlib.asynccontextmanager
    async def begin(self, *, readonly: bool | None = None) -> ta.AsyncIterator[AsyncTxn]:
        resolved = self._readonly if readonly is None else readonly

        if self._cannot_write and not resolved:
            raise ValueError('Database endpoint is read-only')

        async with self._conn.begin(readonly=resolved) as txn:
            self._active_txns += 1

            try:
                yield txn

            finally:
                self._active_txns -= 1


class _DefaultReadonlyAsyncDb(AsyncDb):
    def __init__(self, db: AsyncDb, readonly: bool, *, cannot_write: bool = False) -> None:
        super().__init__()

        self._db = db
        self._readonly = readonly
        self._cannot_write = cannot_write

    @property
    def adapter(self) -> Adapter:
        return self._db.adapter

    @contextlib.asynccontextmanager
    async def connect(self) -> ta.AsyncIterator[AsyncConn]:
        async with self._db.connect() as conn:
            yield _DefaultReadonlyAsyncConn(conn, self._readonly, cannot_write=self._cannot_write)

    @contextlib.asynccontextmanager
    async def query(self, query: Queryable) -> ta.AsyncIterator[AsyncRows]:
        if not self._readonly:
            async with self._db.query(query) as rows:
                yield rows

            return

        async with self.connect() as conn:
            async with conn.begin() as txn:
                async with txn.query(query) as rows:
                    yield rows
