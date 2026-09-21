"""
The whole way out: a tui's injector storing its session in a local sqlite db, and a replication worker carrying that db
to a postgres hub behind its back.

The worker is in this process but not of it. It is a task on the harness's own event loop, as it would be run for real,
but it has a db of its own for the sqlite file - its own connections, on a thread of their own, as a process of its own
would have - and the harness has no idea it is there; it knows the schema only by the mappers; and the hub it reaches
over the loop, by a driver which is really async. Replication is installed db-wide, so both ends are sandboxes.
"""
import asyncio
import contextlib
import typing as ta

import pytest

from omcore import check
from omcore import inject as inj
from omcore import orm
from omcore import sql
from omcore.asyncs.asynclite import all as asl
from omcore.sql import replicate as rep
from omcore.sql.replicate.tests.nodes import read_rows
from omcore.sql.replicate.tests.nodes import read_shadow
from omcore.sql.testing import sandboxes as sbx
from omcore.sql.tests.harness import HarnessSandboxes

from .... import harness as har
from .... import llm
from ....agent.tests.scripted import text_message
from ....agent.tests.scripted import tool_call_message
from ....agent.tests.tools import EchoTool
from ....harness.sessions.storage.orm.tests.scenarios import check_stored_transcript
from ..config import Config
from ..inject import bind_agent_tool_class
from .headless import bind_headless_tui
from .headless import bind_scripted_backend
from .headless import headless_tui


##


@contextlib.asynccontextmanager
async def running_worker(links: ta.Sequence[rep.Link]) -> ta.AsyncIterator[ta.Callable[..., ta.Awaitable[None]]]:
    """
    A replication worker running free as a task for the span of the block - paced as it would be for real, only much
    faster, as nobody is going to wait a minute on a sweep here. What is yielded waits for something to have come of it:
    each look it takes is a real wait on a db, which is when the worker - and the harness - get their turns.
    """

    worker = rep.Worker(
        links,
        events=asl.asyncio.Events(),
        tail_pacing=rep.TailPacing(min_interval_s=.01, max_interval_s=.05),
        sweep_interval_s=.02,
    )
    task = asyncio.create_task(worker.run())

    async def wait_until(fn: ta.Callable[[], ta.Awaitable[bool]], timeout_s: float = 30.) -> None:
        async with asyncio.timeout(timeout_s):
            while not await fn():
                check.state(not task.done())

    try:
        yield wait_until

    finally:
        worker.stop()
        await asyncio.wait_for(task, 30.)

    check.state(not any(worker.failures(link.name) for link in worker.links))


##


@pytest.mark.asyncs('asyncio')
async def test_sqlite_sessions_replicate_to_postgres(harness):
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as edge_sb,
        hs.postgres().allocate() as hub_sb,
    ):
        edge_db_path = check.isinstance(hs.sqlite().backend, sbx.SqliteSandboxBackend).sandbox_db_path(edge_sb.name)

        async with headless_tui(
                inj.override(
                    bind_headless_tui(Config(model='scripted', immediate=True, sql=True)),
                    bind_scripted_backend(
                        text_message('before'),
                        tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'x'})),
                        text_message('after'),
                        RuntimeError('boom'),
                    ),
                    inj.bind(har.SqliteDbConfig(file_path=edge_db_path)),
                ),

                inj.bind(EchoTool, singleton=True),
                bind_agent_tool_class(EchoTool),
        ) as tui:
            # The harness was here first: its db exists, with a turn in it, before anyone thinks to replicate it.
            await tui.session.prompt('hi')

            #

            # The replication side's own view of things: the schema by way of the mappers, the sqlite file by way of
            # connections it opens itself. The edge's tables are the harness's, so only their triggers are installed,
            # and what is in them already is backfilled; the hub's are created.
            schema = rep.ReplicationSchema(orm.sql_table_defs(orm.registry(*har.orm_mappers())))
            assert set(schema.table_names) == {'sessions', 'session_entries'}

            async with har.asyncio_sqlite_db(har.SqliteDbConfig(file_path=edge_db_path)) as edge_db:
                edge = rep.Node('edge', edge_db, rep.SqliteReplicateBackend())
                hub = rep.Node('hub', hub_sb.asyncio_db(), rep.PostgresReplicateBackend())
                await rep.install_node(edge, schema, no_manage_base_tables=True)
                await rep.install_node(hub, schema)

                link = rep.Link(rep.LinkSpec(name='up', source='edge', target='hub'), schema, edge, hub)

                #

                async def hub_has(num_entries: int) -> bool:
                    sessions = await read_rows(hub, schema.table('sessions'))
                    return (
                        len(await read_rows(hub, schema.table('session_entries'))) == num_entries and
                        sessions.get(tui.session.id.v, {}).get('num_entries') == num_entries
                    )

                async with running_worker([link]) as wait_until:
                    # What predates the triggers gets there by the sweep alone, the log knowing nothing of it.
                    await wait_until(lambda: hub_has(2))

                    # What follows them goes while the worker runs, on the same loop the turns themselves are on: one
                    # with a tool call in it, then one which fails.
                    await tui.session.prompt('again')
                    await tui.session.prompt('and again')

                    await wait_until(lambda: hub_has(8))

                #

                # The hub has the edge's rows, as the edge's - down to when it was that the edge last updated each.
                for td in schema.tables:
                    assert await read_rows(hub, td) == await read_rows(edge, td)
                    assert {s.state.origin for s in (await read_shadow(hub, td)).values()} == {await edge.node_id()}

            #

            storage = await tui.injector[har.OrmSessionStorage]
            await check_stored_transcript(storage, tui.agent)
            num_entries = len(await storage.get_entries())
            assert num_entries == 8

            # And the session reads back off of the hub, through the same storage, as the transcript it is.
            async with har.SqlOrm(
                registry=orm.registry(*har.orm_mappers()),
                db=sql.api.SyncToAsyncDb(sql.api.ImmediateSyncToAsyncRunner, hub_sb.db()),
                tabledef_renderer=sql.be.postgres.td.PostgresTabledefRenderer(),
            ) as hub_orm:
                await check_stored_transcript(har.OrmSessionStorage(tui.session.id, hub_orm), tui.agent)
