"""
The whole way out: a tui's injector storing its session in a local sqlite db, and a replication worker carrying that db
to a postgres hub behind its back.

The worker is in this process but not of it. It is on a thread of its own, it has connections of its own to the sqlite
file - the harness has no idea it is there - and it knows the schema only by the mappers, as a process of its own would.
Replication is installed db-wide, so both ends are sandboxes.
"""
import threading
import typing as ta

import pytest

from omcore import check
from omcore import inject as inj
from omcore import orm
from omcore import sql
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


class WorkerThread:
    """
    A replication worker running free on a thread. Its sleeper is the way in: it paces the worker on the stop signal
    rather than the clock, so a stop is prompt, and it counts the passes, which is what lets a test wait for the worker
    to have caught up instead of guessing at how long that takes.
    """

    def __init__(self, links: list[rep.Link]) -> None:
        super().__init__()

        self._worker = rep.Worker(links, interval_s=.01, sleeper=self._sleep)

        self._cond = threading.Condition()
        self._num_passes = 0
        self._stopped = threading.Event()
        self._error: BaseException | None = None

        self._thread = threading.Thread(target=self._run, name='replication-worker', daemon=True)

    def _sleep(self, s: float) -> None:
        with self._cond:
            self._num_passes += 1
            self._cond.notify_all()

        self._stopped.wait(s)

    def _run(self) -> None:
        try:
            self._worker.run()
        except BaseException as e:  # noqa
            self._error = e
            with self._cond:
                self._cond.notify_all()

    def __enter__(self) -> ta.Self:
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._worker.stop()
        self._stopped.set()
        self._thread.join(30.)
        check.state(not self._thread.is_alive())
        check.none(self._error)

    def wait_caught_up(self, timeout_s: float = 30.) -> None:
        """
        Returns once a pass has both started and finished after this was called: a pass already underway may have read
        the source before its last write, the one after it cannot have.
        """

        with self._cond:
            n = self._num_passes + 2
            check.state(self._cond.wait_for(lambda: self._num_passes >= n or self._error is not None, timeout_s))
        check.none(self._error)
        check.state(not any(self._worker.failures(link.name) for link in self._worker.links))


##


def _read_comparable_rows(node: rep.Node, td: sql.td.TableDef) -> dict:
    """
    Column for column, but for `updated_at`. That one is each node's own: its trigger stamps a row which changes without
    it, and the edge's clock ticks in whole seconds - so a row changed twice within one keeps its `updated_at` there,
    arrives at the hub looking like it was left alone, and is given the hub's time.
    """

    return {
        k: {c: v for c, v in row.items() if c != 'updated_at'}
        for k, row in read_rows(node, td).items()
    }


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

            edge = rep.Node('edge', edge_sb.db(), rep.SqliteReplicateBackend())
            hub = rep.Node('hub', hub_sb.db(), rep.PostgresReplicateBackend())
            rep.install_node(edge, schema, no_manage_base_tables=True)
            rep.install_node(hub, schema)

            link = rep.Link(rep.LinkSpec(name='up', source='edge', target='hub'), schema, edge, hub)

            #

            with WorkerThread([link]) as worker:
                # What predates the triggers gets there by the sweep alone.
                worker.wait_caught_up()
                assert len(read_rows(hub, schema.table('session_entries'))) == 2

                # What follows them goes while the worker runs: a turn with a tool call in it, then one which fails.
                await tui.session.prompt('again')
                await tui.session.prompt('and again')

                worker.wait_caught_up()

            #

            storage = await tui.injector[har.OrmSessionStorage]
            await check_stored_transcript(storage, tui.agent)
            num_entries = len(await storage.get_entries())
            assert num_entries == 8

            # The hub has the edge's rows, as the edge's.
            for td in schema.tables:
                assert _read_comparable_rows(hub, td) == _read_comparable_rows(edge, td)
                assert {s.state.origin for s in read_shadow(hub, td).values()} == {edge.node_id}
            assert len(read_rows(hub, schema.table('session_entries'))) == num_entries
            assert read_rows(hub, schema.table('sessions'))[tui.session.id.v]['num_entries'] == num_entries

            # And the session reads back off of the hub, through the same storage, as the transcript it is.
            async with har.SqlOrm(
                registry=orm.registry(*har.orm_mappers()),
                db=sql.api.SyncToAsyncDb(sql.api.ImmediateSyncToAsyncRunner, hub_sb.db()),
                tabledef_renderer=sql.be.postgres.td.PostgresTabledefRenderer(),
            ) as hub_orm:
                await check_stored_transcript(har.OrmSessionStorage(tui.session.id, hub_orm), tui.agent)
