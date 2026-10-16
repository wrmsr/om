import typing as ta

from omcore import lang
from omcore import orm

from .types import Orm


##


class StoreOrm(Orm):
    """An orm over whatever store it is given - which for an `orm.InMemoryStore` is all there is to it."""

    def __init__(
            self,
            *,
            registry: orm.Registry,
            store: orm.Store,
            read_store: orm.Store | None = None,
    ) -> None:
        super().__init__()

        self._registry = registry
        self._store = store
        self._read_store = read_store

    def new_session(self) -> ta.AsyncContextManager[orm.Session]:
        return orm.session(self._registry, self._store)

    def read_session(self) -> ta.AsyncContextManager[orm.Session]:
        return orm.session(self._registry, self._read_store or self._store, readonly=True)

    def ensure_session(self) -> ta.AsyncContextManager[orm.Session]:
        if (active_session := orm.opt_active_session()) is not None:
            return lang.ValueAsyncContextManager(active_session)
        else:
            return self.new_session()
