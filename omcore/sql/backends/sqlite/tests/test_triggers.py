import re
import sqlite3

from ..... import check
from ..... import lang
from ....api import querierfuncs as qf
from ....api.asyncs import ImmediateSyncToAsyncRunner
from ....api.asyncs import SyncToAsyncDb
from ....api.dbapi import ClosingDbapiConnector
from ....api.dbapi import DbapiDb
from ....dtypes import DATETIME
from ....dtypes import STRING
from ....inspect.migrating import migrate_table
from ....params import ParamStyle
from ....qualifiedname import qn
from ....tabledefs.diffing import AddTrigger
from ....tabledefs.diffing import DropTrigger
from ....tabledefs.elements import Column
from ....tabledefs.elements import CreatedAtUpdatedAt
from ....tabledefs.elements import Elements
from ....tabledefs.elements import IdIntegerPrimaryKey
from ....tabledefs.elements import Index
from ....tabledefs.elements import UpdatedAtTrigger
from ....tabledefs.tabledefs import TableDef
from ..inspect import SqliteInspector
from ..tabledefs import SqliteTabledefRenderer


def _adb():
    return SyncToAsyncDb(
        ImmediateSyncToAsyncRunner,
        DbapiDb(ClosingDbapiConnector(sqlite3.connect, ':memory:', autocommit=True), param_style=ParamStyle.QMARK),
    )


def test_updated_at_trigger_lifecycle() -> None:
    async def inner() -> None:
        r = SqliteTabledefRenderer()
        insp = SqliteInspector()

        async with _adb().connect() as conn:
            td = TableDef(qn('users'), Elements(
                IdIntegerPrimaryKey(),
                CreatedAtUpdatedAt(),
                Column('name', STRING),
            ))
            m1 = await migrate_table(conn, td, inspector=insp, renderer=r)
            assert m1.created

            # somebody else's trigger on the same table: never ours to touch
            await qf.exec(conn, 'create trigger "somebody_elses" after insert on "users" begin select 1; end')

            reflected = check.not_none(await insp.reflect_table(conn, 'users'))
            assert {t.name for t in reflected.triggers} == {'users__trigger__updated_at__updated_at', 'somebody_elses'}

            # the reflected trigger matches the in-code one by name, the foreign one is ignored: a true no-op
            m2 = await migrate_table(conn, td, inspector=insp, renderer=r)
            assert not m2.ops

            # and the trigger actually does its job
            await qf.exec(conn, "insert into users (name, updated_at) values ('a', '2000-01-01 00:00:00')")
            await qf.exec(conn, "update users set name = 'b'")
            assert await qf.query_scalar(conn, 'select updated_at from users') != '2000-01-01 00:00:00'

            # what the default gives a row and what the trigger gives it are both to the millisecond, in the one form
            for q in ('select created_at from users', 'select updated_at from users'):
                assert re.fullmatch(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3}', await qf.query_scalar(conn, q))

    lang.sync_await(inner())


def test_trigger_change_is_drop_and_add() -> None:
    async def inner() -> None:
        r = SqliteTabledefRenderer()
        insp = SqliteInspector()

        async with _adb().connect() as conn:
            def td(col):
                return TableDef(qn('t'), Elements(
                    IdIntegerPrimaryKey(),
                    Column('updated_at', DATETIME, nullable=True),
                    Column('modified_at', DATETIME, nullable=True),
                    UpdatedAtTrigger(col),
                ))

            assert (await migrate_table(conn, td('updated_at'), inspector=insp, renderer=r)).created
            await qf.exec(conn, 'create trigger "somebody_elses" after insert on "t" begin select 1; end')

            # moving the trigger to another column: the stale one is in our namespace and goes, the new one comes
            m = await migrate_table(conn, td('modified_at'), inspector=insp, renderer=r)
            assert [type(o) for o in m.ops] == [AddTrigger, DropTrigger]

            reflected = check.not_none(await insp.reflect_table(conn, 't'))
            assert {t.name for t in reflected.triggers} == {'t__trigger__updated_at__modified_at', 'somebody_elses'}

            assert not (await migrate_table(conn, td('modified_at'), inspector=insp, renderer=r)).ops

    lang.sync_await(inner())


def test_qualified_lifecycle() -> None:
    async def inner() -> None:
        r = SqliteTabledefRenderer()
        insp = SqliteInspector()

        async with _adb().connect() as conn:
            td = TableDef(qn('main', 'users'), Elements(
                IdIntegerPrimaryKey(),
                CreatedAtUpdatedAt(),
                Column('name', STRING),
                Index(['name']),
            ))
            assert (await migrate_table(conn, td, inspector=insp, renderer=r)).created

            reflected = check.not_none(await insp.reflect_table(conn, qn('main', 'users')))
            assert reflected.name == qn('main', 'users')
            assert {i.name for i in reflected.indexes} == {'users__index__name'}
            assert {t.name for t in reflected.triggers} == {'users__trigger__updated_at__updated_at'}

            assert not (await migrate_table(conn, td, inspector=insp, renderer=r)).ops

            # the same table seen through a bare name reflects under that name
            assert check.not_none(await insp.reflect_table(conn, 'users')).name == qn('users')

            assert await insp.reflect_table(conn, qn('temp', 'users')) is None

    lang.sync_await(inner())
