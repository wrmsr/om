"""
Thin, provisional glue from a db location to a live og8000 `Db`. Expected to be redone once connection configuration is
properly injected; kept minimal on purpose.
"""
import typing as ta
import urllib.parse

from .... import check
from .... import dataclasses as dc
from ....secrets.secrets import SecretRef
from ....secrets.secrets import Secrets
from ...api.core import Db
from ...dbs import DbTypes
from ...dbs import HostDbLoc
from ...drivers.og8000.core.sync import SyncCoreConnection
from .drivers.og8000.sync import Og8000Db


##


def parse_url_db_loc(url: str) -> tuple[HostDbLoc, str | None]:
    """Splits a `postgresql://user:password@host:port/database` url into a host location and the database name."""

    p_u = urllib.parse.urlparse(url)

    loc = HostDbLoc(
        check.non_empty_str(p_u.hostname),
        p_u.port if p_u.port is not None else DbTypes.POSTGRES.default_port,
        username=p_u.username,
        password=p_u.password,
    )

    return loc, (p_u.path.lstrip('/') or None)


def reveal_password(loc: HostDbLoc, secrets: Secrets | None = None) -> str | None:
    if (pw := loc.password) is None:
        return None
    elif isinstance(pw, str):
        return pw
    elif isinstance(pw, SecretRef):
        return check.not_none(secrets).fix(pw).reveal()
    else:
        raise TypeError(pw)


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

    return Og8000Db(lambda: SyncCoreConnection(**kwargs))


def with_username(loc: HostDbLoc, username: str, password: str | None) -> HostDbLoc:
    return dc.replace(loc, username=username, password=password)
