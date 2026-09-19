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
    and the tabledef renderer. Entering it creates whatever of the schema is not there yet, so a db which did not exist
    is ready by the time anything is stored in it.
    """

    def __init__(
            self,
            *,
            registry: orm.Registry,
            db: sql.AsyncDb,
            tabledef_renderer: sql.td.Renderer,
    ) -> None:
        super().__init__()

        self._store = orm.SqlStore(
            registry,
            db,
            tabledef_renderer=tabledef_renderer,
        )

        self._orm = StoreOrm(
            registry=registry,
            store=self._store,
        )

    async def __aenter__(self) -> ta.Self:
        await super().__aenter__()

        await self._store.ensure_schema()

        return self

    def new_session(self) -> ta.AsyncContextManager[orm.Session]:
        return self._orm.new_session()

    def ensure_session(self) -> ta.AsyncContextManager[orm.Session]:
        return self._orm.ensure_session()
