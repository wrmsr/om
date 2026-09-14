# ruff: noqa: S608
import contextlib
import subprocess
import sys

import pytest

from ..... import check
from ..... import marshal as msh
from .....formats.json import all as json
from ....api import querierfuncs as qf
from ....backends.postgres import connecting as pgc
from ....tests.harness import SANDBOX_ROLE_PASSWORD
from ....tests.harness import HarnessSandboxes
from ..config import SandboxesConfig
from ..errors import SandboxSafetyError
from ..errors import SandboxStateError
from ..names import SandboxNames
from ..names import new_run_id
from ..postgres import PostgresSandboxBackend
from ..postgres import bootstrap_postgres
from ..reaping import Reaper
from ..registry import SandboxKind
from ..registry import SandboxRecord
from ..registry import SandboxRegistry
from ..sandboxes import SandboxAllocator


##


def _backend(harness, **kwargs) -> PostgresSandboxBackend:
    hs = harness[HarnessSandboxes]
    hs.postgres()  # ensure bootstrapped
    return PostgresSandboxBackend(SandboxesConfig(**kwargs), hs.postgres_loc())


##


def test_isolation(harness) -> None:
    alloc = harness[HarnessSandboxes].postgres()

    with alloc.allocate() as a, alloc.allocate() as b:
        assert a.name != b.name
        assert a.run_id == b.run_id == alloc.run_id
        assert {sb.name for sb in alloc.sandboxes} >= {a.name, b.name}

        with a.db().connect() as ca, b.db().connect() as cb:
            # each session lives in its own schema and sees nothing else unqualified
            assert qf.query_scalar(ca, 'select current_schema()') == a.name
            assert qf.query_scalar(cb, 'select current_schema()') == b.name

            qf.exec(ca, 'create table t (v integer)')
            qf.exec(ca, 'insert into t values (1), (2)')
            qf.exec(cb, 'create table t (v text)')

            assert qf.query_scalar(ca, 'select count(*) from t') == 2
            assert qf.query_scalar(cb, 'select count(*) from t') == 0

            # the registry knows both, leased to this run
            regs = {r.name: r for r in alloc.registry.list_run(ca, alloc.run_id)}
            assert {a.name, b.name} <= set(regs)
            assert all(r.kind is SandboxKind.SCHEMA and r.expires_at > r.created_at for r in regs.values())

    assert a.released and b.released
    with pytest.raises(SandboxStateError):
        a.db()

    with alloc.backend.open_db(alloc.run_id).connect() as conn:
        schemas = {r.values[0] for r in qf.query_all(conn, 'select nspname from pg_namespace')}
        assert not ({a.name, b.name} & schemas)
        assert not ({a.name, b.name} & {r.name for r in alloc.registry.list_all(conn)})


def test_guard_refuses_superuser(harness) -> None:
    hs = harness[HarnessSandboxes]
    admin_loc, _ = hs.postgres_admin()

    backend = PostgresSandboxBackend(hs.postgres_config(), admin_loc)
    with pytest.raises(SandboxSafetyError):
        with SandboxAllocator(backend):
            pass


def test_reaper(harness) -> None:
    # a zero ttl means every lease is expired the moment it is taken
    backend = _backend(harness, lease_ttl_s=0)
    names = SandboxNames(backend.config)
    registry = SandboxRegistry(backend.config)
    reaper = Reaper(backend, registry, names)

    dead = SandboxAllocator(backend, no_reap_on_open=True)
    dead.__enter__()
    leaked = dead.allocate().name

    with SandboxAllocator(backend, no_reap_on_open=True) as alloc:
        db = check.not_none(alloc.backend.open_db(alloc.run_id))

        # expired, but its run still holds a session: left alone
        rep = reaper.reap(db)
        assert leaked in rep.live
        assert leaked not in rep.reaped

        # the run dies without releasing (its session closes, nothing else happens)
        dead.abandon()

        with db.connect() as conn:
            # a schema that exists under the prefix with no registry row
            unregistered = names.sandbox_name(new_run_id(), 1)
            qf.exec(conn, f'create schema "{unregistered}"')

            # a registry row whose schema never came to be (or is already gone)
            phantom = names.sandbox_name(new_run_id(), 1)
            now = backend.server_now(conn)
            registry.insert(conn, SandboxRecord(
                name=phantom,
                kind=SandboxKind.SCHEMA,
                run_id=names.parse_sandbox_name(phantom).run_id,  # type: ignore[union-attr]
                owner='nobody',
                created_at=now,
                expires_at=now,
            ))

            # something under the prefix that is not a sandbox name: reported, never dropped
            qf.exec(conn, 'create schema if not exists "_osbx_not_a_sandbox"')

        try:
            rep = reaper.reap(db)
            assert not rep.skipped
            assert {leaked, unregistered, phantom} <= set(rep.reaped)
            assert '_osbx_not_a_sandbox' in rep.unrecognized
            assert not rep.failed

            with db.connect() as conn:
                schemas = {r.values[0] for r in qf.query_all(conn, 'select nspname from pg_namespace')}
                assert not ({leaked, unregistered, phantom} & schemas)
                assert '_osbx_not_a_sandbox' in schemas
                assert not ({leaked, phantom} & {r.name for r in registry.list_all(conn)})

            # and a second pass finds nothing to do
            rep = reaper.reap(db)
            assert not rep.reaped and not rep.failed

        finally:
            with db.connect() as conn:
                qf.exec(conn, 'drop schema if exists "_osbx_not_a_sandbox" cascade')


def test_reaper_after_hard_exit(harness) -> None:
    backend = _backend(harness, lease_ttl_s=0)
    hs = harness[HarnessSandboxes]
    loc = hs.postgres_loc()

    proc = subprocess.run(
        [
            sys.executable,
            '-m', __package__ + '.orphan',
            json.dumps(msh.marshal(backend.config)),
            loc.host,
            str(loc.port),
            SANDBOX_ROLE_PASSWORD,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    leaked = proc.stdout.strip()
    SandboxNames(backend.config).check_sandbox_name(leaked)

    # opening an allocator reaps on entry, and the child's sessions died with it
    with SandboxAllocator(backend) as alloc:
        with alloc.backend.open_db(alloc.run_id).connect() as conn:
            schemas = {r.values[0] for r in qf.query_all(conn, 'select nspname from pg_namespace')}
            assert leaked not in schemas
            assert leaked not in {r.name for r in alloc.registry.list_all(conn)}


def test_reaper_lock_contention(harness) -> None:
    backend = _backend(harness)
    reaper = Reaper(backend, SandboxRegistry(backend.config), SandboxNames(backend.config))

    with SandboxAllocator(backend, no_reap_on_open=True) as alloc:
        db = alloc.backend.open_db(alloc.run_id)
        with db.connect() as holder:
            assert backend.try_lock(holder, Reaper.LOCK_NAME)
            try:
                assert reaper.reap(db).skipped
            finally:
                backend.unlock(holder, Reaper.LOCK_NAME)
            assert not reaper.reap(db).skipped


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
