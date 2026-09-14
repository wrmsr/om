# ruff: noqa: S608
import contextlib

import pytest

from ....api import querierfuncs as qf
from ....backends.mysql import connecting as myc
from ....tests.harness import SANDBOX_ROLE_PASSWORD
from ....tests.harness import HarnessSandboxes
from ..config import SandboxesConfig
from ..errors import SandboxSafetyError
from ..mysql import MysqlSandboxBackend
from ..mysql import bootstrap_mysql
from ..mysql import grant_pattern
from ..sandboxes import SandboxAllocator
from .scenarios import BackendScenario
from .scenarios import check_isolation
from .scenarios import check_reaper
from .scenarios import check_reaper_after_hard_exit
from .scenarios import check_reaper_lock_contention


##


def _scenario(harness) -> BackendScenario:
    hs = harness[HarnessSandboxes]
    hs.mysql()  # ensure bootstrapped
    loc = hs.mysql_loc()

    return BackendScenario(
        make_backend=lambda **kw: MysqlSandboxBackend(SandboxesConfig(**kw), loc),
        namespace_of=lambda q, kind: qf.query_scalar(q, 'select database()'),
        list_namespaces=lambda q: {
            r.values[0] for r in qf.query_all(q, 'select schema_name from information_schema.schemata')
        },
        plant=lambda q, name, kind: qf.exec(q, f'create database `{name}`'),
        unplant=lambda q, name, kind: qf.exec(q, f'drop database if exists `{name}`'),
        orphan_backend='mysql',
        orphan_args=[loc.host, str(loc.port), SANDBOX_ROLE_PASSWORD],
    )


##


def test_isolation(harness) -> None:
    check_isolation(_scenario(harness), harness[HarnessSandboxes].mysql())


def test_reaper(harness) -> None:
    check_reaper(_scenario(harness))


def test_reaper_after_hard_exit(harness) -> None:
    check_reaper_after_hard_exit(_scenario(harness))


def test_reaper_lock_contention(harness) -> None:
    check_reaper_lock_contention(_scenario(harness))


def test_guard_refuses_admin(harness) -> None:
    hs = harness[HarnessSandboxes]

    backend = MysqlSandboxBackend(hs.mysql_config(), hs.mysql_admin())
    with pytest.raises(SandboxSafetyError):
        with SandboxAllocator(backend):
            pass


def test_grant_pattern() -> None:
    assert grant_pattern('_osbx_') == '\\_osbx\\_%'


def test_bootstrap_idempotent(harness) -> None:
    hs = harness[HarnessSandboxes]
    admin_loc = hs.mysql_admin()
    cfg = SandboxesConfig(database='_osbx__db_bootstrap_test', role='_osbx__role_bootstrap_test')

    with myc.omysql_db(admin_loc).connect() as admin:
        with contextlib.ExitStack() as es:
            es.callback(lambda: qf.exec(admin, f"drop user if exists '{cfg.role}'@'%'"))
            es.callback(lambda: qf.exec(admin, f'drop database if exists `{cfg.database}`'))

            r1 = bootstrap_mysql(admin, cfg, role_password='pw1')  # noqa: S106
            assert r1.created_user and r1.created_database

            r2 = bootstrap_mysql(admin, cfg, role_password='pw2')  # noqa: S106
            assert not r2.created_user and not r2.created_database

            with myc.omysql_db(
                    myc.with_username(admin_loc, cfg.role, 'pw2'),
                    database=cfg.database,
            ).connect() as conn:
                MysqlSandboxBackend(cfg, admin_loc).guard(conn)
                assert qf.query_scalar(conn, 'select database()') == cfg.database

                # the server enforces the prefix: nothing outside it is even visible, let alone creatable
                visible = {r.values[0] for r in qf.query_all(conn, 'select schema_name from information_schema.schemata')}  # noqa
                assert 'mysql' not in visible
                with pytest.raises(Exception):  # noqa
                    qf.exec(conn, 'create database `not_ours`')
