"""
Thin, provisional glue between db locations and live connections, shared by the per-backend `connecting` modules.
Expected to be redone once connection configuration is properly injected; kept minimal on purpose.
"""
import urllib.parse

from ... import check
from ... import dataclasses as dc
from ...secrets.secrets import SecretRef
from ...secrets.secrets import Secrets
from ..dbs import DbType
from ..dbs import HostDbLoc


##


def parse_url_db_loc(url: str, db_type: DbType) -> tuple[HostDbLoc, str | None]:
    """Splits a `scheme://user:password@host:port/database` url into a host location and the database name."""

    p_u = urllib.parse.urlparse(url)

    loc = HostDbLoc(
        check.non_empty_str(p_u.hostname),
        p_u.port if p_u.port is not None else db_type.default_port,
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


def with_username(loc: HostDbLoc, username: str, password: str | None) -> HostDbLoc:
    return dc.replace(loc, username=username, password=password)
