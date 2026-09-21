"""
What an updated-at trigger does, which is to be the same thing on every dialect: an update which changes the column is
taken at its word, and one which does not is stamped - later than whatever the column held, whatever the time.
"""
import datetime

from .... import lang
from ...api import querierfuncs as qf
from ...api.asyncs import ImmediateSyncToAsyncRunner
from ...api.asyncs import SyncToAsyncDb
from ...api.core import Db
from ...dtypes import DATETIME
from ...dtypes import INTEGER
from ...dtypes import STRING
from ...inspect.migrating import migrate_table
from ...tabledefs.elements import Column
from ...tabledefs.elements import CreatedAtUpdatedAt
from ...tabledefs.elements import PrimaryKey
from ...tabledefs.tabledefs import table_def
from ...tests.harness import HarnessSandboxes
from ..base import Backend
from ..mysql.backend import MysqlBackend
from ..postgres.backend import PostgresBackend
from ..sqlite.backend import SqliteBackend


##


def _check_updated_at(db: Db, backend: Backend, *, tick: datetime.timedelta) -> None:
    td = table_def(
        'stamped',
        Column('id', STRING),
        PrimaryKey(['id']),
        Column('n', INTEGER),
        CreatedAtUpdatedAt(),
    )

    r = backend.tabledef_renderer
    insp = backend.inspector

    async def create() -> None:
        async with SyncToAsyncDb(ImmediateSyncToAsyncRunner, db).connect() as aconn:
            assert (await migrate_table(aconn, td, inspector=insp, renderer=r)).created

    lang.sync_await(create())

    with db.connect() as conn:
        def updated_at() -> datetime.datetime:
            return backend.dtype_codec.decode(DATETIME, qf.query_scalar(conn, "select updated_at from stamped where id = 'a'"))  # noqa

        def utc(year: int, month: int, day: int) -> datetime.datetime:
            return datetime.datetime(year, month, day, tzinfo=datetime.UTC)

        qf.exec(conn, (
            'insert into stamped (id, n, created_at, updated_at) '  # noqa
            "values ('a', 0, '2000-01-01 00:00:00', '2000-01-01 00:00:00')"
        ))
        assert updated_at() == utc(2000, 1, 1)

        # an update with nothing to say of the column is stamped with the time
        before = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=5)
        qf.exec(conn, "update stamped set n = 1 where id = 'a'")
        assert before < updated_at() < before + datetime.timedelta(minutes=5)

        # one which changes it is taken at its word - as a newer version of a row kept elsewhere would be, arriving here
        qf.exec(conn, "update stamped set n = 2, updated_at = '2999-01-01 00:00:00' where id = 'a'")
        assert updated_at() == utc(2999, 1, 1)

        # and from there the time is of no use, being no later than what is there: so it is the least there is past
        # that, update after update, no two of them alike
        for i in range(1, 6):
            qf.exec(conn, f"update stamped set n = n + 1 where id = 'a'")  # noqa
            assert updated_at() == utc(2999, 1, 1) + (tick * i)

        # even given the very value it already has, which is as good as nothing said: there is no telling them apart
        qf.exec(conn, f"update stamped set n = 99, updated_at = (select u from (select updated_at as u from stamped where id = 'a') x) where id = 'a'")  # noqa
        assert updated_at() == utc(2999, 1, 1) + (tick * 6)

        # back in time is as much its word as any, and the clock is of use again
        qf.exec(conn, "update stamped set updated_at = '2001-01-01 00:00:00' where id = 'a'")
        assert updated_at() == utc(2001, 1, 1)
        qf.exec(conn, "update stamped set n = 100 where id = 'a'")
        assert before < updated_at() < before + datetime.timedelta(minutes=5)

        assert backend.dtype_codec.decode(DATETIME, qf.query_scalar(conn, 'select created_at from stamped')) == utc(2000, 1, 1)  # noqa


##


def test_sqlite(harness) -> None:
    with harness[HarnessSandboxes].sqlite().allocate() as sb:
        _check_updated_at(sb.db(), SqliteBackend(), tick=datetime.timedelta(milliseconds=1))


def test_postgres(harness) -> None:
    with harness[HarnessSandboxes].postgres().allocate() as sb:
        _check_updated_at(sb.db(), PostgresBackend(), tick=datetime.timedelta(microseconds=1))


def test_mysql(harness) -> None:
    with harness[HarnessSandboxes].mysql().allocate() as sb:
        _check_updated_at(sb.db(), MysqlBackend(), tick=datetime.timedelta(microseconds=1))
