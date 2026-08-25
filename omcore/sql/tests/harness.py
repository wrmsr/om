import typing as ta

from ... import check
from ... import lang
from ...docker.all import get_compose_port
from ...docker.all import is_likely_in_docker
from ...docker.tests.services import ComposeServices
from ...os.environ import EnvVar
from ...testing.pytest import inject as pti
from ..dbs import DbSpec
from ..dbs import DbTypes
from ..dbs import UrlDbLoc


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
