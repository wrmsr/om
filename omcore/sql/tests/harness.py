import contextlib
import typing as ta

from ... import check
from ... import lang
from ...docker.all import get_compose_port
from ...docker.all import is_likely_in_docker
from ...docker.tests.services import ComposeServices
from ...os.environ import EnvVar
from ...testing.pytest import inject as pti
from ..backends.mysql import connecting as myc
from ..backends.postgres import connecting as pgc
from ..dbs import DbSpec
from ..dbs import DbTypes
from ..dbs import HostDbLoc
from ..dbs import UrlDbLoc


with lang.auto_proxy_import(globals()):
    from ..testing import sandboxes as sbx


##


MYSQL_URL_ENV_VAR = EnvVar('OM_TEST_MYSQL_URL')
POSTGRES_URL_ENV_VAR = EnvVar('OM_TEST_POSTGRES_URL')
PGVECTOR_URL_ENV_VAR = EnvVar('OM_TEST_PGVECTOR_URL')


@pti.bind('session')
class HarnessDbs:
    def __init__(self, compose_services: ComposeServices) -> None:
        super().__init__()

        self._compose_services = compose_services

    @lang.cached_function
    def _in_docker(self) -> bool:
        return is_likely_in_docker()

    def _build_mysql_db(self, name: str, svc: ta.Mapping[str, ta.Any]) -> DbSpec:
        if self._in_docker():
            host = self._compose_services.prefix + name
            port = DbTypes.MYSQL.default_port
        else:
            host = '127.0.0.1'
            port = get_compose_port(svc, check.not_none(DbTypes.MYSQL.default_port))

        env = svc['environment']
        return DbSpec(
            name,
            DbTypes.MYSQL,
            UrlDbLoc(f'mysql://root:{env["MYSQL_ROOT_PASSWORD"]}@{host}:{port}'),
        )

    def _build_postgres_db(self, name: str, svc: ta.Mapping[str, ta.Any]) -> DbSpec:
        if self._in_docker():
            host = self._compose_services.prefix + name
            port = DbTypes.POSTGRES.default_port
        else:
            host = '127.0.0.1'
            port = get_compose_port(svc, check.not_none(DbTypes.POSTGRES.default_port))

        env = svc['environment']
        return DbSpec(
            name,
            DbTypes.POSTGRES,
            UrlDbLoc(f'postgresql://{env["POSTGRES_USER"]}:{env["POSTGRES_PASSWORD"]}@{host}:{port}'),
        )

    def specs(self) -> ta.Mapping[str, DbSpec]:
        svcs = self._compose_services.config().get_services()
        lst: list[DbSpec] = []

        for name, url_var in [
            ('mysql', MYSQL_URL_ENV_VAR),
        ]:
            if url := url_var.get(None):
                lst.append(DbSpec(
                    name,
                    DbTypes.MYSQL,
                    UrlDbLoc(url),
                ))

            elif (svc := svcs.get(name)):
                lst.append(self._build_mysql_db(name, svc))

        for name, url_var in [
            ('postgres', POSTGRES_URL_ENV_VAR),
            ('pgvector', PGVECTOR_URL_ENV_VAR),
        ]:
            if url := url_var.get(None):
                lst.append(DbSpec(
                    name,
                    DbTypes.POSTGRES,
                    UrlDbLoc(url),
                ))

            elif (svc := svcs.get(name)):
                lst.append(self._build_postgres_db(name, svc))

        return {s.name: s for s in lst}


##


POSTGRES_SANDBOX_URL_ENV_VAR = EnvVar('OM_TEST_POSTGRES_SANDBOX_URL')
MYSQL_SANDBOX_URL_ENV_VAR = EnvVar('OM_TEST_MYSQL_SANDBOX_URL')

# FIXME: provisional - the docker/local sandbox role's password, until credentials are properly injected.
SANDBOX_ROLE_PASSWORD = 'om'  # noqa: S105


@pti.bind('session')
class HarnessSandboxes:
    """
    The session's sandbox allocators. With only an admin url at hand (compose, or a local server) the sandbox role and
    database are bootstrapped on first use; a pre-bootstrapped sandbox-role url (a shared managed instance) is used as
    given and never bootstrapped. Allocators are entered here and exited with the session.
    """

    def __init__(
            self,
            dbs: HarnessDbs,
            es: contextlib.ExitStack,
    ) -> None:
        super().__init__()

        self._dbs = dbs
        self._es = es

    ##
    # postgres

    @lang.cached_function
    def postgres_config(self) -> sbx.SandboxesConfig:
        # A self-bootstrapped (throwaway) server gets the database kind too; a pre-bootstrapped one is whatever it is.
        return sbx.SandboxesConfig(database_sandboxes=POSTGRES_SANDBOX_URL_ENV_VAR.get(None) is None)

    @lang.cached_function
    def postgres_loc(self) -> HostDbLoc:
        cfg = self.postgres_config()

        if (url := POSTGRES_SANDBOX_URL_ENV_VAR.get(None)):
            loc, _ = pgc.parse_url_db_loc(url)
            return loc

        admin_loc, admin_database = self.postgres_admin()
        with pgc.og8000_db(admin_loc, database=admin_database).connect() as conn:
            sbx.bootstrap_postgres(conn, cfg, role_password=SANDBOX_ROLE_PASSWORD)

        return pgc.with_username(admin_loc, cfg.role, SANDBOX_ROLE_PASSWORD)

    @lang.cached_function
    def postgres_admin(self) -> tuple[HostDbLoc, str]:
        url = check.isinstance(check.isinstance(self._dbs.specs()['postgres'].loc, UrlDbLoc).url, str)
        loc, database = pgc.parse_url_db_loc(url)
        return loc, (database if database is not None else 'postgres')

    @lang.cached_function
    def postgres(self) -> sbx.SandboxAllocator:
        backend = sbx.PostgresSandboxBackend(self.postgres_config(), self.postgres_loc())
        return self._es.enter_context(sbx.SandboxAllocator(backend))

    ##
    # mysql

    @lang.cached_function
    def mysql_config(self) -> sbx.SandboxesConfig:
        return sbx.SandboxesConfig()

    @lang.cached_function
    def mysql_admin(self) -> HostDbLoc:
        url = check.isinstance(check.isinstance(self._dbs.specs()['mysql'].loc, UrlDbLoc).url, str)
        loc, _ = myc.parse_url_db_loc(url)
        return loc

    @lang.cached_function
    def mysql_loc(self) -> HostDbLoc:
        cfg = self.mysql_config()

        if (url := MYSQL_SANDBOX_URL_ENV_VAR.get(None)):
            loc, _ = myc.parse_url_db_loc(url)
            return loc

        admin_loc = self.mysql_admin()
        with myc.omysql_db(admin_loc).connect() as conn:
            sbx.bootstrap_mysql(conn, cfg, role_password=SANDBOX_ROLE_PASSWORD)

        return myc.with_username(admin_loc, cfg.role, SANDBOX_ROLE_PASSWORD)

    @lang.cached_function
    def mysql(self) -> sbx.SandboxAllocator:
        backend = sbx.MysqlSandboxBackend(self.mysql_config(), self.mysql_loc())
        return self._es.enter_context(sbx.SandboxAllocator(backend))

    ##
    # sqlite

    @lang.cached_function
    def sqlite_config(self) -> sbx.SandboxesConfig:
        return sbx.SandboxesConfig()

    @lang.cached_function
    def sqlite(self) -> sbx.SandboxAllocator:
        backend = sbx.SqliteSandboxBackend(self.sqlite_config())
        return self._es.enter_context(sbx.SandboxAllocator(backend))
