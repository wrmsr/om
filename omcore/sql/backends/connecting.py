"""
Thin, provisional glue between db locations and live connections, shared by the per-backend `connecting` modules.
Expected to be redone once connection configuration is properly injected; kept minimal on purpose.
"""
import typing as ta
import urllib.parse

from ... import check
from ... import dataclasses as dc
from ...secrets import all as sec
from ..dbs.specs import DbFamily
from ..dbs.specs import HostDbLoc


T = ta.TypeVar('T')


##


def parse_url_db_loc(url: str, family: DbFamily) -> tuple[HostDbLoc, str | None]:
    """Splits a `scheme://user:password@host:port/database` url into a host location and the database name."""

    p_u = urllib.parse.urlparse(url)

    loc = HostDbLoc(
        check.non_empty_str(p_u.hostname),
        p_u.port if p_u.port is not None else family.default_port,
        username=p_u.username,
        password=p_u.password,
    )

    return loc, (p_u.path.lstrip('/') or None)


def reveal_loc_field(
        v: sec.SecretRef | T | None,
        ty: type[T],
        secrets: sec.Secrets | None = None,
) -> T | None:
    if v is None or isinstance(v, ty):
        return v
    elif isinstance(v, sec.SecretRef):
        s = check.not_none(secrets).fix(v).reveal()
        if ty is str:
            return ta.cast(T, s)
        elif ty is int:
            return ta.cast(T, int(s))
        else:
            raise TypeError(ty)
    else:
        raise TypeError(v)


def with_username(
        loc: HostDbLoc,
        username: str,
        password: str | None,
) -> HostDbLoc:
    return dc.replace(
        loc,
        username=username,
        password=password,
    )
