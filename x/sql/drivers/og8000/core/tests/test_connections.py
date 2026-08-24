"""Live tests of the sync and async core connections. These need the server described by tests/dbs.py."""
import asyncio
import io

import pytest

from ...exceptions import DatabaseError
from ...exceptions import InterfaceError
from ...tests.dbs import DB_KWARGS
from ..asyncio import AsyncioCoreConnection
from ..sync import SyncCoreConnection


def sync_connect(**kwargs):
    return SyncCoreConnection(**{**DB_KWARGS, **kwargs})


async def async_connect(**kwargs):
    return await AsyncioCoreConnection.connect(**{**DB_KWARGS, **kwargs})


##
# Sync


def test_sync_queries(db_setup):
    with sync_connect() as con:
        assert con.is_ssl
        assert con.session.sasl_mechanism == 'SCRAM-SHA-256-PLUS'

        assert con.execute_simple('select 1 as x').rows == [[1]]
        assert con.execute_unnamed('select $1::int + $2::int', (40, 2)).rows == [[42]]

        info = con.prepare_statement('select $1::text || $2::text')
        assert con.execute_named(info.name, ('a', 'b'), info.columns, info.input_funcs, 'x').rows == [['ab']]
        con.close_prepared_statement(info.name)

        ctx = con.execute_simple('create temporary table t (x int); insert into t values (1), (2); select * from t')
        assert ctx.rows == [[1], [2]]
        assert [c['name'] for c in ctx.columns] == ['x']

    assert con.is_closed
    with pytest.raises(InterfaceError, match='closed'):
        con.execute_simple('select 1')
    with pytest.raises(InterfaceError, match='closed'):
        con.close()


def test_sync_no_ssl(db_setup):
    with sync_connect(ssl_context=False) as con:
        assert not con.is_ssl
        assert con.session.sasl_mechanism == 'SCRAM-SHA-256'
        assert con.execute_simple('select 2').rows == [[2]]


def test_sync_errors_leave_connection_usable(db_setup):
    with sync_connect() as con:
        with pytest.raises(DatabaseError) as ei:
            con.execute_simple('select nope')
        assert ei.value.args[0]['C'] == '42703'
        assert con.execute_simple('select 3').rows == [[3]]


def test_sync_copy_round_trip(db_setup):
    with sync_connect() as con:
        con.execute_simple('create temporary table t (a int, b text)')
        con.execute_unnamed('copy t from stdin', stream=io.BytesIO(b'1\tx\n2\ty\n'))
        out = io.StringIO()
        con.execute_unnamed('copy t to stdout', stream=out)
        assert out.getvalue() == '1\tx\n2\ty\n'


def test_sync_bad_password(db_setup):
    with pytest.raises(DatabaseError) as ei:
        sync_connect(password='wrong')  # noqa: S106
    assert ei.value.args[0]['C'] == '28P01'


##
# Async


def test_async_queries(db_setup):
    async def main():
        async with await async_connect() as con:
            assert con.is_ssl
            assert con.session.sasl_mechanism == 'SCRAM-SHA-256-PLUS'

            assert (await con.execute_simple('select 1 as x')).rows == [[1]]
            assert (await con.execute_unnamed('select $1::int + $2::int', (40, 2))).rows == [[42]]

            info = await con.prepare_statement('select $1::text || $2::text')
            ctx = await con.execute_named(info.name, ('a', 'b'), info.columns, info.input_funcs, 'x')
            assert ctx.rows == [['ab']]
            await con.close_prepared_statement(info.name)

            with pytest.raises(DatabaseError):
                await con.execute_simple('select nope')
            assert (await con.execute_simple('select 3')).rows == [[3]]

        assert con.is_closed
        with pytest.raises(InterfaceError, match='closed'):
            await con.execute_simple('select 1')

    asyncio.run(main())


def test_async_no_ssl(db_setup):
    async def main():
        async with await async_connect(ssl_context=False) as con:
            assert not con.is_ssl
            assert con.session.sasl_mechanism == 'SCRAM-SHA-256'
            assert (await con.execute_simple('select 2')).rows == [[2]]

    asyncio.run(main())


def test_async_copy_round_trip(db_setup):
    async def main():
        async with await async_connect() as con:
            await con.execute_simple('create temporary table t (a int, b text)')
            await con.execute_unnamed('copy t from stdin', stream=io.BytesIO(b'1\tx\n2\ty\n'))
            out = io.StringIO()
            await con.execute_unnamed('copy t to stdout', stream=out)
            assert out.getvalue() == '1\tx\n2\ty\n'

    asyncio.run(main())


def test_async_bad_password(db_setup):
    async def main():
        with pytest.raises(DatabaseError) as ei:
            await async_connect(password='wrong')  # noqa: S106
        assert ei.value.args[0]['C'] == '28P01'

    asyncio.run(main())
