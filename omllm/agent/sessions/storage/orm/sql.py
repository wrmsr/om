import typing as ta

from omcore import lang
from omcore import orm
from omcore import sql

from .impl import StoreOrm
from .types import Orm


##


class SqlOrm(Orm, lang.SelfAsyncContextManaged):
    """
    An orm kept in a sql db - any, as far as this is concerned: whatever is particular to a dialect comes in with the db
    and the backend's facets. Entering it creates whatever of the schema is not there yet, so a db which did not exist
    is ready by the time anything is stored in it.
    """

    def __init__(
            self,
            *,
            registry: orm.Registry,

            # FIXME: obvious pairs of something
            db: sql.AsyncDb,
            backend: sql.be.Backend,

            read_db: sql.AsyncDb | None = None,
            read_backend: sql.be.Backend | None = None,
    ) -> None:
        super().__init__()

        self._store = orm.SqlStore(
            registry,
            db,
            tabledef_renderer=backend.tabledef_renderer,
            dtype_codec=backend.dtype_codec,
        )

        if read_db is not None:
            if read_backend is None:
                read_backend = backend
            read_store: orm.SqlStore | None = orm.SqlStore(
                registry,
                read_db,
                tabledef_renderer=read_backend.tabledef_renderer,
                dtype_codec=read_backend.dtype_codec,
                manage_schema=False,
            )
        else:
            read_store = None

        self._orm = StoreOrm(
            registry=registry,
            store=self._store,
            read_store=read_store,
        )

    async def __aenter__(self) -> ta.Self:
        await super().__aenter__()

        await self._store.ensure_schema()

        return self

    def new_session(self, *, readonly: bool | None = None) -> ta.AsyncContextManager[orm.Session]:
        return self._orm.new_session(readonly=readonly)

    def ensure_session(self) -> ta.AsyncContextManager[orm.Session]:
        return self._orm.ensure_session()
