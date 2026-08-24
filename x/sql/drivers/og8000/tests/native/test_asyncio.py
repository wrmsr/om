import asyncio

import pytest

from ... import native
from ...exceptions import DatabaseError


def test_async_native(db_kwargs):
    async def main():
        con = await native.AsyncioConnection.connect(**db_kwargs)
        async with con:
            assert await con.run('select 1 as x') == [[1]]
            assert [c['name'] for c in con.columns] == ['x']

            assert await con.run('select :a::int + :b::int as s', a=40, b=2) == [[42]]
            assert await con.run('select :v::text', v='x', types={'v': 25}) == [['x']]

            await con.run('create temporary table t (x int)')
            await con.run('insert into t values (:x)', x=1)
            await con.run('insert into t values (:x)', x=2)
            assert con.row_count == 1
            assert await con.run('select x from t order by x') == [[1], [2]]

            ps = await con.prepare('select :x::int * 2 as d')
            assert await ps.run(x=21) == [[42]]
            assert [c['name'] for c in ps.columns] == ['d']
            await ps.close()

            with pytest.raises(DatabaseError):
                await con.run('select nope')
            assert await con.run('select 3') == [[3]]

    asyncio.run(main())


def test_async_native_notifications(db_kwargs):
    async def main():
        async with await native.AsyncioConnection.connect(**db_kwargs) as con:
            await con.run('listen chan')
            await con.run("notify chan, 'hi'")
            assert [n.payload for n in con.notifications] == ['hi']

    asyncio.run(main())
