# ruff: noqa: S608
import datetime
import hashlib
import struct
import typing as ta

from .... import check
from ....secrets.secrets import Secrets
from ...api import querierfuncs as qf
from ...api.core import Db
from ...api.queriers import Querier
from ...backends.postgres.connecting import og8000_db
from ...backends.postgres.tabledefs import PostgresTabledefRenderer
from ...dbs import HostDbLoc
from ...queries import Q
from ...tabledefs.rendering import Renderer
from .backends import SandboxBackend
from .config import SandboxesConfig
from .errors import SandboxSafetyError
from .names import SandboxNames
from .registry import SandboxRegistry


##


def _lit(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def advisory_lock_key(s: str) -> int:
    # The first 8 bytes of sha1, as a signed 64-bit int - reproducible from sql too via pgcrypto's digest().
    return struct.unpack('>q', hashlib.sha1(s.encode('utf-8')).digest()[:8])[0]  # noqa


class PostgresSandboxBackend(SandboxBackend):
    """A sandbox is a schema in the dedicated sandbox database, entered through the session's search path."""

    def __init__(
            self,
            cfg: SandboxesConfig,
            loc: HostDbLoc,
            *,
            secrets: Secrets | None = None,
    ) -> None:
        super().__init__()

        self._cfg = cfg
        self._loc = loc
        self._secrets = secrets

        self._names = SandboxNames(cfg)
        self._renderer = PostgresTabledefRenderer()

    @property
    def config(self) -> SandboxesConfig:
        return self._cfg

    def _quote(self, s: str) -> str:
        return self._renderer.quote_ident(s)

    #

    def open_db(self, run_id: str) -> Db:
        return og8000_db(
            self._loc,
            database=self._cfg.database,
            application_name=self._names.application_name(run_id),
            secrets=self._secrets,
        )

    def sandbox_db(self, run_id: str, name: str) -> Db:
        self._names.check_sandbox_name(name)
        return og8000_db(
            self._loc,
            database=self._cfg.database,
            application_name=self._names.application_name(run_id),
            startup_params={'search_path': self._quote(name)},
            secrets=self._secrets,
        )

    #

    def guard(self, q: Querier) -> None:
        d = qf.query_one(q, (
            'select current_user as role, current_database() as database, r.rolsuper as superuser '
            'from pg_roles r where r.rolname = current_user'
        )).to_dict()

        if d['superuser']:
            raise SandboxSafetyError(f'refusing to run as superuser {d["role"]!r}')
        if d['role'] != self._cfg.role:
            raise SandboxSafetyError(f'connected as {d["role"]!r}, not the sandbox role {self._cfg.role!r}')
        if d['database'] != self._cfg.database:
            raise SandboxSafetyError(f'connected to {d["database"]!r}, not the sandbox database {self._cfg.database!r}')
        # The config validated these prefixes already; re-checking what the server reports is the belt to its braces.
        for n in (d['role'], d['database']):
            if not n.startswith(self._cfg.internal_prefix):
                raise SandboxSafetyError(f'{n!r} is not under the internal prefix {self._cfg.internal_prefix!r}')

    def ensure_registry(self, q: Querier, registry: SandboxRegistry) -> None:
        qf.exec(q, f'create schema if not exists {self._quote(self._cfg.registry_schema)}')
        for s in self._renderer.render_create_statements(
                registry.table_def,
                Renderer.CreateOptions(if_not_exists=True),
        ):
            qf.exec(q, s)

    #

    def _lock_key(self, name: str) -> int:
        return advisory_lock_key(f'{self._cfg.prefix}{name}')

    def try_lock(self, q: Querier, name: str) -> bool:
        return bool(qf.query_scalar(q, Q.select([Q.f.pg_try_advisory_lock(Q.p.key)]), {Q.p.key: self._lock_key(name)}))

    def lock(self, q: Querier, name: str) -> None:
        qf.query_scalar(q, Q.select([Q.f.pg_advisory_lock(Q.p.key)]), {Q.p.key: self._lock_key(name)})

    def unlock(self, q: Querier, name: str) -> None:
        check.state(bool(qf.query_scalar(q, Q.select([Q.f.pg_advisory_unlock(Q.p.key)]), {Q.p.key: self._lock_key(name)})))  # noqa

    def server_now(self, q: Querier) -> datetime.datetime:
        return check.isinstance(qf.query_scalar(q, Q.select([Q.f.now()])), datetime.datetime)

    def run_is_live(self, q: Querier, run_id: str) -> bool:
        n = qf.query_scalar(
            q,
            Q.select([Q.f.count(Q.star)], Q.n.pg_stat_activity, Q.eq(Q.i.application_name, Q.p.app)),
            {Q.p.app: self._names.application_name(run_id)},
        )
        return int(n) > 0

    #

    def create_sandbox(self, q: Querier, name: str) -> None:
        qf.exec(q, f'create schema {self._quote(self._names.check_sandbox_name(name))}')

    def drop_sandbox(self, q: Querier, name: str) -> None:
        qf.exec(q, f'drop schema if exists {self._quote(self._names.check_sandbox_name(name))} cascade')

    def list_unregistered(self, q: Querier, registry: SandboxRegistry) -> list[str]:
        # One statement, one snapshot: a schema and its registry row commit together, so a schema seen here without a
        # row is a genuine orphan and not a sandbox mid-creation. `like` is avoided since `_` is its wildcard.
        prefix = self._cfg.prefix
        internal_prefix = self._cfg.internal_prefix
        rt = self._renderer.qname(registry.table_name)
        rows = qf.query_all(q, (
            'select n.nspname as name from pg_namespace n '
            f'where left(n.nspname, {len(prefix)}) = {_lit(prefix)} '
            f'and left(n.nspname, {len(internal_prefix)}) <> {_lit(internal_prefix)} '
            f'and not exists (select 1 from {rt} r where r.name = n.nspname) '
            'order by n.nspname'
        ))
        return [check.non_empty_str(r.to_dict()['name']) for r in rows]


##


@ta.final
class PostgresBootstrapReport(ta.NamedTuple):
    created_role: bool
    created_database: bool


def bootstrap_postgres(
        admin: Querier,
        cfg: SandboxesConfig,
        *,
        role_password: str,
) -> PostgresBootstrapReport:
    """
    Idempotently ensures the sandbox role and database exist on a server, given a session with the privileges to create
    them. Runs identically against a throwaway docker server and a shared managed instance; only the caller's
    credentials differ. The registry itself is not created here - each run self-bootstraps it under a lock - so this is
    the whole of what a shared server needs done by hand, once.
    """

    r = PostgresTabledefRenderer()
    role = r.quote_ident(cfg.role)
    database = r.quote_ident(cfg.database)

    created_role = False
    if not int(qf.query_scalar(
            admin,
            Q.select([Q.f.count(Q.star)], Q.n.pg_roles, Q.eq(Q.i.rolname, Q.p.role)),
            {Q.p.role: cfg.role},
    )):
        qf.exec(admin, f'create role {role} with login password {_lit(role_password)}')
        created_role = True
    # Always re-asserted, so a retargeted password or a stray privilege is corrected rather than silently kept.
    qf.exec(admin, (
        f'alter role {role} with login password {_lit(role_password)} '
        'nosuperuser nocreatedb nocreaterole noreplication'
    ))

    created_database = False
    if not int(qf.query_scalar(
            admin,
            Q.select([Q.f.count(Q.star)], Q.n.pg_database, Q.eq(Q.i.datname, Q.p.database)),
            {Q.p.database: cfg.database},
    )):
        qf.exec(admin, f'create database {database} with owner {role}')
        created_database = True
    else:
        qf.exec(admin, f'alter database {database} owner to {role}')

    return PostgresBootstrapReport(created_role, created_database)
