"""
Injector wiring. The `SqlOrm` is bound as an async-managed singleton, as is the db beneath it: both are entered on first
provision - which is when a db that does not exist yet is created, schema and all - and exited, the db's thread with
them, when the injector's `AsyncExitStack` unwinds.
"""
import contextlib
import typing as ta

from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import orm
from omcore import sql

from ..types import SessionStorage
from .models import orm_session_mappers
from .sql import SqlOrm
from .storage import OrmSessionStorage
from .types import Orm


SqliteDbConfig: ta.TypeAlias = sql.be.sqlite.connecting.SqliteDbConfig


##


def _provide_registry() -> orm.Registry:
    return orm.registry(*orm_session_mappers())


def bind_orm_session_storage() -> inj.Elements:
    """Wants an `Orm` bound for it."""

    return inj.as_elements(
        inj.bind(_provide_registry, singleton=True),

        inj.bind(OrmSessionStorage, singleton=True),
        inj.bind(SessionStorage, to_key=OrmSessionStorage),
    )


##


def _provide_sqlite_db_sets(config: SqliteDbConfig) -> sql.DbSets:
    writer = sql.DbSpec('sessions', sql.DbTypes.SQLITE, config)
    reader_config = dc.replace(
        SqliteDbConfig.READONLY,
        file_path=config.file_path,
        page_size=config.page_size,
        application_id=config.application_id,
    )
    reader = sql.DbSpec(
        'sessions-reader',
        sql.DbTypes.SQLITE,
        reader_config,
        caps=sql.DbCaps(readonly=True),
    )
    return sql.DbSets({'sessions': sql.DbSet(writer, reader=reader, analytics='reader')})


# FIXME: should be in core lol
def _backend_for(spec: sql.DbSpec) -> sql.be.Backend:
    if spec.type == sql.DbTypes.SQLITE:
        return sql.be.sqlite.backend.SqliteBackend()
    if spec.type == sql.DbTypes.POSTGRES:
        return sql.be.postgres.backend.PostgresBackend()
    if spec.type == sql.DbTypes.MYSQL:
        return sql.be.mysql.backend.MysqlBackend()
    raise ValueError(f'No ORM backend for {spec.type.name}')


async def _provide_db_sets_orm(
        sets: sql.DbSets,
        registry: orm.Registry,
        aes: contextlib.AsyncExitStack,
) -> SqlOrm:
    resolver = await aes.enter_async_context(sql.DbResolver(sets))
    db_set = sets['sessions']
    writer = await resolver.async_db('sessions')
    reader = await resolver.async_db('sessions', sql.DbSlot.READER)

    return await aes.enter_async_context(SqlOrm(
        registry=registry,
        db=writer,
        backend=_backend_for(db_set.spec()),
        read_db=reader,
        read_backend=_backend_for(db_set.spec(sql.DbSlot.READER)),
    ))


def bind_db_sets_orm(sets: sql.DbSets) -> inj.Elements:
    return inj.as_elements(
        inj.bind(sets),

        inj.bind(SqlOrm, singleton=True, to_async_fn=_provide_db_sets_orm),
        inj.bind(Orm, to_key=SqlOrm),
    )


def bind_asyncio_sqlite_orm(config: SqliteDbConfig) -> inj.Elements:
    return inj.as_elements(
        inj.bind(config),
        inj.bind(_provide_sqlite_db_sets, singleton=True),

        inj.bind(SqlOrm, singleton=True, to_async_fn=_provide_db_sets_orm),
        inj.bind(Orm, to_key=SqlOrm),
    )
