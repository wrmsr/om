"""
TODO:
 - re-add _DefaultReadonlyDb?
"""
import threading
import typing as ta

from ... import check
from ... import lang
from ...secrets.secrets import Secrets
from ..api.core import AsyncDb
from ..api.core import Db
from ._readonly import _DefaultReadonlyAsyncDb
from ._readonly import _DefaultReadonlyDb
from .factories import AsyncDbFactory
from .factories import DbFactory
from .factories import DbFactoryContext
from .factories import _DefaultAsyncDbFactory
from .factories import _DefaultDbFactory
from .sets import DbSetKey
from .sets import DbSets
from .sets import DbSlot
from .sets import is_readonly_db_slot
from .specs import DbSpec


DbT = ta.TypeVar('DbT')
DbFactoryT = ta.TypeVar('DbFactoryT')


##


class AnyDbs(
    lang.BaseExitStacked,
    lang.Abstract,
    ta.Generic[DbT, DbFactoryT],
):
    def __init__(
            self,
            sets: DbSets,
            *,
            factory: DbFactoryT,
            secrets: Secrets | None = None,
            default_key: DbSetKey | None = DbSlot.WRITER,
    ) -> None:
        super().__init__()

        self._sets = sets
        self._factory = factory
        self._secrets = secrets
        self._default_key = default_key

        self._dbs: dict[DbSpec, DbT] = {}

        # NOTE: lock does *not* protect from thread-unsafe context management - e.g. won't block `__exit__`
        self._lock = threading.RLock()

    def _factory_context(self, spec: DbSpec) -> DbFactoryContext:
        return DbFactoryContext(
            spec,
            secrets=self._secrets,
        )


##


class Dbs(
    lang.ExitStacked,
    AnyDbs[Db, DbFactory],
):
    def __init__(
            self,
            sets: DbSets,
            *,
            factory: DbFactory | None = None,
            default_key: DbSetKey | None = DbSlot.WRITER,
            secrets: Secrets | None = None,
    ) -> None:
        super().__init__(
            sets,
            factory=factory or _DefaultDbFactory(),
            default_key=default_key,
            secrets=secrets,
        )

    def db(
            self,
            name: str,
            key: DbSetKey | None = None,
    ) -> Db:
        if key is None:
            key = self._default_key
        key = check.non_empty_str(key)

        spec = self._sets[name][key]

        self._check_exit_stacked_state('entered')
        with self._lock:
            self._check_exit_stacked_state('entered')

            try:
                db: Db = self._dbs[spec]

            except KeyError:
                df_ctx = self._factory_context(spec)
                db_cm = check.not_none(self._factory(df_ctx))
                db = self._enter_context(db_cm)
                self._dbs[spec] = db

            db = _DefaultReadonlyDb(
                db,
                slot_readonly=is_readonly_db_slot(key),
                spec_readonly=bool(spec.readonly),
            )

            return db


##


class AsyncDbs(
    lang.AsyncExitStacked,
    AnyDbs[AsyncDb, AsyncDbFactory],
):
    def __init__(
            self,
            sets: DbSets,
            *,
            factory: AsyncDbFactory | None = None,
            default_key: DbSetKey | None = DbSlot.WRITER,
            secrets: Secrets | None = None,
    ) -> None:
        super().__init__(
            sets,
            factory=factory or _DefaultAsyncDbFactory(),
            default_key=default_key,
            secrets=secrets,
        )

    async def db(
            self,
            name: str,
            key: DbSetKey | None = None,
    ) -> AsyncDb:
        if key is None:
            key = self._default_key
        key = check.non_empty_str(key)

        spec = self._sets[name][key]

        self._check_exit_stacked_state('entered')
        with self._lock:
            self._check_exit_stacked_state('entered')

            try:
                db: AsyncDb = self._dbs[spec]

            except KeyError:
                df_ctx = self._factory_context(spec)
                db_cm = check.not_none(self._factory(df_ctx))
                db = await self._enter_async_context(db_cm)
                self._dbs[spec] = db

            db = _DefaultReadonlyAsyncDb(
                db,
                slot_readonly=is_readonly_db_slot(key),
                spec_readonly=bool(spec.readonly),
            )

            return db
