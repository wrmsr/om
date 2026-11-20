"""
Thin, provisional glue from a db location to a live omysql `Db`. Expected to be redone once connection configuration is
properly injected; kept minimal on purpose.
"""
import typing as ta

from .... import check
from .... import lang
from ....secrets.secrets import Secrets
from ...api.core import AsyncDb
from ...api.core import Db
from ...dbs.specs import DbFamilies
from ...dbs.specs import HostDbLoc
from ...drivers.omysql.core.asyncio import AsyncioConnection
from ...drivers.omysql.core.sync import SyncConnection
from ..connecting import parse_url_db_loc as _parse_url_db_loc
from ..connecting import reveal_loc_field
from ..connecting import with_username  # noqa
from .drivers.omysql.asyncio import AsyncioOmysqlDb
from .drivers.omysql.sync import OmysqlDb


##


def parse_url_db_loc(url: str) -> tuple[HostDbLoc, str | None]:
    return _parse_url_db_loc(url, DbFamilies.MYSQL)


def _omysql_kwargs(
        loc: HostDbLoc,
        *,
        database: str | None = None,
        secrets: Secrets | None = None,
) -> dict[str, ta.Any]:
    return dict(
        user=reveal_loc_field(loc.username, str, secrets),
        password=reveal_loc_field(loc.password, str, secrets),
        host=reveal_loc_field(loc.host, str, secrets),
        port=lang.coalesce(reveal_loc_field(loc.port, int, secrets), check.not_none(DbFamilies.MYSQL.default_port)),
        database=database,
    )


def omysql_db(
        loc: HostDbLoc,
        *,
        database: str | None = None,
        secrets: Secrets | None = None,
) -> Db:
    kwargs = _omysql_kwargs(loc, database=database, secrets=secrets)

    return OmysqlDb(lambda: SyncConnection(**kwargs))


def asyncio_omysql_db(
        loc: HostDbLoc,
        *,
        database: str | None = None,
        secrets: Secrets | None = None,
) -> AsyncDb:
    """The same db, reached over asyncio's own io rather than blocking sockets."""

    kwargs = _omysql_kwargs(loc, database=database, secrets=secrets)

    return AsyncioOmysqlDb(lambda: AsyncioConnection.connect(**kwargs))
