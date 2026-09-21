"""
What an identity column is, which is to be the same thing on every dialect: given a value when it has none, and never
one that any row of the table has had before - whether or not that row is still there.
"""
from .... import check
from .... import lang
from ...api import querierfuncs as qf
from ...api.asyncs import ImmediateSyncToAsyncRunner
from ...api.asyncs import SyncToAsyncDb
from ...api.core import Db
from ...dtypes import STRING
from ...inspect.migrating import migrate_table
from ...tabledefs.elements import Column
from ...tabledefs.elements import IdIntegerPrimaryKey
from ...tabledefs.elements import PrimaryKey
from ...tabledefs.tabledefs import table_def
from ...tests.harness import HarnessSandboxes
from ..base import Backend
from ..mysql.backend import MysqlBackend
from ..postgres.backend import PostgresBackend
from ..sqlite.backend import SqliteBackend


##


def _check_identity(db: Db, backend: Backend) -> None:
    td = table_def(
        'things',
        IdIntegerPrimaryKey(),
        Column('name', STRING),
    )

    r = backend.tabledef_renderer
    insp = backend.inspector

    async def migrate() -> None:
        async with SyncToAsyncDb(ImmediateSyncToAsyncRunner, db).connect() as aconn:
            assert (await migrate_table(aconn, td, inspector=insp, renderer=r)).created

            # however the dialect says it, it reflects as the primary key it is, and migrates as nothing to do
            lifted = insp.lift_table(check.not_none(await insp.reflect_table(aconn, 'things')))
            assert list(lifted.elements[PrimaryKey].columns) == ['id']
            assert not (await migrate_table(aconn, td, inspector=insp, renderer=r)).ops

    lang.sync_await(migrate())

    with db.connect() as conn:
        def insert(name: str) -> int:
            qf.exec(conn, f"insert into things (name) values ('{name}')")  # noqa
            return int(qf.query_scalar(conn, f"select id from things where name = '{name}'"))  # noqa

        ids = [insert(n) for n in 'abc']
        assert ids == sorted(set(ids))

        # the highest goes, and its id does not come around again
        qf.exec(conn, f'delete from things where id = {ids[-1]}')  # noqa
        ids.append(insert('d'))
        assert ids[-1] > ids[-2]

        # nor do any of them once every row has gone, with nothing left to count on from
        qf.exec(conn, 'delete from things')  # noqa
        ids.append(insert('e'))
        assert ids[-1] > ids[-2]

        assert ids == sorted(set(ids))


##


def test_sqlite(harness) -> None:
    with harness[HarnessSandboxes].sqlite().allocate() as sb:
        _check_identity(sb.db(), SqliteBackend())


def test_postgres(harness) -> None:
    with harness[HarnessSandboxes].postgres().allocate() as sb:
        _check_identity(sb.db(), PostgresBackend())


def test_mysql(harness) -> None:
    with harness[HarnessSandboxes].mysql().allocate() as sb:
        _check_identity(sb.db(), MysqlBackend())
