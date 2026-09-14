"""
Thin, provisional glue from a db location to a live omysql `Db`. Expected to be redone once connection configuration is
properly injected; kept minimal on purpose.
"""
import typing as ta

from .... import check
from ....secrets.secrets import Secrets
from ...api.core import Db
from ...dbs import DbTypes
from ...dbs import HostDbLoc
from ...drivers.omysql.core.sync import SyncConnection
from ..connecting import parse_url_db_loc as _parse_url_db_loc
from ..connecting import reveal_password
from ..connecting import with_username  # noqa
from .drivers.omysql.sync import OmysqlDb


##


def parse_url_db_loc(url: str) -> tuple[HostDbLoc, str | None]:
    return _parse_url_db_loc(url, DbTypes.MYSQL)


def omysql_db(
        loc: HostDbLoc,
        *,
        database: str | None = None,
        secrets: Secrets | None = None,
) -> Db:
    password = reveal_password(loc, secrets)

    kwargs: dict[str, ta.Any] = dict(
        user=check.non_empty_str(loc.username),
        password=password if password is not None else '',
        host=loc.host,
        port=loc.port if loc.port is not None else check.not_none(DbTypes.MYSQL.default_port),
        database=database,
    )

    return OmysqlDb(lambda: SyncConnection(**kwargs))
