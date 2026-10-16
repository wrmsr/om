"""
TODO:
 - move to api
 - also wtf
 - god the contextlib.[async]contextmanager overhead
 - rename spec_readonly ffs
 - common base classes
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
    def __init__(
            self,
            conn: Conn,
            *,
            slot_readonly: bool,
            spec_readonly: bool = False,
    ) -> None:
        super().__init__()

        self._conn = conn
        self._slot_readonly = slot_readonly
        self._spec_readonly = spec_readonly
        self._active_txns = 0

    @property
    def adapter(self) -> Adapter:
        return self._conn.adapter

    @contextlib.contextmanager
    def query(self, query: Queryable) -> ta.Iterator[Rows]:
        if self._slot_readonly and not self._active_txns:
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
        resolved = self._slot_readonly if readonly is None else readonly

        if self._spec_readonly and not resolved:
            # FIXME: db api error
            raise ValueError('Database is readonly')

        with self._conn.begin(readonly=resolved) as txn:
            self._active_txns += 1

            try:
                yield txn

            finally:
                self._active_txns -= 1


class _DefaultReadonlyDb(Db):
    def __init__(
            self,
            db: Db,
            *,
            slot_readonly: bool,
            spec_readonly: bool = False,
    ) -> None:
        super().__init__()

        self._db = db
        self._slot_readonly = slot_readonly
        self._spec_readonly = spec_readonly

    @property
    def adapter(self) -> Adapter:
        return self._db.adapter

    @contextlib.contextmanager
    def connect(self) -> ta.Iterator[Conn]:
        with self._db.connect() as conn:
            yield _DefaultReadonlyConn(
                conn,
                slot_readonly=self._slot_readonly,
                spec_readonly=self._spec_readonly,
            )

    @contextlib.contextmanager
    def query(self, query: Queryable) -> ta.Iterator[Rows]:
        if not self._slot_readonly:
            with self._db.query(query) as rows:
                yield rows

            return

        with self.connect() as conn:
            with conn.begin() as txn:
                with txn.query(query) as rows:
                    yield rows


##


class _DefaultReadonlyAsyncConn(AsyncConn):
    def __init__(
            self,
            conn: AsyncConn,
            *,
            slot_readonly: bool,
            spec_readonly: bool = False,
    ) -> None:
        super().__init__()

        self._conn = conn
        self._slot_readonly = slot_readonly
        self._spec_readonly = spec_readonly
        self._active_txns = 0

    @property
    def adapter(self) -> Adapter:
        return self._conn.adapter

    @contextlib.asynccontextmanager
    async def query(self, query: Queryable) -> ta.AsyncIterator[AsyncRows]:
        if self._slot_readonly and not self._active_txns:
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
        resolved = self._slot_readonly if readonly is None else readonly

        if self._spec_readonly and not resolved:
            # FIXME: db api error
            raise ValueError('Database is readonly')

        async with self._conn.begin(readonly=resolved) as txn:
            self._active_txns += 1

            try:
                yield txn

            finally:
                self._active_txns -= 1


class _DefaultReadonlyAsyncDb(AsyncDb):
    def __init__(
            self,
            db: AsyncDb,
            *,
            slot_readonly: bool,
            spec_readonly: bool = False,
    ) -> None:
        super().__init__()

        self._db = db
        self._slot_readonly = slot_readonly
        self._spec_readonly = spec_readonly

    @property
    def adapter(self) -> Adapter:
        return self._db.adapter

    @contextlib.asynccontextmanager
    async def connect(self) -> ta.AsyncIterator[AsyncConn]:
        async with self._db.connect() as conn:
            yield _DefaultReadonlyAsyncConn(
                conn,
                slot_readonly=self._slot_readonly,
                spec_readonly=self._spec_readonly,
            )

    @contextlib.asynccontextmanager
    async def query(self, query: Queryable) -> ta.AsyncIterator[AsyncRows]:
        if not self._slot_readonly:
            async with self._db.query(query) as rows:
                yield rows

            return

        async with self.connect() as conn:
            async with conn.begin() as txn:
                async with txn.query(query) as rows:
                    yield rows
