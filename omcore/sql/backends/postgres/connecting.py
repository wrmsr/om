"""
Thin, provisional glue from a db location to a live og8000 `Db`. Expected to be redone once connection configuration is
properly injected; kept minimal on purpose.
"""
import typing as ta

from .... import check
from ....secrets.secrets import Secrets
from ...api.core import Db
from ...dbs import DbTypes
from ...dbs import HostDbLoc
from ...drivers import og8000 as og8000_
from ..connecting import parse_url_db_loc as _parse_url_db_loc
from ..connecting import reveal_password
from ..connecting import with_username  # noqa
from .drivers import og8000


##


def parse_url_db_loc(url: str) -> tuple[HostDbLoc, str | None]:
    return _parse_url_db_loc(url, DbTypes.POSTGRES)


def og8000_db(
        loc: HostDbLoc,
        *,
        database: str | None = None,
        application_name: str | None = None,
        startup_params: ta.Mapping[str, str] | None = None,
        secrets: Secrets | None = None,
) -> Db:
    password = reveal_password(loc, secrets)

    kwargs: dict[str, ta.Any] = dict(
        user=check.non_empty_str(loc.username),
        password=password,
        host=loc.host,
        port=loc.port if loc.port is not None else check.not_none(DbTypes.POSTGRES.default_port),
        database=database,
        application_name=application_name,
        startup_params=dict(startup_params) if startup_params is not None else None,
    )

    return og8000.Og8000Db(lambda: og8000_.SyncCoreConnection(**kwargs))
