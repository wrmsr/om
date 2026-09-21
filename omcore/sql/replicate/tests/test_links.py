import contextlib
import threading

from .... import lang
from ....asyncs.asynclite import all as asl
from ...tests.harness import HarnessSandboxes
from ..backends.mysql import MysqlReplicateBackend
from ..backends.postgres import PostgresReplicateBackend
from ..backends.sqlite import SqliteReplicateBackend
from ..config import LinkSpec
from ..install import install_node
from ..links import Link
from ..nodes import Node
from ..workers import TailPacing
from ..workers import Worker
from .models import build_schema
from .nodes import FailingDb
from .nodes import insert_row
from .nodes import mysql_node
from .nodes import postgres_node
from .nodes import read_rows
from .nodes import sandbox_async_db
from .nodes import sqlite_node
from .scenarios import _business
from .scenarios import check_chunked_apply
from .scenarios import check_fanout
from .scenarios import check_fault_between_apply_and_cursor
from .scenarios import check_log_tail
from .scenarios import check_no_log
from .scenarios import check_roundtrip
from .scenarios import check_step_costs
from .scenarios import check_worker
from .scenarios import check_worker_maintenance
from .scenarios import check_worker_pacing


def test_sqlite_to_postgres(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        lang.sync_await(check_roundtrip(
            sqlite_node('edge', e),
            postgres_node('hub', h),
            build_schema(),
        ))


def test_postgres_to_sqlite(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.postgres().allocate() as e,
        hs.sqlite().allocate() as h,
    ):
        lang.sync_await(check_roundtrip(
            postgres_node('edge', e),
            sqlite_node('hub', h),
            build_schema(),
        ))


def test_sqlite_to_mysql(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.mysql().allocate() as h,
    ):
        lang.sync_await(check_roundtrip(
            sqlite_node('edge', e),
            mysql_node('hub', h),
            build_schema(),
        ))


def test_mysql_to_postgres(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.mysql().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        lang.sync_await(check_roundtrip(
            mysql_node('edge', e),
            postgres_node('hub', h),
            build_schema(),
        ))


def test_fault_between_apply_and_cursor(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        lang.sync_await(check_fault_between_apply_and_cursor(
            sqlite_node('edge', e),
            postgres_node('hub', h, FailingDb(sandbox_async_db(h))),
            build_schema(),
        ))


def test_step_costs(harness) -> None:
    hs = harness[HarnessSandboxes]
    with hs.sqlite().allocate() as e, hs.postgres().allocate() as h:
        lang.sync_await(check_step_costs(
            sqlite_node('edge', e, FailingDb(sandbox_async_db(e))),
            postgres_node('hub', h, FailingDb(sandbox_async_db(h))),
            build_schema(),
        ))


def test_chunked_apply(harness) -> None:
    hs = harness[HarnessSandboxes]
    with contextlib.ExitStack() as es:
        for i, (alloc, backend_cls) in enumerate([
            (hs.postgres(), PostgresReplicateBackend),
            (hs.sqlite(), SqliteReplicateBackend),
            (hs.mysql(), MysqlReplicateBackend),
        ]):
            e = es.enter_context(hs.sqlite().allocate())
            h = es.enter_context(alloc.allocate())
            lang.sync_await(check_chunked_apply(
                sqlite_node(f'edge{i}', e),
                Node(f'hub{i}', FailingDb(sandbox_async_db(h)), backend_cls(max_statement_params=10)),
                build_schema(),
                max_statement_params=10,
            ))


def test_fanout(harness) -> None:
    hs = harness[HarnessSandboxes]
    with contextlib.ExitStack() as es:
        h = es.enter_context(hs.postgres().allocate())
        n = es.enter_context(hs.sqlite().allocate())
        m = es.enter_context(hs.sqlite().allocate())
        lang.sync_await(check_fanout(
            postgres_node('hub', h),
            sqlite_node('n', n),
            sqlite_node('m', m),
            build_schema(),
        ))


def test_worker(harness) -> None:
    hs = harness[HarnessSandboxes]
    with contextlib.ExitStack() as es:
        e = es.enter_context(hs.sqlite().allocate())
        h = es.enter_context(hs.postgres().allocate())
        b = es.enter_context(hs.postgres().allocate())
        lang.sync_await(check_worker(
            sqlite_node('edge', e),
            postgres_node('hub', h),
            postgres_node('broken', b, FailingDb(sandbox_async_db(b))),
            build_schema(),
        ))


def test_log_tail_sqlite_to_postgres(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        lang.sync_await(check_log_tail(
            sqlite_node('edge', e),
            postgres_node('hub', h),
            build_schema(),
        ))


def test_log_tail_postgres_to_sqlite(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.postgres().allocate() as e,
        hs.sqlite().allocate() as h,
    ):
        lang.sync_await(check_log_tail(
            postgres_node('edge', e),
            sqlite_node('hub', h),
            build_schema(),
        ))


def test_log_tail_mysql_to_sqlite(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.mysql().allocate() as e,
        hs.sqlite().allocate() as h,
    ):
        lang.sync_await(check_log_tail(
            mysql_node('edge', e),
            sqlite_node('hub', h),
            build_schema(),
        ))


def test_no_log(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        lang.sync_await(check_no_log(
            sqlite_node('edge', e, no_log=True),
            postgres_node('hub', h),
            build_schema(),
        ))


def test_worker_in_a_thread(harness) -> None:
    """
    The worker with no event loop to be had: its dbs the sync kind, its stop event a thread's, and `run` a call which
    does not return until another thread says so.
    """

    hs = harness[HarnessSandboxes]
    with hs.sqlite().allocate() as e, hs.postgres().allocate() as h:
        schema = build_schema()
        biz = schema.table('businesses')
        edge, hub = sqlite_node('edge', e), postgres_node('hub', h)
        for n in (edge, hub):
            lang.sync_await(install_node(n, schema))

        # A pass is over when the worker goes to sleep, which is its to say: so that is what is waited on.
        passed = threading.Condition()
        num_passes = [0]
        stopped = threading.Event()

        async def sleeper(s: float) -> None:
            with passed:
                num_passes[0] += 1
                passed.notify_all()
            stopped.wait(s)

        worker = Worker(
            [Link(LinkSpec(name='up', source='edge', target='hub'), schema, edge, hub)],
            events=asl.sync.Events(),
            tail_pacing=TailPacing(min_interval_s=.01, max_interval_s=.05),
            sweep_interval_s=.02,
            sleeper=sleeper,
        )
        thread = threading.Thread(target=lambda: lang.sync_await(worker.run()), daemon=True)
        thread.start()

        try:
            rows = [_business(f'h{i}') for i in range(20)]
            for r in rows:
                lang.sync_await(insert_row(edge, biz, r))

            def caught_up() -> bool:
                return lang.sync_await(read_rows(hub, biz)) == {r['id']: r for r in rows}

            with passed:
                assert passed.wait_for(caught_up, 30.)

        finally:
            worker.stop()
            stopped.set()
            thread.join(30.)

        assert not thread.is_alive()
        assert not any(worker.failures(link.name) for link in worker.links)


def test_worker_pacing(harness) -> None:
    hs = harness[HarnessSandboxes]
    with hs.sqlite().allocate() as e, hs.postgres().allocate() as h:
        lang.sync_await(check_worker_pacing(
            sqlite_node('edge', e, FailingDb(sandbox_async_db(e))),
            postgres_node('hub', h, FailingDb(sandbox_async_db(h))),
            build_schema(),
        ))


def test_worker_maintenance(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        lang.sync_await(check_worker_maintenance(
            sqlite_node('edge', e),
            postgres_node('hub', h),
            build_schema(),
        ))
