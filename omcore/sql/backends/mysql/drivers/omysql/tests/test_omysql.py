import typing as ta
import urllib.parse

import pytest

from ....... import check
from ......api import querierfuncs as qf
from ......dbs import UrlDbLoc
from ......drivers.omysql.core.asyncio import AsyncioConnection
from ......drivers.omysql.core.sync import SyncConnection
from ......queries import Q
from ......tests.harness import HarnessDbs
from ..asyncio import AsyncioOmysqlDb
from ..sync import OmysqlDb


##


def _connect_kwargs(harness) -> dict[str, ta.Any]:
    url = check.isinstance(check.isinstance(harness[HarnessDbs].specs()['mysql'].loc, UrlDbLoc).url, str)
    p_u = urllib.parse.urlparse(url)

    return {
        'user': check.not_none(p_u.username),
        'password': p_u.password or '',
        'host': p_u.hostname,
        'port': check.not_none(p_u.port),
    }


def test_omysql_sync(harness) -> None:
    kwargs = _connect_kwargs(harness)
    db = OmysqlDb(lambda: SyncConnection(**kwargs))

    with db.connect() as conn:
        rows = qf.query_all(conn, 'select 1 as a union select 2 order by a')
        assert [r.values for r in rows] == [(1,), (2,)]
        assert [c.name for c in rows[0].columns] == ['a']

        assert qf.query_scalar(conn, 'select %s as v', ('barf',)) == 'barf'
        assert qf.query_scalar(conn, 'select %(x)s as x', {'x': 420}) == 420

        qf.exec(conn, 'create database if not exists test_omysql_api')
        try:
            qf.exec(conn, 'create temporary table test_omysql_api.tbl (i int)')

            with conn.begin() as txn:
                qf.exec(txn, 'insert into test_omysql_api.tbl values (%s)', (420,))
            assert qf.query_scalar(conn, 'select count(*) from test_omysql_api.tbl') == 1

            with conn.begin() as txn:
                qf.exec(txn, 'insert into test_omysql_api.tbl values (%s)', (421,))
                txn.rollback()
            assert qf.query_scalar(conn, 'select count(*) from test_omysql_api.tbl') == 1

            def txn_boom():
                with conn.begin() as txn:
                    qf.exec(txn, 'insert into test_omysql_api.tbl values (%s)', (422,))
                    raise RuntimeError('boom')

            with pytest.raises(RuntimeError, match='boom'):
                txn_boom()
            assert qf.query_scalar(conn, 'select count(*) from test_omysql_api.tbl') == 1
        finally:
            qf.exec(conn, 'drop database if exists test_omysql_api')

    assert [r.values for r in qf.query_all(db, Q.select([1]))] == [(1,)]


@pytest.mark.asyncs('asyncio')
async def test_omysql_asyncio(harness) -> None:
    kwargs = _connect_kwargs(harness)
    adb = AsyncioOmysqlDb(lambda: AsyncioConnection.connect(**kwargs))

    async with adb.connect() as conn:
        rows = await qf.query_all(conn, 'select 1 as a union select 2 order by a')
        assert [r.values for r in rows] == [(1,), (2,)]
        assert [c.name for c in rows[0].columns] == ['a']

        assert await qf.query_scalar(conn, 'select %s as v', ('barf',)) == 'barf'
        assert await qf.query_scalar(conn, 'select %(x)s as x', {'x': 420}) == 420

        await qf.exec(conn, 'create database if not exists test_omysql_api')
        try:
            await qf.exec(conn, 'create temporary table test_omysql_api.tbl (i int)')

            async with conn.begin() as txn:
                await qf.exec(txn, 'insert into test_omysql_api.tbl values (%s)', (420,))
            assert await qf.query_scalar(conn, 'select count(*) from test_omysql_api.tbl') == 1

            async with conn.begin() as txn:
                await qf.exec(txn, 'insert into test_omysql_api.tbl values (%s)', (421,))
                await txn.rollback()
            assert await qf.query_scalar(conn, 'select count(*) from test_omysql_api.tbl') == 1

            async def txn_boom():
                async with conn.begin() as txn:
                    await qf.exec(txn, 'insert into test_omysql_api.tbl values (%s)', (422,))
                    raise RuntimeError('boom')

            with pytest.raises(RuntimeError, match='boom'):
                await txn_boom()
            assert await qf.query_scalar(conn, 'select count(*) from test_omysql_api.tbl') == 1
        finally:
            await qf.exec(conn, 'drop database if exists test_omysql_api')

    assert [r.values for r in await qf.query_all(adb, Q.select([1]))] == [(1,)]
