import typing as ta
import urllib.parse

import pytest

from ....... import check
from ......api import querierfuncs as qf
from ......dbs import UrlDbLoc
from ......drivers.og8000.core.asyncio import AsyncioCoreConnection
from ......drivers.og8000.core.sync import SyncCoreConnection
from ......queries import Q
from ......tests.harness import HarnessDbs
from ..asyncio import AsyncioOg8000Db
from ..sync import Og8000Db


##


def _connect_kwargs(harness) -> dict[str, ta.Any]:
    url = check.isinstance(check.isinstance(harness[HarnessDbs].specs()['postgres'].loc, UrlDbLoc).url, str)
    p_u = urllib.parse.urlparse(url)

    return {
        'user': check.not_none(p_u.username),
        'password': p_u.password,
        'host': p_u.hostname,
        'port': check.not_none(p_u.port),
        'database': p_u.path.lstrip('/') or None,
    }


def test_og8000_sync(harness) -> None:
    kwargs = _connect_kwargs(harness)
    db = Og8000Db(lambda: SyncCoreConnection(**kwargs))

    with db.connect() as conn:
        rows = qf.query_all(conn, 'select 1 as a union select 2 order by a')
        assert [r.values for r in rows] == [(1,), (2,)]
        assert [c.name for c in rows[0].columns] == ['a']

        assert qf.query_scalar(conn, 'select $1::text as v', ('barf',)) == 'barf'

        qf.exec(conn, 'create temporary table test_og8000_api_tbl (i int)')

        with conn.begin() as txn:
            qf.exec(txn, 'insert into test_og8000_api_tbl values ($1)', (420,))
        assert qf.query_scalar(conn, 'select count(*) from test_og8000_api_tbl') == 1

        with conn.begin() as txn:
            qf.exec(txn, 'insert into test_og8000_api_tbl values ($1)', (421,))
            txn.rollback()
        assert qf.query_scalar(conn, 'select count(*) from test_og8000_api_tbl') == 1

        def txn_boom():
            with conn.begin() as txn:
                qf.exec(txn, 'insert into test_og8000_api_tbl values ($1)', (422,))
                raise RuntimeError('boom')

        with pytest.raises(RuntimeError, match='boom'):
            txn_boom()
        assert qf.query_scalar(conn, 'select count(*) from test_og8000_api_tbl') == 1

    assert [r.values for r in qf.query_all(db, Q.select([1]))] == [(1,)]


@pytest.mark.asyncs('asyncio')
async def test_og8000_asyncio(harness) -> None:
    kwargs = _connect_kwargs(harness)
    adb = AsyncioOg8000Db(lambda: AsyncioCoreConnection.connect(**kwargs))

    async with adb.connect() as conn:
        rows = await qf.query_all(conn, 'select 1 as a union select 2 order by a')
        assert [r.values for r in rows] == [(1,), (2,)]
        assert [c.name for c in rows[0].columns] == ['a']

        assert await qf.query_scalar(conn, 'select $1::text as v', ('barf',)) == 'barf'

        await qf.exec(conn, 'create temporary table test_og8000_api_tbl (i int)')

        async with conn.begin() as txn:
            await qf.exec(txn, 'insert into test_og8000_api_tbl values ($1)', (420,))
        assert await qf.query_scalar(conn, 'select count(*) from test_og8000_api_tbl') == 1

        async with conn.begin() as txn:
            await qf.exec(txn, 'insert into test_og8000_api_tbl values ($1)', (421,))
            await txn.rollback()
        assert await qf.query_scalar(conn, 'select count(*) from test_og8000_api_tbl') == 1

        async def txn_boom():
            async with conn.begin() as txn:
                await qf.exec(txn, 'insert into test_og8000_api_tbl values ($1)', (422,))
                raise RuntimeError('boom')

        with pytest.raises(RuntimeError, match='boom'):
            await txn_boom()
        assert await qf.query_scalar(conn, 'select count(*) from test_og8000_api_tbl') == 1

    assert [r.values for r in await qf.query_all(adb, Q.select([1]))] == [(1,)]
