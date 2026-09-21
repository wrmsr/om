# ruff: noqa: S608
import datetime
import hashlib
import struct
import typing as ta

from ..... import check
from .....secrets.secrets import Secrets
from ....api import querierfuncs as qf
from ....api.core import AsyncDb
from ....api.core import Conn
from ....api.core import Db
from ....api.queriers import Querier
from ....backends import postgres as be
from ....dbs import HostDbLoc
from ....queries import Q
from ....tabledefs.rendering import Renderer
from ..backend import SandboxBackend
from ..backend import UnregisteredSandbox
from ..config import SandboxesConfig
from ..errors import SandboxSafetyError
from ..names import SandboxNames
from ..registry import SandboxKind
from ..registry import SandboxRecord
from ..registry import SandboxRegistry


##


def _lit(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def advisory_lock_key(s: str) -> int:
    # The first 8 bytes of sha1, as a signed 64-bit int - reproducible from sql too via pgcrypto's digest().
    return struct.unpack('>q', hashlib.sha1(s.encode('utf-8')).digest()[:8])[0]  # noqa


class PostgresSandboxBackend(SandboxBackend):
    """
    A sandbox is a schema in the dedicated sandbox database, entered through the session's search path - or, when the
    config allows it, a whole database of its own. A run is recognizable by the application name stamped on each of its
    sessions, so liveness needs nothing beyond the session itself.
    """

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
        self._renderer = be.td.PostgresTabledefRenderer()
        self._registry = SandboxRegistry(cfg)

    @property
    def config(self) -> SandboxesConfig:
        return self._cfg

    @property
    def registry(self) -> SandboxRegistry:
        return self._registry

    @property
    def supported_kinds(self) -> ta.AbstractSet[SandboxKind]:
        return {SandboxKind.SCHEMA, SandboxKind.DATABASE} if self._cfg.database_sandboxes else {SandboxKind.SCHEMA}

    @property
    def default_kind(self) -> SandboxKind:
        return SandboxKind.SCHEMA

    def _quote(self, s: str) -> str:
        return self._renderer.quote_ident(s)

    #

    def open_db(self, run_id: str) -> Db:
        return be.connecting.og8000_db(
            self._loc,
            database=self._cfg.database,
            application_name=self._names.application_name(run_id),
            secrets=self._secrets,
        )

    def _sandbox_db_kwargs(self, run_id: str, name: str, kind: SandboxKind) -> dict[str, ta.Any]:
        self._names.check_sandbox_name(name)

        if kind is SandboxKind.SCHEMA:
            return dict(
                database=self._cfg.database,
                application_name=self._names.application_name(run_id),
                startup_params={'search_path': self._quote(name)},
                secrets=self._secrets,
            )

        elif kind is SandboxKind.DATABASE:
            return dict(
                database=name,
                application_name=self._names.application_name(run_id),
                secrets=self._secrets,
            )

        else:
            raise ValueError(kind)

    def sandbox_db(self, run_id: str, name: str, kind: SandboxKind) -> Db:
        return be.connecting.og8000_db(self._loc, **self._sandbox_db_kwargs(run_id, name, kind))

    def sandbox_asyncio_db(self, run_id: str, name: str, kind: SandboxKind) -> AsyncDb:
        return be.connecting.asyncio_og8000_db(self._loc, **self._sandbox_db_kwargs(run_id, name, kind))

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

    def ensure_registry(self, q: Querier) -> None:
        qf.exec(q, f'create schema if not exists {self._quote(self._cfg.registry_schema)}')
        for s in self._renderer.render_create_statements(
                self._registry.table_def,
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

    #

    def mark_run_live(self, q: Querier, run_id: str) -> None:
        pass  # every session of the run already carries its application name

    def unmark_run_live(self, q: Querier, run_id: str) -> None:
        pass

    def run_is_live(self, q: Querier, run_id: str) -> bool:
        n = qf.query_scalar(
            q,
            Q.select([Q.f.count(Q.star)], Q.n.pg_stat_activity, Q.eq(Q.i.application_name, Q.p.app)),
            {Q.p.app: self._names.application_name(run_id)},
        )
        return int(n) > 0

    #

    def create_sandbox(self, conn: Conn, rec: SandboxRecord) -> None:
        name = self._quote(self._names.check_sandbox_name(rec.name))

        if rec.kind is SandboxKind.SCHEMA:
            # Schema ddl is transactional: the row and the schema commit together.
            with conn.begin() as txn:
                self._registry.insert(txn, rec)
                qf.exec(txn, f'create schema {name}')

        elif rec.kind is SandboxKind.DATABASE:
            # 'create database' refuses to run inside a transaction, so register first; a crash in between leaves a
            # phantom row, which is harmless to reap.
            self._registry.insert(conn, rec)
            qf.exec(conn, f'create database {name}')

        else:
            raise ValueError(rec.kind)

    def drop_sandbox(self, q: Querier, name: str, kind: SandboxKind) -> None:
        qname = self._quote(self._names.check_sandbox_name(name))

        if kind is SandboxKind.SCHEMA:
            qf.exec(q, f'drop schema if exists {qname} cascade')
        elif kind is SandboxKind.DATABASE:
            # 'with (force)' evicts whatever sessions a dead run left connected to it.
            qf.exec(q, f'drop database if exists {qname} with (force)')
        else:
            raise ValueError(kind)

    def list_unregistered(self, q: Querier) -> list[UnregisteredSandbox]:
        # One statement per catalog, one snapshot each: a schema and its registry row commit together, and a database
        # is registered before it is created, so anything seen here without a row is a genuine orphan and not a sandbox
        # mid-creation. `like` is avoided since `_` is its wildcard.
        prefix = self._cfg.prefix
        internal_prefix = self._cfg.internal_prefix
        rt = self._renderer.qname(self._registry.table_name)

        def prefixed(col: str) -> str:
            return (
                f'left({col}, {len(prefix)}) = {_lit(prefix)} '
                f'and left({col}, {len(internal_prefix)}) <> {_lit(internal_prefix)} '
                f'and not exists (select 1 from {rt} r where r.name = {col})'
            )

        out: list[UnregisteredSandbox] = []

        for r in qf.query_all(q, (
                'select n.nspname as name from pg_namespace n '
                f'where {prefixed("n.nspname")} '
                'order by n.nspname'
        )):
            out.append(UnregisteredSandbox(check.non_empty_str(r.to_dict()['name']), SandboxKind.SCHEMA))

        for r in qf.query_all(q, (
                'select d.datname as name from pg_database d '
                f'where {prefixed("d.datname")} '
                'order by d.datname'
        )):
            out.append(UnregisteredSandbox(check.non_empty_str(r.to_dict()['name']), SandboxKind.DATABASE))

        return out


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

    r = be.td.PostgresTabledefRenderer()
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
        f'nosuperuser {"createdb" if cfg.database_sandboxes else "nocreatedb"} nocreaterole noreplication'
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
