import contextlib
import enum
import typing as ta

from .. import check
from .. import lang
from ..secrets.secrets import SecretRef
from ..secrets.secrets import Secrets
from .api.adapters import Adapter
from .api.core import AsyncConn
from .api.core import AsyncDb
from .api.core import AsyncRows
from .api.core import AsyncTxn
from .api.core import Conn
from .api.core import Db
from .api.core import Rows
from .api.core import Txn
from .api.queries import Queryable
from .dbs import DbSpec
from .dbs import DbTypes
from .dbs import HostDbLoc
from .dbs import UrlDbLoc


with lang.auto_proxy_import(globals()):
    from .backends import connecting as bc
    from .backends.mysql import connecting as mc
    from .backends.postgres import connecting as pc
    from .backends.sqlite import connecting as sc


type SyncDbFactory = ta.Callable[[DbSpec, Secrets | None], Db]
type AsyncDbFactory = ta.Callable[[DbSpec, Secrets | None], ta.AsyncContextManager[AsyncDb]]


##


class DbSlot(enum.StrEnum):
    WRITER = 'writer'
    READER = 'reader'
    ANALYTICS = 'analytics'


class DbSet:
    def __init__(
            self,
            writer: DbSpec,
            *,
            reader: DbSpec | str | None = None,
            analytics: DbSpec | str | None = None,
            others: ta.Mapping[str, DbSpec | str] | None = None,
    ) -> None:
        super().__init__()

        entries: dict[str, DbSpec | str] = {DbSlot.WRITER: writer}
        if reader is not None:
            entries[DbSlot.READER] = reader
        if analytics is not None:
            entries[DbSlot.ANALYTICS] = analytics
        for name, entry in (others or {}).items():
            check.not_in(name, entries)
            entries[name] = entry
        self._entries = entries

    def spec(self, slot: DbSlot | str = DbSlot.WRITER) -> DbSpec:
        seen: set[str] = set()
        name = str(slot)
        while True:
            if name in seen:
                raise ValueError(f'Circular database alias at {name!r}')
            seen.add(name)
            entry = self._entries[name]
            if isinstance(entry, DbSpec):
                return entry
            name = entry


class DbSets:
    def __init__(self, sets: ta.Mapping[str, DbSet]) -> None:
        super().__init__()

        self._sets = dict(sets)

    def __getitem__(self, name: str) -> DbSet:
        return self._sets[name]


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


##


class DbResolver:
    def __init__(
            self,
            sets: DbSets,
            *,
            secrets: Secrets | None = None,
            sync_factories: ta.Mapping[str, SyncDbFactory] | None = None,
            async_factories: ta.Mapping[str, AsyncDbFactory] | None = None,
    ) -> None:
        super().__init__()

        self._sets = sets
        self._secrets = secrets
        self._sync_factories = dict(sync_factories or {})
        self._async_factories = dict(async_factories or {})
        self._sync_dbs: dict[DbSpec, Db] = {}
        self._async_dbs: dict[DbSpec, AsyncDb] = {}
        self._async_stack = contextlib.AsyncExitStack()
        self._entered = False
        self._closed = False

    async def __aenter__(self) -> ta.Self:
        check.state(not self._entered and not self._closed)
        await self._async_stack.__aenter__()
        self._entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._entered = False
        self._closed = True
        return await self._async_stack.__aexit__(exc_type, exc_val, exc_tb)

    def _url(self, loc: UrlDbLoc) -> str:
        if isinstance(loc.url, str):
            return loc.url
        if isinstance(loc.url, SecretRef):
            return check.not_none(self._secrets).fix(loc.url).reveal()
        raise TypeError(loc.url)

    def _network_loc(self, spec: DbSpec) -> tuple[HostDbLoc, str | None]:
        if isinstance(spec.loc, HostDbLoc):
            return spec.loc, spec.database
        if isinstance(spec.loc, UrlDbLoc):
            loc, database = bc.parse_url_db_loc(self._url(spec.loc), spec.type)
            return loc, spec.database if spec.database is not None else database
        raise TypeError(spec.loc)

    def _driver(self, spec: DbSpec) -> str:
        if spec.driver is not None:
            return spec.driver
        return {
            DbTypes.SQLITE: 'sqlite3',
            DbTypes.POSTGRES: 'og8000',
            DbTypes.MYSQL: 'omysql',
            DbTypes.SNOWFLAKE: 'snowflake',
        }[spec.type]

    def _sync_db(self, spec: DbSpec) -> Db:
        driver = self._driver(spec)
        if (factory := self._sync_factories.get(driver)) is not None:
            return factory(spec, self._secrets)

        if driver == 'sqlite3' and spec.type == DbTypes.SQLITE:
            return sc.sqlite_db(check.isinstance(spec.loc, sc.SqliteDbConfig))

        loc, database = self._network_loc(spec)
        if driver == 'og8000' and spec.type == DbTypes.POSTGRES:
            return pc.og8000_db(loc, database=database, secrets=self._secrets)
        if driver == 'omysql' and spec.type == DbTypes.MYSQL:
            return mc.omysql_db(loc, database=database, secrets=self._secrets)
        raise ValueError(f'No sync database factory for {spec.type.name}/{driver}')

    def db(self, name: str, slot: DbSlot | str = DbSlot.WRITER) -> Db:
        spec = self._sets[name].spec(slot)
        readonly = slot != DbSlot.WRITER
        cannot_write = bool(spec.caps and spec.caps.readonly)
        if cannot_write and not readonly:
            raise ValueError('Writer slot refers to a read-only endpoint')
        try:
            db = self._sync_dbs[spec]
        except KeyError:
            db = self._sync_dbs[spec] = self._sync_db(spec)
        return _DefaultReadonlyDb(db, readonly, cannot_write=cannot_write)

    async def _async_db(self, spec: DbSpec) -> AsyncDb:
        driver = self._driver(spec)
        if (factory := self._async_factories.get(driver)) is not None:
            cm = factory(spec, self._secrets)

        elif driver == 'sqlite3' and spec.type == DbTypes.SQLITE:
            cm = sc.asyncio_sqlite_db(check.isinstance(spec.loc, sc.SqliteDbConfig))

        elif driver == 'og8000' and spec.type == DbTypes.POSTGRES:
            loc, database = self._network_loc(spec)
            cm = lang.ValueAsyncContextManager(pc.asyncio_og8000_db(loc, database=database, secrets=self._secrets))

        elif driver == 'omysql' and spec.type == DbTypes.MYSQL:
            loc, database = self._network_loc(spec)
            cm = lang.ValueAsyncContextManager(mc.asyncio_omysql_db(loc, database=database, secrets=self._secrets))

        else:
            raise ValueError(f'No async database factory for {spec.type.name}/{driver}')

        return await self._async_stack.enter_async_context(cm)

    async def async_db(self, name: str, slot: DbSlot | str = DbSlot.WRITER) -> AsyncDb:
        check.state(self._entered)
        spec = self._sets[name].spec(slot)
        readonly = slot != DbSlot.WRITER
        cannot_write = bool(spec.caps and spec.caps.readonly)
        if cannot_write and not readonly:
            raise ValueError('Writer slot refers to a read-only endpoint')
        try:
            db = self._async_dbs[spec]
        except KeyError:
            db = self._async_dbs[spec] = await self._async_db(spec)
        return _DefaultReadonlyAsyncDb(db, readonly, cannot_write=cannot_write)
