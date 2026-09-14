# ruff: noqa: S608
import typing as ta
import urllib.parse

from ..... import check
from ..... import lang
from ....api import querierfuncs as qf
from ....api.asyncs import ImmediateSyncToAsyncRunner
from ....api.asyncs import SyncToAsyncDb
from ....dbs import UrlDbLoc
from ....drivers.og8000.core.sync import SyncCoreConnection
from ....dtypes import DATETIME
from ....dtypes import STRING
from ....dtypes import Integer
from ....dtypes import String
from ....inspect.migrating import migrate_table
from ....qualifiedname import qn
from ....tabledefs.diffing import AddTrigger
from ....tabledefs.diffing import AlterColumn
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
from ..drivers.og8000.sync import Og8000Db
from ..inspect import PostgresInspector
from ..tabledefs import PostgresTabledefRenderer


def _adb(harness):
    url = check.isinstance(check.isinstance(harness[HarnessDbs].specs()['postgres'].loc, UrlDbLoc).url, str)
    p_u = urllib.parse.urlparse(url)

    kwargs: dict[str, ta.Any] = {
        'user': check.not_none(p_u.username),
        'password': p_u.password,
        'host': p_u.hostname,
        'port': check.not_none(p_u.port),
        'database': p_u.path.lstrip('/') or 'postgres',
    }

    return SyncToAsyncDb(ImmediateSyncToAsyncRunner, Og8000Db(lambda: SyncCoreConnection(**kwargs)))


def test_qualified_lifecycle(harness) -> None:
    schema = 'test_qualified_lifecycle'

    async def inner() -> None:
        r = PostgresTabledefRenderer()
        insp = PostgresInspector()

        async with _adb(harness).connect() as conn:
            await qf.exec(conn, f'drop schema if exists {schema} cascade')
            await qf.exec(conn, f'create schema {schema}')

            td = TableDef(qn(schema, 'tq_users'), Elements(
                IdIntegerPrimaryKey(),
                CreatedAtUpdatedAt(),
                Column('name', String(length=40)),
                Column('bio', STRING, nullable=True),
                Column('age', Integer(bits=16), nullable=True),
                Index(['name']),
            ))
            assert (await migrate_table(conn, td, inspector=insp, renderer=r)).created

            reflected = check.not_none(await insp.reflect_table(conn, qn(schema, 'tq_users')))
            assert reflected.name == qn(schema, 'tq_users')
            assert {i.name for i in reflected.indexes} == {'tq_users__index__name'}
            assert {t.name for t in reflected.triggers} == {'tq_users__trigger__updated_at__updated_at'}

            # widths and lengths are lifted faithfully, so the re-run is a true no-op
            lifted = {c.name: c.type for c in insp.lift_table(reflected).elements[Column]}
            assert lifted['id'] == Integer(bits=64)
            assert lifted['name'] == String(length=40)
            assert lifted['bio'] == STRING
            assert lifted['age'] == Integer(bits=16)
            assert not (await migrate_table(conn, td, inspector=insp, renderer=r)).ops

            # a bare name resolves against the session's current schema: absent from public, present once switched
            assert await insp.reflect_table(conn, 'tq_users') is None
            await qf.exec(conn, f'set search_path to {schema}')
            assert check.not_none(await insp.reflect_table(conn, 'tq_users')).name == qn('tq_users')

            # a confident width change is altered in place
            grown = TableDef(qn(schema, 'tq_users'), Elements(*[
                Column('age', Integer(bits=64), nullable=True) if isinstance(e, Column) and e.name == 'age' else e
                for e in td.elements
            ]))
            m = await migrate_table(conn, grown, inspector=insp, renderer=r)
            assert [type(o) for o in m.ops] == [AlterColumn]
            assert not (await migrate_table(conn, grown, inspector=insp, renderer=r)).ops

            # and the updated-at trigger does its job
            await qf.exec(conn, f"insert into {schema}.tq_users (name, updated_at) values ('a', '2000-01-01')")
            await qf.exec(conn, f"update {schema}.tq_users set name = 'b'")
            assert await qf.query_scalar(conn, f"select updated_at > '2001-01-01' from {schema}.tq_users")

            await qf.exec(conn, f'drop schema if exists {schema} cascade')

    lang.sync_await(inner())


def test_trigger_change_is_drop_and_add(harness) -> None:
    tn = 'tq_trigger_change'

    async def inner() -> None:
        r = PostgresTabledefRenderer()
        insp = PostgresInspector()

        async with _adb(harness).connect() as conn:
            await qf.exec(conn, f'drop table if exists {tn} cascade')

            def td(col):
                return TableDef(qn(tn), Elements(
                    Column('id', Integer(bits=64)),
                    PrimaryKey(['id']),
                    Column('updated_at', DATETIME, nullable=True),
                    Column('modified_at', DATETIME, nullable=True),
                    UpdatedAtTrigger(col),
                ))

            assert (await migrate_table(conn, td('updated_at'), inspector=insp, renderer=r)).created

            # somebody else's trigger (and function) on the same table: never ours to touch
            await qf.exec(conn, (
                f'create or replace function {tn}_noop() returns trigger language plpgsql '
                'as $$ begin return new; end $$'
            ))
            await qf.exec(conn, (
                f'create trigger somebody_elses before insert on {tn} for each row execute function {tn}_noop()'
            ))

            m = await migrate_table(conn, td('modified_at'), inspector=insp, renderer=r)
            assert [type(o) for o in m.ops] == [AddTrigger, DropTrigger]

            reflected = check.not_none(await insp.reflect_table(conn, tn))
            assert {t.name for t in reflected.triggers} == {f'{tn}__trigger__updated_at__modified_at', 'somebody_elses'}

            # the dropped trigger took its function with it; the new one has its own
            fns = {
                r_.to_dict()['proname']
                for r_ in await qf.query_all(conn, (
                    f"select proname from pg_proc where proname like '{tn}__function__%'"
                ))
            }
            assert fns == {f'{tn}__function__updated_at__modified_at'}

            assert not (await migrate_table(conn, td('modified_at'), inspector=insp, renderer=r)).ops

            await qf.exec(conn, f'drop table if exists {tn} cascade')
            await qf.exec(conn, f'drop function if exists {tn}_noop()')

    lang.sync_await(inner())
