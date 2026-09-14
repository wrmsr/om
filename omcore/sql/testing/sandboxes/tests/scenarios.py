"""
The behaviors every backend must exhibit, written once against the generic interface and driven by each backend's test
module with the few backend-specific hooks below. Not a test module itself.
"""
import subprocess
import sys
import typing as ta

import pytest

from ..... import check
from ..... import dataclasses as dc
from ..... import lang
from ..... import marshal as msh
from .....formats.json import all as json
from ....api import querierfuncs as qf
from ....api.queriers import Querier
from ..backend import SandboxBackend
from ..errors import SandboxStateError
from ..names import SandboxNames
from ..names import new_run_id
from ..reaping import Reaper
from ..registry import SandboxKind
from ..registry import SandboxRecord
from ..sandboxes import SandboxAllocator


##


@dc.dataclass(frozen=True, kw_only=True)
class BackendScenario(lang.Final):
    make_backend: ta.Callable[..., SandboxBackend]  # config kwargs -> a backend against the same server / base dir

    # The name of the namespace a sandbox session finds itself in.
    namespace_of: ta.Callable[[Querier, SandboxKind], str]

    # The names of the sandbox objects (schemas, databases, directories) that currently exist.
    list_namespaces: ta.Callable[[Querier], ta.AbstractSet[str]]

    # Create / remove a sandbox object by hand, bypassing the registry.
    plant: ta.Callable[[Querier, str, SandboxKind], None]
    unplant: ta.Callable[[Querier, str, SandboxKind], None]

    orphan_backend: str
    orphan_args: ta.Sequence[str]


##


def check_isolation(sc: BackendScenario, alloc: SandboxAllocator, kind: SandboxKind | None = None) -> None:
    if kind is None:
        kind = alloc.backend.default_kind

    with alloc.allocate(kind) as a, alloc.allocate(kind) as b:
        assert a.name != b.name
        assert a.kind is b.kind is kind
        assert a.run_id == b.run_id == alloc.run_id
        assert {sb.name for sb in alloc.sandboxes} >= {a.name, b.name}

        with a.db().connect() as ca, b.db().connect() as cb:
            # each session lives in its own namespace and sees nothing else unqualified
            assert sc.namespace_of(ca, kind) == a.name
            assert sc.namespace_of(cb, kind) == b.name

            qf.exec(ca, 'create table t (v integer)')
            qf.exec(ca, 'insert into t values (1), (2)')
            qf.exec(cb, 'create table t (v text)')

            assert qf.query_scalar(ca, 'select count(*) from t') == 2
            assert qf.query_scalar(cb, 'select count(*) from t') == 0

        with alloc.backend.open_db(alloc.run_id).connect() as conn:
            # the registry knows both, leased to this run
            regs = {r.name: r for r in alloc.registry.list_run(conn, alloc.run_id)}
            assert {a.name, b.name} <= set(regs)
            assert all(r.kind is kind and r.expires_at > r.created_at for r in regs.values())

    assert a.released and b.released
    with pytest.raises(SandboxStateError):
        a.db()

    with alloc.backend.open_db(alloc.run_id).connect() as conn:
        assert not ({a.name, b.name} & sc.list_namespaces(conn))
        assert not ({a.name, b.name} & {r.name for r in alloc.registry.list_all(conn)})


def check_reaper(sc: BackendScenario, kind: SandboxKind | None = None) -> None:
    # a zero ttl means every lease is expired the moment it is taken
    backend = sc.make_backend(lease_ttl_s=0)
    if kind is None:
        kind = backend.default_kind
    names = SandboxNames(backend.config)
    registry = backend.registry
    reaper = Reaper(backend, names)

    dead = SandboxAllocator(backend, no_reap_on_open=True)
    dead.__enter__()
    leaked = dead.allocate(kind).name

    with SandboxAllocator(backend, no_reap_on_open=True) as alloc:
        db = alloc.backend.open_db(alloc.run_id)

        # expired, but its run is still alive: left alone
        rep = reaper.reap(db)
        assert leaked in rep.live
        assert leaked not in rep.reaped

        # the run dies without releasing
        dead.abandon()

        unrecognized = backend.config.prefix + 'not_a_sandbox'
        with db.connect() as conn:
            # a sandbox object that exists under the prefix with no registry row
            unregistered = names.sandbox_name(new_run_id(), 1)
            sc.plant(conn, unregistered, kind)

            # a registry row whose object never came to be (or is already gone)
            phantom = names.sandbox_name(new_run_id(), 1)
            now = backend.server_now(conn)
            registry.insert(conn, SandboxRecord(
                name=phantom,
                kind=kind,
                run_id=check.not_none(names.parse_sandbox_name(phantom)).run_id,
                owner='nobody',
                created_at=now,
                expires_at=now,
            ))

            # something under the prefix that is not a sandbox name: reported, never dropped
            sc.plant(conn, unrecognized, kind)

        try:
            rep = reaper.reap(db)
            assert not rep.skipped
            assert {leaked, unregistered, phantom} <= set(rep.reaped)
            assert unrecognized in rep.unrecognized
            assert not rep.failed

            with db.connect() as conn:
                existing = sc.list_namespaces(conn)
                assert not ({leaked, unregistered, phantom} & existing)
                assert unrecognized in existing
                assert not ({leaked, phantom} & {r.name for r in registry.list_all(conn)})

            # and a second pass finds nothing to do
            rep = reaper.reap(db)
            assert not rep.reaped and not rep.failed

        finally:
            with db.connect() as conn:
                sc.unplant(conn, unrecognized, kind)


def check_reaper_after_hard_exit(sc: BackendScenario) -> None:
    backend = sc.make_backend(lease_ttl_s=0)

    proc = subprocess.run(
        [
            sys.executable,
            '-m', __package__ + '.orphan',
            sc.orphan_backend,
            json.dumps(msh.marshal(backend.config)),
            *sc.orphan_args,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    leaked = proc.stdout.strip()
    SandboxNames(backend.config).check_sandbox_name(leaked)

    # opening an allocator reaps on entry, and the child's liveness died with it
    with SandboxAllocator(backend) as alloc:
        with alloc.backend.open_db(alloc.run_id).connect() as conn:
            assert leaked not in sc.list_namespaces(conn)
            assert leaked not in {r.name for r in alloc.registry.list_all(conn)}


def check_reaper_lock_contention(sc: BackendScenario) -> None:
    backend = sc.make_backend()
    reaper = Reaper(backend, SandboxNames(backend.config))

    with SandboxAllocator(backend, no_reap_on_open=True) as alloc:
        db = alloc.backend.open_db(alloc.run_id)
        with db.connect() as holder:
            assert backend.try_lock(holder, Reaper.LOCK_NAME)
            try:
                assert reaper.reap(db).skipped
            finally:
                backend.unlock(holder, Reaper.LOCK_NAME)
            assert not reaper.reap(db).skipped
