import contextlib
import enum
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...secrets.secrets import SecretRef
from ...secrets.secrets import Secrets
from ..api.adapters import Adapter
from ..api.core import AsyncConn
from ..api.core import AsyncDb
from ..api.core import AnyDb
from ..api.core import AsyncRows
from ..api.core import AsyncTxn
from ..api.core import Conn
from ..api.core import Db
from ..api.core import Rows
from ..api.core import Txn
from ..api.queries import Queryable
from .specs import DbSpec
from .specs import HostDbLoc
from .specs import UrlDbLoc
from .sets import DbSets
from .factories import DbFactory
from .factories import AsyncDbFactory
from .factories import _DefaultAsyncDbFactory
from .factories import _DefaultDbFactory
from .sets import DbSlot
from .sets import DbSetKey


T = ta.TypeVar('T')


##


class AnyDbs(lang.Abstract):
    def __init__(
            self,
            sets: DbSets,
            *,
            secrets: Secrets | None = None,
            default_key: DbSetKey | None = DbSlot.WRITER,
    ) -> None:
        super().__init__()

        self._sets = sets
        self._secrets = secrets
        self._default_key = default_key

        self._entered = False
        self._closed = False


##


class Dbs(AnyDbs, lang.ExitStacked):
    def __init__(
            self,
            sets: DbSets,
            *,
            default_key: DbSetKey | None = DbSlot.WRITER,
            secrets: Secrets | None = None,

            factory: DbFactory | None = None,
    ) -> None:
        super().__init__(
            sets,
            default_key=default_key,
            secrets=secrets,
        )

        if factory is None:
            factory = _DefaultDbFactory()
        self._factory = factory

    def db(self, name: str, key: DbSetKey | None = None) -> Db:
        check.state(self._entered)

        spec = self._sets[name][slot]
        readonly = slot != DbSlot.WRITER
        cannot_write = bool(spec.caps and spec.caps.readonly)
        if cannot_write and not readonly:
            raise ValueError('Writer slot refers to a read-only endpoint')

        try:
            db = self._sync_dbs[spec]
        except KeyError:
            db = self._sync_dbs[spec] = self._sync_db(spec)
        return _DefaultReadonlyDb(db, readonly, cannot_write=cannot_write)

##


class AsyncDbs(AnyDbs, lang.AsyncExitStacked):
    def __init__(
            self,
            sets: DbSets,
            *,
            factory: DbFactory | None = None,
            async_factory: AsyncDbFactory | None = None,

            secrets: Secrets | None = None,

            default_key: DbSetKey | None = DbSlot.WRITER,
    ) -> None:
        super().__init__()

        self._sets = sets
        self._secrets = secrets
        self._default_key = default_key

        if factory is None:
            factory = _DefaultDbFactory()
        if async_factory is None:
            async_factory = _DefaultAsyncDbFactory()
        self._factory = factory
        self._async_factories = async_factory

        self._dbs: dict[DbSpec, Db] = {}
        self._async_dbs: dict[DbSpec, AsyncDb] = {}

        self._aes = contextlib.AsyncExitStack()

        self._entered = False
        self._closed = False

    #

    async def __aenter__(self) -> ta.Self:
        check.state(not self._entered and not self._closed)
        await self._aes.__aenter__()
        self._entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._entered = False
        self._closed = True
        return await self._aes.__aexit__(exc_type, exc_val, exc_tb)

    #


    #

    async def async_db(self, name: str, key: DbSetKey | None = None) -> AsyncDb:
        check.state(self._entered)

        spec = self._sets[name][slot]
        readonly = slot != DbSlot.WRITER
        cannot_write = bool(spec.caps and spec.caps.readonly)
        if cannot_write and not readonly:
            raise ValueError('Writer slot refers to a read-only endpoint')

        try:
            db = self._async_dbs[spec]
        except KeyError:
            db = self._async_dbs[spec] = await self._async_db(spec)
        return _DefaultReadonlyAsyncDb(db, readonly, cannot_write=cannot_write)
