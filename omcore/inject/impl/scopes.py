import abc
import contextlib
import enum
import threading
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ..bindings import Binding
from ..elements import Elements
from ..elements import as_elements
from ..errors import ScopeAlreadyOpenError
from ..errors import ScopeNotOpenError
from ..injector import AsyncInjector
from ..keys import Key
from ..keys import as_key
from ..providers import FnProvider
from ..providers import Provider
from ..scopes import ScopeSeededProvider
from ..scopes import SeededScope
from ..scopes import Singleton
from ..scopes import ThreadScope
from ..types import Scope
from ..types import Unscoped
from .bindings import BindingImpl
from .providers import ProviderImpl
from .provision import OnceProvisionMap


if ta.TYPE_CHECKING:
    from . import injector as _injector
else:
    _injector = lang.proxy_import('.injector', __package__)


ScopeT = ta.TypeVar('ScopeT', bound=Scope)


##


class EagerInstantiationPoint(enum.Enum):
    """
    The point in an injector's or scope's lifecycle at which a scope's eager bindings are instantiated. A scope impl
    with no eager instantiation point does not support eager bindings at all, and eagers on its bindings are rejected
    at element collection.
    """

    INJECTOR_INIT = enum.auto()
    SCOPE_OPEN = enum.auto()


class ScopeImpl(lang.Abstract, ta.Generic[ScopeT]):
    @classmethod
    @abc.abstractmethod
    def scope_cls(cls) -> type[ScopeT]:
        raise NotImplementedError

    @classmethod
    def eager_point(cls) -> EagerInstantiationPoint | None:
        return None

    @classmethod
    def auto_elements(cls, scope: ScopeT) -> Elements | None:  # noqa
        return None

    #

    def __init__(self, scope: ScopeT) -> None:
        super().__init__()

        self._scope = check.isinstance(scope, self.scope_cls())

    @property
    def scope(self) -> ScopeT:
        return self._scope

    @abc.abstractmethod
    def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Awaitable[ta.Any]:
        raise NotImplementedError


class UnscopedScopeImpl(ScopeImpl[Unscoped], lang.Final):
    @classmethod
    def scope_cls(cls) -> type[Unscoped]:
        return Unscoped

    @classmethod
    def eager_point(cls) -> EagerInstantiationPoint | None:
        return EagerInstantiationPoint.INJECTOR_INIT

    #

    async def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Any:
        return await binding.provider.provide(injector)


class SingletonScopeImpl(ScopeImpl[Singleton], lang.Final):
    @classmethod
    def scope_cls(cls) -> type[Singleton]:
        return Singleton

    @classmethod
    def eager_point(cls) -> EagerInstantiationPoint | None:
        return EagerInstantiationPoint.INJECTOR_INIT

    #

    def __init__(self, scope: Singleton) -> None:
        super().__init__(scope)

        self._om = OnceProvisionMap()

    async def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Any:
        return await self._om.provide(binding, injector)


class ThreadScopeImpl(ScopeImpl[ThreadScope], lang.Final):
    @classmethod
    def scope_cls(cls) -> type[ThreadScope]:
        return ThreadScope

    #

    def __init__(self, scope: ThreadScope) -> None:
        super().__init__(scope)

        self._local = threading.local()

    async def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Any:
        dct: dict[BindingImpl, ta.Any]
        try:
            dct = self._local.dct
        except AttributeError:
            dct = self._local.dct = {}
        try:
            return dct[binding]
        except KeyError:
            pass
        v = await binding.provider.provide(injector)
        dct[binding] = v
        return v


##


@dc.dataclass(frozen=True, eq=False)
class ScopeSeededProviderImpl(ProviderImpl):
    p: ScopeSeededProvider

    @property
    def providers(self) -> ta.Iterable[Provider]:
        return (self.p,)

    async def provide(self, injector: AsyncInjector) -> ta.Any:
        ii = check.isinstance(injector, _injector.AsyncInjectorImpl)
        ssi = check.isinstance(ii.get_scope_impl(self.p.ss), SeededScopeImpl)
        return ssi.must_state().seeds[self.p.key]


class SeededScopeImpl(ScopeImpl[SeededScope]):
    @classmethod
    def scope_cls(cls) -> type[SeededScope]:
        return SeededScope

    @classmethod
    def eager_point(cls) -> EagerInstantiationPoint | None:
        return EagerInstantiationPoint.SCOPE_OPEN

    @classmethod
    def auto_elements(cls, scope: SeededScope) -> Elements:
        return as_elements(
            Binding(
                as_key(SeededScope.Manager, tag=scope),
                FnProvider(lang.typed_partial(SeededScopeImpl.Manager, scope=scope)),
                scope=Singleton(),
            ),
        )

    #

    @dc.dataclass(frozen=True)
    class State:
        seeds: dict[Key, ta.Any]
        om: OnceProvisionMap = dc.field(default_factory=OnceProvisionMap)

    def __init__(self, scope: SeededScope) -> None:
        super().__init__(scope)

        self._st_mtx = threading.Lock()
        self._st: SeededScopeImpl.State | None = None

    def must_state(self) -> SeededScopeImpl.State:
        if (st := self._st) is None:
            raise ScopeNotOpenError(self._scope)
        return st

    class Manager(SeededScope.Manager, lang.Final):
        def __init__(self, scope: SeededScope, i: AsyncInjector) -> None:
            super().__init__()

            self._scope = check.isinstance(scope, SeededScope)
            self._ii = check.isinstance(i, _injector.AsyncInjectorImpl)
            self._ssi = check.isinstance(self._ii.get_scope_impl(self._scope), SeededScopeImpl)

        def __call__(self, seeds: ta.Mapping[Key, ta.Any]) -> ta.AsyncContextManager[None]:
            @contextlib.asynccontextmanager
            async def inner():
                with self._ssi._st_mtx:  # noqa
                    if self._ssi._st is not None:  # noqa
                        raise ScopeAlreadyOpenError(self._scope)
                    self._ssi._st = SeededScopeImpl.State(dict(seeds))  # noqa
                try:
                    await self._ii._instantiate_eagers(self._scope)  # noqa
                    yield
                finally:
                    with self._ssi._st_mtx:  # noqa
                        self._ssi._st = None  # noqa
            return inner()

    async def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Any:
        st = self.must_state()
        return await st.om.provide(binding, injector)


##


SCOPE_IMPLS: ta.Final[ta.Sequence[type[ScopeImpl]]] = [
    UnscopedScopeImpl,
    SingletonScopeImpl,
    ThreadScopeImpl,
    SeededScopeImpl,
]


SCOPE_IMPLS_BY_SCOPE: ta.Final[ta.Mapping[type[Scope], type[ScopeImpl]]] = {
    si.scope_cls(): si for si in SCOPE_IMPLS
}


def get_scope_impl(s: Scope) -> type[ScopeImpl]:
    try:
        return SCOPE_IMPLS_BY_SCOPE[type(s)]
    except KeyError:
        raise TypeError(s) from None


def make_scope_impl(s: Scope) -> ScopeImpl:
    return get_scope_impl(s)(s)
