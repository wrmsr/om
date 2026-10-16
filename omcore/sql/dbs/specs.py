import typing as ta
import urllib.parse

from ... import dataclasses as dc
from ... import lang
from ...secrets import all as sec


##


@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class DbFamily(lang.Final):
    name: str
    dialect_name: str

    default_port: int | None = None


class DbFamilies(lang.Namespace, lang.Final):
    MYSQL = DbFamily(
        name='mysql',
        dialect_name='mysql',
        default_port=3306,
    )

    POSTGRES = DbFamily(
        name='postgres',
        dialect_name='postgresql',
        default_port=5432,
    )

    SQLITE = DbFamily(
        name='sqlite',
        dialect_name='sqlite',
    )

    SNOWFLAKE = DbFamily(
        name='snowflake',
        dialect_name='snowflake',
    )


##


class DbLoc(lang.Abstract, lang.PackageSealed, sealed_package=__package__.rpartition('.')[0]):
    pass


@dc.dataclass(frozen=True)
class UrlDbLoc(DbLoc, lang.Final):
    url: sec.SecretRefOrStr = dc.xfield() | sec.secret_field


@dc.dataclass(frozen=True)
class HostDbLoc(DbLoc, lang.Final):
    host: str
    port: int | None = None

    _: dc.KW_ONLY

    username: str | None = None
    password: sec.SecretRefOrStr | None = dc.xfield(default=None) | sec.secret_field


##


@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class DbCaps:
    readonly: bool | None = None
    privileged: bool | None = None


@dc.dataclass(frozen=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class DbSpec(lang.Final):
    name: str
    type: DbFamily  # FIXME: -> family
    loc: DbLoc

    _: dc.KW_ONLY

    caps: DbCaps | None = None

    @property
    def readonly(self) -> bool | None:
        if (caps := self.caps) is None:
            return None
        return caps.readonly

    database: str | None = None
    driver: str | None = None


##


def rebuild_url(url: str, fn: ta.Callable[[urllib.parse.ParseResult], urllib.parse.ParseResult]) -> str:
    if '://' in url:
        engine, _, url = url.partition('://')
        url = 'sql://' + url
    else:
        engine = None
    parsed = urllib.parse.urlparse(url)
    parsed = fn(parsed)
    if engine is not None and parsed.scheme == 'sql':
        parsed = parsed._replace(scheme=engine)
    return urllib.parse.urlunparse(parsed)  # noqa


def set_url_engine(url: str, engine: str) -> str:
    return rebuild_url(url, lambda parsed: parsed._replace(scheme=engine))  # noqa


def set_url_database(url: str, database: str) -> str:
    return rebuild_url(url, lambda parsed: parsed._replace(path='/' + database))  # noqa
