"""
TODO:
 - finally unify this crap with the backends.connecting crap - ugh
"""
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...secrets.secrets import SecretRef
from ...secrets.secrets import Secrets
from ..api.core import AsyncDb
from ..api.core import Db
from .specs import DbFamilies
from .specs import DbSpec
from .specs import HostDbLoc
from .specs import UrlDbLoc


with lang.auto_proxy_import(globals()):
    from ..backends import connecting as bc
    from ..backends.mysql import connecting as mc
    from ..backends.postgres import connecting as pc
    from ..backends.sqlite import connecting as sc


T_co = ta.TypeVar('T_co', covariant=True)


##


@dc.dataclass(frozen=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class DbFactoryContext:
    spec: DbSpec

    _: dc.KW_ONLY

    secrets: Secrets | None = None


class AnyDbFactory(ta.Protocol[T_co]):
    def __call__(self, ctx: DbFactoryContext) -> T_co: ...


DbFactoryOutput: ta.TypeAlias = ta.ContextManager[Db]
DbFactory: ta.TypeAlias = ta.Callable[[DbFactoryContext], DbFactoryOutput]

AsyncDbFactoryOutput: ta.TypeAlias = ta.AsyncContextManager[AsyncDb]
AsyncDbFactory: ta.TypeAlias = ta.Callable[[DbFactoryContext], AsyncDbFactoryOutput]


##


class _BaseDefaultDbFactory:
    def _url(self, ctx: DbFactoryContext, loc: UrlDbLoc) -> str:
        if isinstance(loc.url, str):
            return loc.url

        elif isinstance(loc.url, SecretRef):
            return check.not_none(ctx.secrets).fix(loc.url).reveal()

        else:
            raise TypeError(loc.url)

    def _network_loc(self, ctx: DbFactoryContext, spec: DbSpec) -> tuple[HostDbLoc, str | None]:
        if isinstance(spec.loc, HostDbLoc):
            return spec.loc, spec.database

        elif isinstance(spec.loc, UrlDbLoc):
            loc, database = bc.parse_url_db_loc(self._url(ctx, spec.loc), spec.type)
            return loc, spec.database if spec.database is not None else database

        else:
            raise TypeError(spec.loc)

    #

    def _driver(self, spec: DbSpec) -> str:
        if spec.driver is not None:
            return spec.driver

        return {
            DbFamilies.SQLITE: 'sqlite3',
            DbFamilies.POSTGRES: 'og8000',
            DbFamilies.MYSQL: 'omysql',
            DbFamilies.SNOWFLAKE: 'snowflake',
        }[spec.type]


#


class _DefaultDbFactory(_BaseDefaultDbFactory):
    def __call__(self, ctx: DbFactoryContext) -> ta.ContextManager[Db]:
        spec = ctx.spec
        driver = self._driver(spec)

        if driver == 'sqlite3' and spec.type == DbFamilies.SQLITE:
            return lang.ValueContextManager(sc.sqlite_db(check.isinstance(
                spec.loc,
                sc.SqliteDbConfig,
            )))

        elif driver == 'og8000' and spec.type == DbFamilies.POSTGRES:
            loc, database = self._network_loc(ctx, spec)
            return lang.ValueContextManager(pc.og8000_db(
                loc,
                database=database,
                secrets=ctx.secrets,
            ))

        elif driver == 'omysql' and spec.type == DbFamilies.MYSQL:
            loc, database = self._network_loc(ctx, spec)
            return lang.ValueContextManager(mc.omysql_db(
                loc,
                database=database,
                secrets=ctx.secrets,
            ))

        else:
            raise ValueError(f'No sync database factory for {spec.type.name}/{driver}')


#


class _DefaultAsyncDbFactory(_BaseDefaultDbFactory):
    def __call__(self, ctx: DbFactoryContext) -> ta.AsyncContextManager[AsyncDb]:
        spec = ctx.spec
        driver = self._driver(ctx.spec)

        if driver == 'sqlite3' and spec.type == DbFamilies.SQLITE:
            return sc.asyncio_sqlite_db(check.isinstance(spec.loc, sc.SqliteDbConfig))

        elif driver == 'og8000' and spec.type == DbFamilies.POSTGRES:
            loc, database = self._network_loc(ctx, spec)
            return lang.ValueAsyncContextManager(pc.asyncio_og8000_db(
                loc,
                database=database,
                secrets=ctx.secrets,
            ))

        elif driver == 'omysql' and spec.type == DbFamilies.MYSQL:
            loc, database = self._network_loc(ctx, spec)
            return lang.ValueAsyncContextManager(mc.asyncio_omysql_db(
                loc,
                database=database,
                secrets=ctx.secrets,
            ))

        else:
            raise ValueError(f'No async database factory for {spec.type.name}/{driver}')
