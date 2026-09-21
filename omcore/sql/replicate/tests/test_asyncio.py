"""
The same scenarios under a real event loop, over dbs which are really async: postgres and mysql by way of their asyncio
drivers, sqlite - there being no such thing for it - by way of the sync one run off the loop. Everywhere else they are
driven with no loop at all, over sync dbs behind the same interfaces; nothing in between knows the difference.
"""
import asyncio

import pytest

from ....asyncs.asynclite import all as asl
from ...tests.harness import HarnessSandboxes
from ..backends.mysql import MysqlReplicateBackend
from ..backends.postgres import PostgresReplicateBackend
from ..backends.sqlite import SqliteReplicateBackend
from ..install import install_node
from ..nodes import Node
from ..workers import TailPacing
from ..workers import Worker
from .models import build_schema
from .nodes import insert_row
from .nodes import read_rows
from .scenarios import _business
from .scenarios import _link
from .scenarios import check_log_tail
from .scenarios import check_roundtrip


##


@pytest.mark.asyncs('asyncio')
async def test_sqlite_to_postgres(harness) -> None:
    hs = harness[HarnessSandboxes]
    with hs.sqlite().allocate() as e, hs.postgres().allocate() as h:
        await check_roundtrip(
            Node('edge', e.asyncio_db(), SqliteReplicateBackend()),
            Node('hub', h.asyncio_db(), PostgresReplicateBackend()),
            build_schema(),
        )


@pytest.mark.asyncs('asyncio')
async def test_mysql_to_postgres(harness) -> None:
    hs = harness[HarnessSandboxes]
    with hs.mysql().allocate() as e, hs.postgres().allocate() as h:
        await check_roundtrip(
            Node('edge', e.asyncio_db(), MysqlReplicateBackend()),
            Node('hub', h.asyncio_db(), PostgresReplicateBackend()),
            build_schema(),
        )


@pytest.mark.asyncs('asyncio')
async def test_log_tail_postgres_to_mysql(harness) -> None:
    hs = harness[HarnessSandboxes]
    with hs.postgres().allocate() as e, hs.mysql().allocate() as h:
        await check_log_tail(
            Node('edge', e.asyncio_db(), PostgresReplicateBackend()),
            Node('hub', h.asyncio_db(), MysqlReplicateBackend()),
            build_schema(),
        )


@pytest.mark.asyncs('asyncio')
async def test_worker_as_a_task(harness) -> None:
    """
    The worker as it is meant to be run under a loop: a task among others, asleep on the loop's own kind of event
    between passes, and stopped by it.
    """

    hs = harness[HarnessSandboxes]
    with hs.sqlite().allocate() as e, hs.postgres().allocate() as h:
        schema = build_schema()
        biz = schema.table('businesses')
        edge = Node('edge', e.asyncio_db(), SqliteReplicateBackend())
        hub = Node('hub', h.asyncio_db(), PostgresReplicateBackend())
        for n in (edge, hub):
            await install_node(n, schema)

        worker = Worker(
            [_link('up', schema, edge, hub)],
            events=asl.asyncio.Events(),
            tail_pacing=TailPacing(min_interval_s=.01, max_interval_s=.05),
            sweep_interval_s=.02,
        )
        task = asyncio.create_task(worker.run())

        try:
            # The loop is everyone's: rows go in here while the worker is off between passes, or amid one.
            rows = [_business(f'a{i}') for i in range(20)]
            for r in rows:
                await insert_row(edge, biz, r)

            # Each look at the hub is a real wait on it, which is when the worker gets its turns.
            async with asyncio.timeout(30.):
                while await read_rows(hub, biz) != {r['id']: r for r in rows}:
                    assert not task.done(), task.exception()

        finally:
            worker.stop()
            await asyncio.wait_for(task, 30.)

        assert not any(worker.failures(link.name) for link in worker.links)
