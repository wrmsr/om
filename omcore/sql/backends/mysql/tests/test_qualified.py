# ruff: noqa: S608
import typing as ta
import urllib.parse

from ..... import check
from ..... import lang
from ....api import querierfuncs as qf
from ....api.asyncs import ImmediateSyncToAsyncRunner
from ....api.asyncs import SyncToAsyncDb
from ....dbs import UrlDbLoc
from ....drivers.omysql.core.sync import SyncConnection
from ....dtypes import DATETIME
from ....dtypes import STRING
from ....dtypes import Integer
from ....dtypes import String
from ....inspect.migrating import migrate_table
from ....qualifiedname import qn
from ....tabledefs.diffing import AddTrigger
from ....tabledefs.diffing import AlterColumn
from ....tabledefs.diffing import DropIndex
from ....tabledefs.diffing import DropTrigger
from ....tabledefs.elements import Column
from ....tabledefs.elements import CreatedAtUpdatedAt
from ....tabledefs.elements import Elements
from ....tabledefs.elements import IdIntegerPrimaryKey
from ....tabledefs.elements import Index
from ....tabledefs.elements import PrimaryKey
from ....tabledefs.elements import UpdatedAtTrigger
from ....tabledefs.tabledefs import TableDef
from ....tests.harness import HarnessDbs
from ..drivers.omysql.sync import OmysqlDb
from ..inspect import MysqlInspector
from ..tabledefs import MysqlTabledefRenderer


def _adb(harness):
    url = check.isinstance(check.isinstance(harness[HarnessDbs].specs()['mysql'].loc, UrlDbLoc).url, str)
    p_u = urllib.parse.urlparse(url)

    kwargs: dict[str, ta.Any] = {
        'user': check.not_none(p_u.username),
        'password': p_u.password or '',
        'host': p_u.hostname,
        'port': check.not_none(p_u.port),
    }

    return SyncToAsyncDb(ImmediateSyncToAsyncRunner, OmysqlDb(lambda: SyncConnection(**kwargs)))


def test_qualified_lifecycle(harness) -> None:
    db = 'om_test'
    tn = 'tq_users'

    async def inner() -> None:
        r = MysqlTabledefRenderer()
        insp = MysqlInspector()

        async with _adb(harness).connect() as conn:
            await qf.exec(conn, f'create database if not exists {db}')
            await qf.exec(conn, f'drop table if exists {db}.{tn}')

            def td(*extra):
                return TableDef(qn(db, tn), Elements(
                    IdIntegerPrimaryKey(),
                    CreatedAtUpdatedAt(),
                    Column('name', String(length=40)),
                    Column('bio', STRING, nullable=True),
                    Column('age', Integer(bits=16), nullable=True),
                    *extra,
                ))

            with_index = td(Index(['name']))
            assert (await migrate_table(conn, with_index, inspector=insp, renderer=r)).created

            reflected = check.not_none(await insp.reflect_table(conn, qn(db, tn)))
            assert reflected.name == qn(db, tn)
            assert {i.name for i in reflected.indexes} == {f'{tn}__index__name'}
            assert {t.name for t in reflected.triggers} == {f'{tn}__trigger__updated_at__updated_at'}

            lifted = {c.name: c.type for c in insp.lift_table(reflected).elements[Column]}
            assert lifted['id'] == Integer(bits=64)
            assert lifted['name'] == String(length=40)
            assert lifted['bio'] == STRING
            assert lifted['age'] == Integer(bits=16)
            assert not (await migrate_table(conn, with_index, inspector=insp, renderer=r)).ops

            # a bare name resolves against the connection's current database, which is none here
            assert await insp.reflect_table(conn, tn) is None

            # a confident width change is altered in place, and mysql's per-table 'drop index ... on' works
            grown = TableDef(qn(db, tn), Elements(*[
                Column('age', Integer(bits=64), nullable=True) if isinstance(e, Column) and e.name == 'age' else e
                for e in td().elements
            ]))
            m = await migrate_table(conn, grown, inspector=insp, renderer=r)
            assert {type(o) for o in m.ops} == {AlterColumn, DropIndex}
            assert not (await migrate_table(conn, grown, inspector=insp, renderer=r)).ops
            assert not check.not_none(await insp.reflect_table(conn, qn(db, tn))).indexes

            # and the updated-at trigger does its job
            await qf.exec(conn, f"insert into {db}.{tn} (name, updated_at) values ('a', '2000-01-01')")
            await qf.exec(conn, f"update {db}.{tn} set name = 'b'")
            assert await qf.query_scalar(conn, f"select updated_at > '2001-01-01' from {db}.{tn}")

            await qf.exec(conn, f'drop table if exists {db}.{tn}')

    lang.sync_await(inner())


def test_trigger_change_is_drop_and_add(harness) -> None:
    db = 'om_test'
    tn = 'tq_trigger_change'

    async def inner() -> None:
        r = MysqlTabledefRenderer()
        insp = MysqlInspector()

        async with _adb(harness).connect() as conn:
            await qf.exec(conn, f'create database if not exists {db}')
            await qf.exec(conn, f'drop table if exists {db}.{tn}')

            def td(col):
                return TableDef(qn(db, tn), Elements(
                    Column('id', Integer(bits=64)),
                    PrimaryKey(['id']),
                    Column('updated_at', DATETIME, nullable=True),
                    Column('modified_at', DATETIME, nullable=True),
                    UpdatedAtTrigger(col),
                ))

            assert (await migrate_table(conn, td('updated_at'), inspector=insp, renderer=r)).created

            # somebody else's trigger on the same table: never ours to touch
            await qf.exec(conn, (
                f'create trigger {db}.somebody_elses before insert on {db}.{tn} for each row set new.id = new.id'
            ))

            m = await migrate_table(conn, td('modified_at'), inspector=insp, renderer=r)
            assert [type(o) for o in m.ops] == [AddTrigger, DropTrigger]

            reflected = check.not_none(await insp.reflect_table(conn, qn(db, tn)))
            assert {t.name for t in reflected.triggers} == {f'{tn}__trigger__updated_at__modified_at', 'somebody_elses'}

            assert not (await migrate_table(conn, td('modified_at'), inspector=insp, renderer=r)).ops

            await qf.exec(conn, f'drop table if exists {db}.{tn}')

    lang.sync_await(inner())
