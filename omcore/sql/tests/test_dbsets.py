import os.path
import sqlite3
import tempfile
import uuid

import pytest

from ... import dataclasses as dc
from ...secrets.secrets import MappingSecrets
from ...secrets.secrets import SecretRef
from .. import api
from ..backends.sqlite.connecting import SqliteDbConfig
from ..backends.sqlite.connecting import sqlite_db
from ..dbs import DbCaps
from ..dbs import DbSpec
from ..dbs import DbTypes
from ..dbs import UrlDbLoc
from ..dbsets import DbResolver
from ..dbsets import DbSet
from ..dbsets import DbSets
from ..drivers.omysql.errors import DatabaseError
from .harness import HarnessDbs


##


def _sqlite_sets(path: str) -> DbSets:
    writer = DbSpec('local', DbTypes.SQLITE, SqliteDbConfig(file_path=path))
    reader = DbSpec(
        'local-read',
        DbTypes.SQLITE,
        dc.replace(SqliteDbConfig.READONLY, file_path=path),
        caps=DbCaps(readonly=True),
    )
    return DbSets({'sessions': DbSet(writer, reader=reader, analytics='reader')})


def test_sqlite_set_and_readonly_transactions():
    path = os.path.join(tempfile.mkdtemp(), 'sessions.db')
    resolver = DbResolver(_sqlite_sets(path))
    writer = resolver.db('sessions')
    reader = resolver.db('sessions', 'reader')

    api.exec(writer, 'create table entries (value text)')
    api.exec(writer, "insert into entries values ('one')")
    assert api.query_scalar(reader, 'select value from entries') == 'one'
    assert api.query_scalar(resolver.db('sessions', 'analytics'), 'select count(*) from entries') == 1

    with reader.connect() as conn:
        with conn.begin() as txn:
            assert api.query_scalar(txn, 'select count(*) from entries') == 1
            with pytest.raises(sqlite3.OperationalError):
                api.exec(txn, "insert into entries values ('two')")

        with pytest.raises(ValueError, match='read-only'):
            with conn.begin(readonly=False):
                pass

    with writer.connect() as conn:
        with conn.begin(readonly=True) as txn:
            with pytest.raises(sqlite3.OperationalError):
                api.exec(txn, "insert into entries values ('two')")
        with conn.begin() as txn:
            api.exec(txn, "insert into entries values ('two')")

    assert api.query_scalar(reader, 'select count(*) from entries') == 2


def test_alias_to_writer_keeps_reader_intent():
    path = os.path.join(tempfile.mkdtemp(), 'sessions.db')
    spec = DbSpec('local', DbTypes.SQLITE, SqliteDbConfig(file_path=path))
    resolver = DbResolver(DbSets({'sessions': DbSet(spec, reader='writer', analytics='reader')}))
    writer = resolver.db('sessions')
    reader = resolver.db('sessions', 'reader')

    api.exec(writer, 'create table entries (value text)')
    with reader.connect() as conn:
        with pytest.raises(sqlite3.OperationalError):
            api.exec(conn, "insert into entries values ('one')")
        with conn.begin() as txn:
            with pytest.raises(sqlite3.OperationalError):
                api.exec(txn, "insert into entries values ('one')")
        with conn.begin(readonly=False) as txn:
            api.exec(txn, "insert into entries values ('one')")
    api.exec(writer, "insert into entries values ('one')")
    assert api.query_scalar(reader, 'select count(*) from entries') == 2

    with pytest.raises(ValueError, match='Circular'):
        DbSet(spec, reader='analytics', analytics='reader').spec('reader')


@pytest.mark.asyncs('asyncio')
async def test_async_sqlite_set():
    path = os.path.join(tempfile.mkdtemp(), 'sessions.db')
    async with DbResolver(_sqlite_sets(path)) as resolver:
        writer = await resolver.async_db('sessions')
        reader = await resolver.async_db('sessions', 'reader')

        await api.exec(writer, 'create table entries (value text)')
        await api.exec(writer, "insert into entries values ('one')")
        assert await api.query_scalar(reader, 'select value from entries') == 'one'

        async with reader.connect() as conn:
            async with conn.begin() as txn:
                with pytest.raises(sqlite3.OperationalError):
                    await api.exec(txn, "insert into entries values ('two')")


def test_postgres_resolver_readonly(harness):
    original = harness[HarnessDbs].specs()['postgres']
    url = original.loc
    assert isinstance(url, UrlDbLoc)
    assert isinstance(url.url, str)
    spec = dc.replace(original, loc=UrlDbLoc(SecretRef('postgres_url')))
    resolver = DbResolver(
        DbSets({'test': DbSet(spec, reader='writer')}),
        secrets=MappingSecrets({'postgres_url': url.url}),
    )
    with resolver.db('test', 'reader').connect() as conn:
        with conn.begin() as txn:
            assert api.query_scalar(txn, 'show transaction_read_only') == 'on'
    with resolver.db('test').connect() as conn:
        with conn.begin() as txn:
            assert api.query_scalar(txn, 'show transaction_read_only') == 'off'


def test_mysql_resolver_readonly(harness):
    spec = harness[HarnessDbs].specs()['mysql']
    resolver = DbResolver(DbSets({'test': DbSet(spec, reader='writer')}))
    table = 'om_dbsets_' + uuid.uuid4().hex
    try:
        api.exec(resolver.db('test'), f'create table {table} (value integer)')
        with resolver.db('test', 'reader').connect() as conn:
            with conn.begin() as txn:
                with pytest.raises(DatabaseError):
                    api.exec(txn, f'insert into {table} values (1)')  # noqa: S608
        with resolver.db('test').connect() as conn:
            with conn.begin() as txn:
                assert api.query_scalar(txn, 'select 1') == 1
    finally:
        api.exec(resolver.db('test'), f'drop table if exists {table}')


def test_driver_override():
    path = os.path.join(tempfile.mkdtemp(), 'override.db')
    config = SqliteDbConfig(file_path=path)
    spec = DbSpec('local', DbTypes.SQLITE, config, driver='custom')
    seen: list[DbSpec] = []

    def make_db(spec: DbSpec, secrets) -> api.Db:
        seen.append(spec)
        assert secrets is None
        return sqlite_db(config)

    resolver = DbResolver(
        DbSets({'test': DbSet(spec)}),
        sync_factories={'custom': make_db},
    )
    assert api.query_scalar(resolver.db('test'), 'select 1') == 1
    assert seen == [spec]
