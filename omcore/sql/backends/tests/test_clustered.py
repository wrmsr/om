"""
A clustered table, all the way down to a live db and back, on every dialect: it is created in whatever physical form the
backend has for it, migrating it again finds nothing to do - the reflection of that form being what it is diffed as -
and its triggers, whenever they are added, are those of the table as defined.
"""
import typing as ta

import pytest

from .... import check
from .... import lang
from .... import typedvalues as tv
from ...api import querierfuncs as qf
from ...api.asyncs import ImmediateSyncToAsyncRunner
from ...api.asyncs import SyncToAsyncDb
from ...api.core import Db
from ...dtypes import DATETIME
from ...dtypes import INTEGER
from ...dtypes import STRING
from ...inspect.migrating import migrate_table
from ...tabledefs.diffing import AddTrigger
from ...tabledefs.elements import Column
from ...tabledefs.elements import Index
from ...tabledefs.elements import PrimaryKey
from ...tabledefs.elements import UpdatedAtTrigger
from ...tabledefs.options import Clustered
from ...tabledefs.tabledefs import TableDef
from ...tabledefs.tabledefs import table_def
from ...tests.harness import HarnessSandboxes
from ..base import Backend
from ..mysql.backend import MysqlBackend
from ..postgres.backend import PostgresBackend
from ..sqlite.backend import SqliteBackend


##


def _entries(*extra: ta.Any) -> TableDef:
    # The clustered key's order is deliberately not its columns' order in the table.
    return table_def(
        'entries',
        Column('id', STRING),
        PrimaryKey(['id']),
        Column('seq', INTEGER),
        Column('session_id', STRING),
        Column('entry', STRING),
        Column('updated_at', DATETIME),
        Index(['session_id', 'seq'], name='entries__session_id__seq', unique=True, options=tv.TypedValues(Clustered())),
        *extra,
    )


def _check_clustered(db: Db, backend: Backend, *, physical_primary_key: ta.Sequence[str]) -> None:
    r = backend.tabledef_renderer
    insp = backend.inspector

    async def inner() -> None:
        async with SyncToAsyncDb(ImmediateSyncToAsyncRunner, db).connect() as conn:
            td = _entries()
            assert (await migrate_table(conn, td, inspector=insp, renderer=r)).created

            # what is there is the physical table, its key in the key's own order
            lifted = insp.lift_table(check.not_none(await insp.reflect_table(conn, 'entries')))
            assert list(lifted.elements[PrimaryKey].columns) == list(physical_primary_key)

            # which is what the definition is diffed as: a true no-op
            m = await migrate_table(conn, td, inspector=insp, renderer=r)
            assert not m.created and not m.ops

            # a trigger added later is rendered against the definition, and works
            td = _entries(UpdatedAtTrigger('updated_at'))
            [op] = (await migrate_table(conn, td, inspector=insp, renderer=r)).ops
            assert isinstance(op, AddTrigger)
            assert list(op.table_def.elements[PrimaryKey].columns) == ['id']
            assert not (await migrate_table(conn, td, inspector=insp, renderer=r)).ops

            for i, s, q in [('a', 's1', 1), ('b', 's1', 2), ('c', 's2', 1)]:
                await qf.exec(conn, (
                    'insert into entries (id, session_id, seq, entry, updated_at) '  # noqa
                    f"values ('{i}', '{s}', {q}, 'x', '2000-01-01 00:00:00')"
                ))
            await qf.exec(conn, "update entries set entry = 'y' where id = 'a'")
            rows = {
                row.values[0]: row.values[1]
                for row in await qf.query_all(conn, "select id, updated_at > '2001-01-01 00:00:00' from entries")
            }
            assert {k: bool(v) for k, v in rows.items()} == {'a': True, 'b': False, 'c': False}

            # both keys are still keys: the one it was defined with, and the one it is kept by
            for i, s, q in [('a', 's9', 9), ('z', 's1', 2)]:
                with pytest.raises(Exception):  # noqa
                    await qf.exec(conn, (
                        'insert into entries (id, session_id, seq, entry, updated_at) '  # noqa
                        f"values ('{i}', '{s}', {q}, 'x', '2000-01-01 00:00:00')"
                    ))
            assert await qf.query_scalar(conn, 'select count(*) from entries') == 3

    lang.sync_await(inner())


def _check_primary_key_order(db: Db, backend: Backend) -> None:
    td = table_def('ordered', Column('a', INTEGER), Column('b', INTEGER), PrimaryKey(['b', 'a']))

    r = backend.tabledef_renderer
    insp = backend.inspector

    async def inner() -> None:
        async with SyncToAsyncDb(ImmediateSyncToAsyncRunner, db).connect() as conn:
            assert (await migrate_table(conn, td, inspector=insp, renderer=r)).created

            reflected = check.not_none(await insp.reflect_table(conn, 'ordered'))
            assert list(reflected.primary_key) == ['b', 'a']

            assert not (await migrate_table(conn, td, inspector=insp, renderer=r)).ops

    lang.sync_await(inner())


##


def test_sqlite(harness) -> None:
    with harness[HarnessSandboxes].sqlite().allocate() as sb:
        _check_primary_key_order(sb.db(), SqliteBackend())
        _check_clustered(sb.db(), SqliteBackend(), physical_primary_key=['session_id', 'seq'])

        # the table is its clustered key's b-tree, and its defined key an index on it
        with sb.db().connect() as conn:
            def plan(q: str) -> str:
                return ' '.join(str(row.values[-1]) for row in qf.query_all(conn, 'explain query plan ' + q))

            assert 'USING PRIMARY KEY (session_id=?)' in plan("select * from entries where session_id = 's1' order by seq")  # noqa
            assert 'USING INDEX entries__index__id (id=?)' in plan("select * from entries where id = 'a'")


def test_postgres(harness) -> None:
    with harness[HarnessSandboxes].postgres().allocate() as sb:
        _check_primary_key_order(sb.db(), PostgresBackend())
        _check_clustered(sb.db(), PostgresBackend(), physical_primary_key=['id'])

        # nothing keeps a heap in order, so the table is as it was defined - with the index marked the one to cluster on
        with sb.db().connect() as conn:
            assert qf.query_scalar(conn, (
                'select ix.indisclustered from pg_index ix join pg_class i on i.oid = ix.indexrelid '
                "where i.relname = 'entries__session_id__seq' and i.relnamespace = current_schema()::regnamespace"
            )) is True
            qf.exec(conn, 'cluster entries')


def test_mysql(harness) -> None:
    with harness[HarnessSandboxes].mysql().allocate() as sb:
        _check_primary_key_order(sb.db(), MysqlBackend())
        _check_clustered(sb.db(), MysqlBackend(), physical_primary_key=['session_id', 'seq'])


##


def test_render() -> None:
    td = _entries()

    assert SqliteBackend().tabledef_renderer.render_create_statements(td) == [
        (
            'create table "entries" (\n'
            '  "id" text not null,\n'
            '  "seq" integer not null,\n'
            '  "session_id" text not null,\n'
            '  "entry" text not null,\n'
            '  "updated_at" datetime not null,\n'
            '  primary key ("session_id", "seq")\n'
            ')\n'
            'without rowid'
        ),
        'create unique index "entries__index__id" on "entries" ("id")\n',
    ]

    assert PostgresBackend().tabledef_renderer.render_create_statements(td) == [
        (
            'create table "entries" (\n'
            '  "id" text not null,\n'
            '  "seq" integer not null,\n'
            '  "session_id" text not null,\n'
            '  "entry" text not null,\n'
            '  "updated_at" timestamp with time zone not null,\n'
            '  primary key ("id")\n'
            ')'
        ),
        'create unique index "entries__session_id__seq" on "entries" ("session_id", "seq")\n',
        'alter table "entries" cluster on "entries__session_id__seq"',
    ]
