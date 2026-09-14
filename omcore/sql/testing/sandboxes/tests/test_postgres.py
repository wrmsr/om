# ruff: noqa: S608
import contextlib

import pytest

from ..... import check
from ....api import querierfuncs as qf
from ....backends.postgres import connecting as pgc
from ....tests.harness import SANDBOX_ROLE_PASSWORD
from ....tests.harness import HarnessSandboxes
from ..backends.postgres import PostgresSandboxBackend
from ..backends.postgres import bootstrap_postgres
from ..config import SandboxesConfig
from ..errors import SandboxSafetyError
from ..registry import SandboxKind
from ..sandboxes import SandboxAllocator
from .scenarios import BackendScenario
from .scenarios import check_isolation
from .scenarios import check_reaper
from .scenarios import check_reaper_after_hard_exit
from .scenarios import check_reaper_lock_contention


##


def _scenario(harness) -> BackendScenario:
    hs = harness[HarnessSandboxes]
    hs.postgres()  # ensure bootstrapped
    loc = hs.postgres_loc()
    base_cfg = hs.postgres_config()

    def plant(q, name, kind):
        if kind is SandboxKind.SCHEMA:
            qf.exec(q, f'create schema "{name}"')
        else:
            qf.exec(q, f'create database "{name}"')

    def unplant(q, name, kind):
        if kind is SandboxKind.SCHEMA:
            qf.exec(q, f'drop schema if exists "{name}" cascade')
        else:
            qf.exec(q, f'drop database if exists "{name}" with (force)')

    return BackendScenario(
        make_backend=lambda **kw: PostgresSandboxBackend(
            SandboxesConfig(database_sandboxes=base_cfg.database_sandboxes, **kw),
            loc,
        ),
        namespace_of=lambda q, kind: qf.query_scalar(
            q,
            'select current_schema()' if kind is SandboxKind.SCHEMA else 'select current_database()',
        ),
        list_namespaces=lambda q: {
            *(r.values[0] for r in qf.query_all(q, 'select nspname from pg_namespace')),
            *(r.values[0] for r in qf.query_all(q, 'select datname from pg_database')),
        },
        plant=plant,
        unplant=unplant,
        orphan_backend='postgres',
        orphan_args=[loc.host, str(loc.port), SANDBOX_ROLE_PASSWORD],
    )


##


def test_isolation(harness) -> None:
    check_isolation(_scenario(harness), harness[HarnessSandboxes].postgres())


def test_reaper(harness) -> None:
    check_reaper(_scenario(harness))


def test_reaper_after_hard_exit(harness) -> None:
    check_reaper_after_hard_exit(_scenario(harness))


def test_reaper_lock_contention(harness) -> None:
    check_reaper_lock_contention(_scenario(harness))


def test_database_kind(harness) -> None:
    sc = _scenario(harness)
    alloc = harness[HarnessSandboxes].postgres()
    if SandboxKind.DATABASE not in alloc.backend.supported_kinds:
        pytest.skip('database sandboxes not enabled on this server')

    check_isolation(sc, alloc, SandboxKind.DATABASE)
    check_reaper(sc, SandboxKind.DATABASE)

    # the two kinds coexist under one run
    with alloc.allocate(SandboxKind.SCHEMA) as s, alloc.allocate(SandboxKind.DATABASE) as d:
        with s.db().connect() as cs, d.db().connect() as cd:
            assert qf.query_scalar(cs, 'select current_database()') == alloc.config.database
            assert qf.query_scalar(cd, 'select current_database()') == d.name


def test_guard_refuses_superuser(harness) -> None:
    hs = harness[HarnessSandboxes]
    admin_loc, _ = hs.postgres_admin()

    backend = PostgresSandboxBackend(hs.postgres_config(), admin_loc)
    with pytest.raises(SandboxSafetyError):
        with SandboxAllocator(backend):
            pass


def test_bootstrap_idempotent(harness) -> None:
    hs = harness[HarnessSandboxes]
    admin_loc, admin_database = hs.postgres_admin()
    cfg = SandboxesConfig(database='_osbx__db_bootstrap_test', role='_osbx__role_bootstrap_test')

    with pgc.og8000_db(admin_loc, database=admin_database).connect() as admin:
        with contextlib.ExitStack() as es:
            # last-in-first-out: the database must go before the role that owns it
            es.callback(lambda: qf.exec(admin, f'drop role if exists "{cfg.role}"'))
            es.callback(lambda: qf.exec(admin, f'drop database if exists "{cfg.database}"'))

            r1 = bootstrap_postgres(admin, cfg, role_password='pw1')  # noqa: S106
            assert r1.created_role and r1.created_database

            # the second run changes nothing but re-asserts the password
            r2 = bootstrap_postgres(admin, cfg, role_password='pw2')  # noqa: S106
            assert not r2.created_role and not r2.created_database

            with pgc.og8000_db(
                    pgc.with_username(admin_loc, cfg.role, 'pw2'),
                    database=cfg.database,
            ).connect() as conn:
                PostgresSandboxBackend(cfg, admin_loc).guard(conn)
                assert qf.query_scalar(conn, 'select current_database()') == cfg.database
                assert check.isinstance(qf.query_scalar(conn, (
                    'select rolcreatedb from pg_roles where rolname = current_user'
                )), bool) is False
