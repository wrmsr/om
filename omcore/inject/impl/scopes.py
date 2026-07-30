import abc
import enum
import threading
import types
import typing as ta
import weakref

from ... import check
from ... import dataclasses as dc
from ... import lang
from ..bindings import Binding
from ..elements import Elements
from ..elements import as_elements
from ..errors import DeadInjectorError
from ..errors import ScopeAlreadyOpenError
from ..errors import ScopeFrozenError
from ..errors import ScopeNotOpenError
from ..injector import AsyncInjector
from ..keys import Key
from ..keys import as_key
from ..providers import FnProvider
from ..providers import Provider
from ..scopes import DelimitedScope
from ..scopes import DelimitedScopeContext
from ..scopes import DelimitedScopeStateStore
from ..scopes import ScopeSeededProvider
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
        ssi = check.isinstance(ii.get_scope_impl(self.p.ss), DelimitedScopeImpl)
        return ssi.must_state().seeds[self.p.key]


class _InjectorGlobalScopeContext(DelimitedScopeContext, lang.Singleton, lang.Final):
    """The default (`context=None`) policy: one opening at a time, injector-global - every thread and task sees it."""

    class _Store(DelimitedScopeStateStore, lang.Final):
        def __init__(self, scope: DelimitedScope) -> None:
            super().__init__()

            self._scope = scope
            self._mtx = threading.Lock()
            self._st: ta.Any | None = None

        def get(self) -> ta.Any | None:
            return self._st

        def open(self, state: ta.Any) -> ta.Any:
            with self._mtx:
                if self._st is not None:
                    raise ScopeAlreadyOpenError(self._scope)
                self._st = state
            return state

        def close(self, token: ta.Any) -> None:
            with self._mtx:
                self._st = None

    def make_state_store(self, scope: DelimitedScope) -> DelimitedScopeStateStore:
        return _InjectorGlobalScopeContext._Store(scope)


class DelimitedScopeImpl(ScopeImpl[DelimitedScope]):
    @classmethod
    def scope_cls(cls) -> type[DelimitedScope]:
        return DelimitedScope

    @classmethod
    def eager_point(cls) -> EagerInstantiationPoint | None:
        return EagerInstantiationPoint.SCOPE_OPEN

    @classmethod
    def auto_elements(cls, scope: DelimitedScope) -> Elements:
        return as_elements(
            Binding(
                as_key(DelimitedScope.Manager, tag=scope),
                FnProvider(lang.typed_partial(DelimitedScopeImpl.Manager, scope=scope)),
                scope=Singleton(),
            ),
        )

    #

    @dc.dataclass(eq=False)
    class State:
        seeds: dict[Key, ta.Any]
        om: OnceProvisionMap = dc.field(default_factory=OnceProvisionMap)
        frozen: bool = False

    def __init__(self, scope: DelimitedScope) -> None:
        super().__init__(scope)

        ctx: DelimitedScopeContext = scope.context if scope.context is not None else _InjectorGlobalScopeContext()
        self._store = ctx.make_state_store(scope)

    def must_state(self) -> DelimitedScopeImpl.State:
        if (st := self._store.get()) is None:
            raise ScopeNotOpenError(self._scope)
        return st

    def freeze(self) -> None:
        """
        Transitions the current opening - under a contextual policy, the current *context's* opening - to serve-only:
        provisions already made (or in flight) remain available, but further construction raises ScopeFrozenError.
        The freeze boundary is 'no new construction attempts', not a barrier - an in-flight construction at freeze
        time completes and serves. Lasts until the scope is exited; the next opening starts fresh.
        """

        self.must_state().frozen = True

    class Manager(DelimitedScope.Manager, lang.Final):
        def __init__(self, scope: DelimitedScope, i: AsyncInjector) -> None:
            super().__init__()

            self._scope = check.isinstance(scope, DelimitedScope)
            ii = check.isinstance(i, _injector.AsyncInjectorImpl)
            # Held weakly - the manager is cached in the injector's own singleton scope, and a strong ref would make
            # every delimited-scope-bearing injector a reference cycle.
            self._ii_ref: weakref.ref = weakref.ref(ii)
            self._ssi = check.isinstance(ii.get_scope_impl(self._scope), DelimitedScopeImpl)

        class _Entry:
            """
            Manual (non-generator) async contextmanager - scope entry is warm, and flat frames single-step
            better.
            """

            __slots__ = (
                '_mgr',
                '_seeds',
                '_tok',
            )

            _tok: ta.Any

            def __init__(self, mgr: DelimitedScopeImpl.Manager, seeds: ta.Mapping[Key, ta.Any] | None) -> None:
                self._mgr = mgr
                self._seeds = seeds

            async def __aenter__(self) -> None:
                mgr = self._mgr
                if (ii := mgr._ii_ref()) is None:  # noqa
                    raise DeadInjectorError

                self._tok = tok = mgr._ssi._store.open(DelimitedScopeImpl.State(dict(self._seeds or {})))  # noqa
                try:
                    await ii._instantiate_eagers(mgr._scope)  # noqa
                except BaseException:
                    mgr._ssi._store.close(tok)  # noqa
                    raise

            async def __aexit__(
                    self,
                    exc_type: type[BaseException] | None,
                    exc_val: BaseException | None,
                    exc_tb: types.TracebackType | None,
            ) -> None:
                self._mgr._ssi._store.close(self._tok)  # noqa

        def __call__(self, seeds: ta.Mapping[Key, ta.Any] | None = None) -> ta.AsyncContextManager[None]:
            return self._Entry(self, seeds)

    async def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Any:
        st = self.must_state()
        # The has/provide window is benign: freezing is meant for quiescent transition points, and the one race it
        # leaves - a pre-freeze construction failing after the check - correctly rejects the retry.
        if st.frozen and not st.om.has(binding):
            raise ScopeFrozenError(self._scope, binding.key)
        return await st.om.provide(binding, injector)


##


DEFAULT_SCOPES: ta.Final[ta.Sequence[Scope]] = [
    Unscoped(),
    Singleton(),
    ThreadScope(),
]


SCOPE_IMPLS: ta.Final[ta.Sequence[type[ScopeImpl]]] = [
    UnscopedScopeImpl,
    SingletonScopeImpl,
    ThreadScopeImpl,
    DelimitedScopeImpl,
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
