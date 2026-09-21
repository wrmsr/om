# ruff: noqa: S608
import datetime
import typing as ta

from ..... import check
from ..... import lang
from .....logs import all as logs
from .....secrets.secrets import Secrets
from ....api import querierfuncs as qf
from ....api.asyncs import ImmediateSyncToAsyncRunner
from ....api.asyncs import SyncToAsyncConn
from ....api.core import AsyncDb
from ....api.core import Conn
from ....api.core import Db
from ....api.queriers import Querier
from ....backends import mysql as be
from ....dbs import HostDbLoc
from ....queries import Q
from ..backend import SandboxBackend
from ..backend import UnregisteredSandbox
from ..config import SandboxesConfig
from ..errors import SandboxSafetyError
from ..errors import SandboxStateError
from ..names import SandboxNames
from ..registry import SandboxKind
from ..registry import SandboxRecord
from ..registry import SandboxRegistry
from ..registry import WholeSecondsTimestampCodec


log = logs.get_module_logger(globals())


##


def _lit(s: str) -> str:
    return "'" + s.replace('\\', '\\\\').replace("'", "''") + "'"


def _account(user: str, host: str = '%') -> str:
    return f'{_lit(user)}@{_lit(host)}'


class MysqlSandboxBackend(SandboxBackend):
    """
    A sandbox is a database (mysql's 'schema'), which the wildcard grant on the prefix confines the role to. Advisory
    locks are mysql's named user locks, and a run keeps one named after itself for as long as its session lives, which
    is how a reaper tells a dead run from an idle one.
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
        self._renderer = be.td.MysqlTabledefRenderer()
        self._inspector = be.inspect.MysqlInspector()
        # Mysql's plain datetime has no fractional seconds.
        self._registry = SandboxRegistry(cfg, timestamp_codec=WholeSecondsTimestampCodec())

    @property
    def config(self) -> SandboxesConfig:
        return self._cfg

    @property
    def registry(self) -> SandboxRegistry:
        return self._registry

    @property
    def supported_kinds(self) -> ta.AbstractSet[SandboxKind]:
        return {SandboxKind.DATABASE}

    @property
    def default_kind(self) -> SandboxKind:
        return SandboxKind.DATABASE

    def _quote(self, s: str) -> str:
        return self._renderer.quote_ident(s)

    #

    def open_db(self, run_id: str) -> Db:
        self._names.check_run_id(run_id)
        return be.connecting.omysql_db(self._loc, database=self._cfg.database, secrets=self._secrets)

    def sandbox_db(self, run_id: str, name: str, kind: SandboxKind) -> Db:
        check.is_(kind, SandboxKind.DATABASE)
        self._names.check_sandbox_name(name)
        return be.connecting.omysql_db(self._loc, database=name, secrets=self._secrets)

    def sandbox_asyncio_db(self, run_id: str, name: str, kind: SandboxKind) -> AsyncDb:
        check.is_(kind, SandboxKind.DATABASE)
        self._names.check_sandbox_name(name)
        return be.connecting.asyncio_omysql_db(self._loc, database=name, secrets=self._secrets)

    #

    def guard(self, q: Querier) -> None:
        d = qf.query_one(q, 'select current_user() as account, database() as db').to_dict()

        user = check.non_empty_str(d['account']).split('@', 1)[0]
        if user != self._cfg.role:
            raise SandboxSafetyError(f'connected as {user!r}, not the sandbox role {self._cfg.role!r}')
        if d['db'] != self._cfg.database:
            raise SandboxSafetyError(f'connected to {d["db"]!r}, not the sandbox database {self._cfg.database!r}')
        for n in (user, d['db']):
            if not n.startswith(self._cfg.internal_prefix):
                raise SandboxSafetyError(f'{n!r} is not under the internal prefix {self._cfg.internal_prefix!r}')

        # Mysql has no single superuser flag; what matters is that the account holds no global privilege at all, only
        # the db-pattern grant - so anything beyond the bare 'usage' marker means this is not the sandbox role.
        privs = {
            r.to_dict()['privilege_type']
            for r in qf.query_all(q, (
                'select privilege_type from information_schema.user_privileges '
                "where grantee = concat(\"'\", substring_index(current_user(), '@', 1), \"'@'\", "
                "substring_index(current_user(), '@', -1), \"'\")"
            ))
        } - {'USAGE'}
        if privs:
            raise SandboxSafetyError(f'refusing to run with global privileges {sorted(privs)!r}')

    def ensure_registry(self, q: Querier) -> None:
        qf.exec(q, f'create database if not exists {self._quote(self._cfg.registry_schema)}')

        # Mysql has no 'create index if not exists', so the table is created only if reflection finds it absent; the
        # caller holds the registry lock, so that is race-free.
        aq = SyncToAsyncConn(ImmediateSyncToAsyncRunner(), check.isinstance(q, Conn))
        if lang.sync_await(self._inspector.reflect_table(aq, self._registry.table_name)) is None:
            for s in self._renderer.render_create_statements(self._registry.table_def):
                qf.exec(q, s)

    #

    def _lock_name(self, name: str) -> str:
        return f'{self._cfg.prefix}{name}'

    def try_lock(self, q: Querier, name: str) -> bool:
        r = qf.query_scalar(
            q,
            Q.select([Q.f.get_lock(Q.p.name, Q.p.timeout)]),
            {Q.p.name: self._lock_name(name), Q.p.timeout: 0},
        )
        return int(check.not_none(r)) == 1

    def lock(self, q: Querier, name: str) -> None:
        r = qf.query_scalar(
            q,
            Q.select([Q.f.get_lock(Q.p.name, Q.p.timeout)]),
            {Q.p.name: self._lock_name(name), Q.p.timeout: -1},
        )
        check.state(int(check.not_none(r)) == 1)

    def unlock(self, q: Querier, name: str) -> None:
        r = qf.query_scalar(
            q,
            Q.select([Q.f.release_lock(Q.p.name)]),
            {Q.p.name: self._lock_name(name)},
        )
        check.state(int(check.not_none(r)) == 1)

    def server_now(self, q: Querier) -> datetime.datetime:
        return check.isinstance(qf.query_scalar(q, 'select now(6)'), datetime.datetime)

    #

    def mark_run_live(self, q: Querier, run_id: str) -> None:
        r = qf.query_scalar(
            q,
            Q.select([Q.f.get_lock(Q.p.name, Q.p.timeout)]),
            {Q.p.name: self._names.application_name(run_id), Q.p.timeout: 0},
        )
        if int(check.not_none(r)) != 1:
            raise SandboxStateError(f'run {run_id!r} is already marked live elsewhere')

    def unmark_run_live(self, q: Querier, run_id: str) -> None:
        qf.query_scalar(
            q,
            Q.select([Q.f.release_lock(Q.p.name)]),
            {Q.p.name: self._names.application_name(run_id)},
        )

    def run_is_live(self, q: Querier, run_id: str) -> bool:
        r = qf.query_scalar(
            q,
            Q.select([Q.f.is_used_lock(Q.p.name)]),
            {Q.p.name: self._names.application_name(run_id)},
        )
        return r is not None

    #

    def create_sandbox(self, conn: Conn, rec: SandboxRecord) -> None:
        check.is_(rec.kind, SandboxKind.DATABASE)
        name = self._quote(self._names.check_sandbox_name(rec.name))

        # Database ddl commits implicitly, so register first; a crash in between leaves a phantom row, harmless to reap.
        self._registry.insert(conn, rec)
        qf.exec(conn, f'create database {name}')

    def drop_sandbox(self, q: Querier, name: str, kind: SandboxKind) -> None:
        check.is_(kind, SandboxKind.DATABASE)
        qf.exec(q, f'drop database if exists {self._quote(self._names.check_sandbox_name(name))}')

    def list_unregistered(self, q: Querier) -> list[UnregisteredSandbox]:
        # A database is registered before it is created, so one that shows up here without a row is a real orphan.
        prefix = self._cfg.prefix
        internal_prefix = self._cfg.internal_prefix
        rt = self._renderer.qname(self._registry.table_name)
        rows = qf.query_all(q, (
            'select s.schema_name as name from information_schema.schemata s '
            f'where left(s.schema_name, {len(prefix)}) = {_lit(prefix)} '
            f'and left(s.schema_name, {len(internal_prefix)}) <> {_lit(internal_prefix)} '
            f'and not exists (select 1 from {rt} r where r.name = s.schema_name) '
            'order by s.schema_name'
        ))
        return [UnregisteredSandbox(check.non_empty_str(r.to_dict()['name']), SandboxKind.DATABASE) for r in rows]


##


@ta.final
class MysqlBootstrapReport(ta.NamedTuple):
    created_user: bool
    created_database: bool


def grant_pattern(prefix: str) -> str:
    # In a grant's database pattern `_` and `%` are wildcards, so the prefix's own underscores must be escaped.
    return prefix.replace('\\', '\\\\').replace('_', '\\_').replace('%', '\\%') + '%'


def bootstrap_mysql(
        admin: Querier,
        cfg: SandboxesConfig,
        *,
        role_password: str,
) -> MysqlBootstrapReport:
    """
    Idempotently ensures the sandbox account and its home database exist, and that the account holds exactly one grant:
    everything on databases under the prefix and nothing anywhere else - the server itself then enforces the prefix
    boundary. Re-run freely; privileges are revoked and re-granted from scratch each time.
    """

    r = be.td.MysqlTabledefRenderer()
    account = _account(cfg.role)
    database = r.quote_ident(cfg.database)

    created_user = False
    if not int(qf.query_scalar(
            admin,
            Q.select(
                [Q.f.count(Q.star)],
                Q.n(('mysql', 'user')),
                Q.and_(
                    Q.eq(Q.i.user, Q.p.user),
                    Q.eq(Q.i.host, Q.p.host),
                ),
            ),
            {
                Q.p.user: cfg.role,
                Q.p.host: '%',
            },
    )):
        qf.exec(admin, f'create user {account} identified by {_lit(role_password)}')
        created_user = True
    qf.exec(admin, f'alter user {account} identified by {_lit(role_password)}')
    qf.exec(admin, f'revoke all privileges, grant option from {account}')
    qf.exec(admin, f'grant all privileges on {r.quote_ident(grant_pattern(cfg.prefix))}.* to {account}')

    # With binary logging on, mysql lets only a super account create triggers and functions unless the server is told to
    # trust creators. A managed instance sets this through its parameter group instead, so a refusal is a warning.
    try:
        qf.exec(admin, 'set global log_bin_trust_function_creators = 1')
    except Exception:  # noqa
        log.warning('Could not set log_bin_trust_function_creators; the sandbox role may be unable to create triggers')

    created_database = False
    if not int(qf.query_scalar(
            admin,
            Q.select(
                [Q.f.count(Q.star)],
                Q.n(('information_schema', 'schemata')),
                Q.eq(Q.i.schema_name, Q.p.db),
            ),
            {Q.p.db: cfg.database},
    )):
        qf.exec(admin, f'create database {database}')
        created_database = True

    return MysqlBootstrapReport(created_user, created_database)
