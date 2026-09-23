"""
Injector wiring. The `SqlOrm` is bound as an async-managed singleton, as is the db beneath it: both are entered on first
provision - which is when a db that does not exist yet is created, schema and all - and exited, the db's thread with
them, when the injector's `AsyncExitStack` unwinds.
"""
import contextlib
import typing as ta

from omcore import inject as inj
from omcore import orm
from omcore import sql

from ..types import SessionStorage
from .models import orm_mappers
from .sql import SqlOrm
from .storage import OrmSessionStorage
from .types import Orm


SqliteDbConfig: ta.TypeAlias = sql.be.sqlite.connecting.SqliteDbConfig


##


def _provide_registry() -> orm.Registry:
    return orm.registry(*orm_mappers())


def bind_orm_session_storage() -> inj.Elements:
    """Wants an `Orm` bound for it."""

    return inj.as_elements(
        inj.bind(_provide_registry, singleton=True),

        inj.bind(OrmSessionStorage, singleton=True),
        inj.bind(SessionStorage, to_key=OrmSessionStorage),
    )


##


async def _provide_asyncio_sqlite_orm(
        config: SqliteDbConfig,
        registry: orm.Registry,
        aes: contextlib.AsyncExitStack,
) -> SqlOrm:
    db = await aes.enter_async_context(sql.be.sqlite.connecting.asyncio_sqlite_db(config))

    return await aes.enter_async_context(SqlOrm(
        registry=registry,
        db=db,
        backend=sql.be.sqlite.backend.SqliteBackend(),
    ))


def bind_asyncio_sqlite_orm(config: SqliteDbConfig) -> inj.Elements:
    return inj.as_elements(
        inj.bind(config),

        inj.bind(SqlOrm, singleton=True, to_async_fn=_provide_asyncio_sqlite_orm),
        inj.bind(Orm, to_key=SqlOrm),
    )
