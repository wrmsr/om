"""Live tests of the sync and async MySQL connections against the server described by tests/dbs.py."""
import asyncio

import pytest

from ...err import OperationalError
from ...tests.dbs import DATABASES
from ..asyncio import AsyncioConnection
from ..sync import SyncConnection


def _kwargs(**over):
    params = {k: v for k, v in DATABASES[0].items() if k not in ('use_unicode', 'local_infile')}
    params['password'] = params.pop('passwd', '')
    params.update(over)
    return params


def test_sync_ssl_connect():
    con = SyncConnection(**_kwargs())
    try:
        assert con.is_ssl
        con.query('select 1')
        assert con.result is not None and con.result.rows == ((1,),)
    finally:
        con.close()


def test_sync_no_ssl_connect():
    con = SyncConnection(**_kwargs(ssl_disabled=True))
    try:
        assert not con.is_ssl
        con.query('select 2')
        assert con.result is not None and con.result.rows == ((2,),)
    finally:
        con.close()


def test_sync_bad_password():
    with pytest.raises(OperationalError):
        SyncConnection(**_kwargs(password='definitely-wrong'))  # noqa: S106


def test_async_ssl_connect():
    async def main():
        con = await AsyncioConnection.connect(**_kwargs())
        try:
            assert con.is_ssl
            await con.query('select 1')
            assert con.result is not None and con.result.rows == ((1,),)
        finally:
            await con.close()

    asyncio.run(main())


def test_async_queries_and_unbuffered():
    async def main():
        async with await AsyncioConnection.connect(**_kwargs()) as con:
            await con.query('drop table if exists og_async_t')
            await con.query('create temporary table og_async_t (a int)')
            await con.query('insert into og_async_t values (1),(2),(3)')
            await con.query('select a from og_async_t order by a')
            assert con.result is not None and con.result.rows == ((1,), (2,), (3,))

            await con.query('select a from og_async_t order by a', unbuffered=True)
            rows = []
            while (row := await con.fetch_unbuffered_row()) is not None:
                rows.append(row)
            assert rows == [(1,), (2,), (3,)]

    asyncio.run(main())
