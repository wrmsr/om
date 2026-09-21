import contextlib

from ...tests.harness import HarnessSandboxes
from .models import build_schema
from .nodes import FailingDb
from .nodes import mysql_node
from .nodes import postgres_node
from .nodes import sqlite_node
from .scenarios import check_fanout
from .scenarios import check_fault_between_apply_and_cursor
from .scenarios import check_log_tail
from .scenarios import check_no_log
from .scenarios import check_roundtrip
from .scenarios import check_worker
from .scenarios import check_worker_maintenance


def test_sqlite_to_postgres(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        check_roundtrip(
            sqlite_node('edge', e),
            postgres_node('hub', h),
            build_schema(),
        )


def test_postgres_to_sqlite(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.postgres().allocate() as e,
        hs.sqlite().allocate() as h,
    ):
        check_roundtrip(
            postgres_node('edge', e),
            sqlite_node('hub', h),
            build_schema(),
        )


def test_sqlite_to_mysql(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.mysql().allocate() as h,
    ):
        check_roundtrip(
            sqlite_node('edge', e),
            mysql_node('hub', h),
            build_schema(),
        )


def test_mysql_to_postgres(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.mysql().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        check_roundtrip(
            mysql_node('edge', e),
            postgres_node('hub', h),
            build_schema(),
        )


def test_fault_between_apply_and_cursor(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        check_fault_between_apply_and_cursor(
            sqlite_node('edge', e),
            postgres_node('hub', h, FailingDb(h.db())),
            build_schema(),
        )


def test_fanout(harness) -> None:
    hs = harness[HarnessSandboxes]
    with contextlib.ExitStack() as es:
        h = es.enter_context(hs.postgres().allocate())
        n = es.enter_context(hs.sqlite().allocate())
        m = es.enter_context(hs.sqlite().allocate())
        check_fanout(
            postgres_node('hub', h),
            sqlite_node('n', n),
            sqlite_node('m', m),
            build_schema(),
        )


def test_worker(harness) -> None:
    hs = harness[HarnessSandboxes]
    with contextlib.ExitStack() as es:
        e = es.enter_context(hs.sqlite().allocate())
        h = es.enter_context(hs.postgres().allocate())
        b = es.enter_context(hs.postgres().allocate())
        check_worker(
            sqlite_node('edge', e),
            postgres_node('hub', h),
            postgres_node('broken', b, FailingDb(b.db())),
            build_schema(),
        )


def test_log_tail_sqlite_to_postgres(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        check_log_tail(
            sqlite_node('edge', e),
            postgres_node('hub', h),
            build_schema(),
        )


def test_log_tail_postgres_to_sqlite(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.postgres().allocate() as e,
        hs.sqlite().allocate() as h,
    ):
        check_log_tail(
            postgres_node('edge', e),
            sqlite_node('hub', h),
            build_schema(),
        )


def test_log_tail_mysql_to_sqlite(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.mysql().allocate() as e,
        hs.sqlite().allocate() as h,
    ):
        check_log_tail(
            mysql_node('edge', e),
            sqlite_node('hub', h),
            build_schema(),
        )


def test_no_log(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        check_no_log(
            sqlite_node('edge', e, no_log=True),
            postgres_node('hub', h),
            build_schema(),
        )


def test_worker_maintenance(harness) -> None:
    hs = harness[HarnessSandboxes]
    with (
        hs.sqlite().allocate() as e,
        hs.postgres().allocate() as h,
    ):
        check_worker_maintenance(
            sqlite_node('edge', e),
            postgres_node('hub', h),
            build_schema(),
        )
