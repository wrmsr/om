import abc
import contextlib
import threading
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...asyncs.asynclite import all as asl
from ..bindings import Binding
from ..elements import Elements
from ..elements import as_elements
from ..errors import CyclicDependencyError
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


if ta.TYPE_CHECKING:
    from . import injector as _injector
else:
    _injector = lang.proxy_import('.injector', __package__)


##


DEFAULT_PROVISION_WAIT_TIMEOUT_S: float = 60. * 60.


class _ProvisionWaitRegistry(lang.Final):
    """
    Global registry of cross-context provision waits, used to detect deadlocking dependency cycles spanning multiple
    provisioning contexts before those contexts block on each other. It must be global as cycles may span injectors
    and scopes. Only waits made through it are visible to detection - a wait-for path routing through IO or external
    synchronization is not, and remains backstopped only by wait timeouts.
    """

    def __init__(self) -> None:
        super().__init__()

        self._mtx = threading.Lock()  # guards _waits, held only for bookkeeping and walks - never while waiting
        self._waits: dict[tuple[int, ta.Any], _ProvisionWaitRegistry._Wait] = {}

    @dc.dataclass(frozen=True, eq=False)
    class _Wait:
        key: Key
        promise: asl.Promise
        target_owner: tuple[int, ta.Any]

    def _detect(
            self,
            owner: tuple[int, ta.Any],
            key: Key,
            target_owner: tuple[int, ta.Any],
    ) -> None:
        # Callers must hold _mtx. Since every wait-edge addition performs this check under the mutex, whichever
        # context adds the closing edge of a cycle is guaranteed to observe it.
        chain: list[Key] = [key]
        seen: set[tuple[int, ta.Any]] = {owner}
        cur = target_owner
        while True:
            if cur == owner:
                raise CyclicDependencyError(key, chain=tuple(chain))
            if cur in seen:
                return
            seen.add(cur)
            # A done promise's wait is already unwinding - treating it as absent keeps the walk conservative against
            # false positives from stale edges.
            if (w := self._waits.get(cur)) is None or w.promise.is_done():
                return
            chain.append(w.key)
            cur = w.target_owner

    @contextlib.contextmanager
    def waiting(
            self,
            owner: tuple[int, ta.Any],
            key: Key,
            promise: asl.Promise,
            target_owner: tuple[int, ta.Any],
    ) -> ta.Iterator[None]:
        with self._mtx:
            self._detect(owner, key, target_owner)
            check.not_in(owner, self._waits)  # an owner blocks on at most one wait at a time
            self._waits[owner] = _ProvisionWaitRegistry._Wait(key, promise, target_owner)

        try:
            yield
        finally:
            with self._mtx:
                del self._waits[owner]


_PROVISION_WAIT_REGISTRY = _ProvisionWaitRegistry()


class OnceProvisionMap(lang.Final):
    """
    Per-binding once-provisioning: the first arrival constructs, concurrent arrivals wait on a Promise. No lock is ever
    held across construction, so the wait-for graph can only follow dependency edges - which form a dag for any legal
    (acyclic) binding graph - making cross-context waits deadlock-free. Illegal cyclic graphs raced across contexts are
    caught eagerly by the wait registry rather than deadlocking. Failed construction attempts are not cached: each
    waiter of a failed attempt retries, potentially becoming the next constructor and raising its own error.
    """

    def __init__(self) -> None:
        super().__init__()

        self._mtx = threading.Lock()  # guards _dct only - must never be held across construction
        self._dct: dict[BindingImpl, OnceProvisionMap._Entry | OnceProvisionMap._Done] = {}

    @dc.dataclass(frozen=True, eq=False)
    class _Entry:
        promise: asl.Promise
        owner: tuple[int, ta.Any]

    @dc.dataclass(frozen=True, eq=False)
    class _Done:
        v: ta.Any

    async def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Any:
        # Unlocked fast path for the common already-constructed case.
        if isinstance(e := self._dct.get(binding), OnceProvisionMap._Done):
            return e.v

        ii = check.isinstance(injector, _injector.AsyncInjectorImpl)
        owner = ii._current_owner()  # noqa

        while True:
            with self._mtx:
                e = self._dct.get(binding)
                if isinstance(e, OnceProvisionMap._Done):
                    return e.v
                if e is None:
                    e = OnceProvisionMap._Entry(ii._al.make_promise(), owner)  # noqa
                    self._dct[binding] = e
                    mine = True
                else:
                    mine = False

            if mine:
                try:
                    v = await binding.provider.provide(injector)
                except BaseException as ex:
                    with self._mtx:
                        if self._dct.get(binding) is e:
                            del self._dct[binding]
                    e.promise.set_error(ex)
                    raise
                e.promise.set_value(v)
                # The full entry is then swapped for a minimal terminal record - the promise, its synchronization
                # machinery, and the owner identity all become garbage once any in-flight waiters drain.
                with self._mtx:
                    self._dct[binding] = OnceProvisionMap._Done(v)
                return v

            try:
                if e.promise.is_done():
                    return await e.promise.wait(timeout=DEFAULT_PROVISION_WAIT_TIMEOUT_S)

                # The registry raises CyclicDependencyError before waiting if this wait would close a cycle of
                # cross-context waits - including the single-hop case of a fresh request from the same thread and task
                # re-arriving mid-construction (eg. a Late invoked within its own constructor).
                with _PROVISION_WAIT_REGISTRY.waiting(owner, binding.key, e.promise, e.owner):
                    return await e.promise.wait(timeout=DEFAULT_PROVISION_WAIT_TIMEOUT_S)

            except asl.PromiseWaitTimeoutError:
                raise
            except BaseException:  # noqa
                if not e.promise.is_done():
                    raise  # this waiter itself was interrupted (eg. task cancellation) - not a failed construction
                # That construction attempt failed - loop and retry, potentially becoming the next constructor.


##


class ScopeImpl(lang.Abstract):
    @property
    @abc.abstractmethod
    def scope(self) -> Scope:
        raise NotImplementedError

    def auto_elements(self) -> Elements | None:
        return None

    @abc.abstractmethod
    def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Awaitable[ta.Any]:
        raise NotImplementedError


class UnscopedScopeImpl(ScopeImpl, lang.Final):
    @property
    def scope(self) -> Unscoped:
        return Unscoped()

    async def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Any:
        return await binding.provider.provide(injector)


class SingletonScopeImpl(ScopeImpl, lang.Final):
    def __init__(self) -> None:
        super().__init__()

        self._om = OnceProvisionMap()

    @property
    def scope(self) -> Singleton:
        return Singleton()

    async def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Any:
        return await self._om.provide(binding, injector)


class ThreadScopeImpl(ScopeImpl, lang.Final):
    def __init__(self) -> None:
        super().__init__()

        self._local = threading.local()

    @property
    def scope(self) -> ThreadScope:
        return ThreadScope()

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


class SeededScopeImpl(ScopeImpl):
    @dc.dataclass(frozen=True)
    class State:
        seeds: dict[Key, ta.Any]
        om: OnceProvisionMap = dc.field(default_factory=OnceProvisionMap)

    def __init__(self, ss: SeededScope) -> None:
        super().__init__()

        self._ss = check.isinstance(ss, SeededScope)
        self._st_mtx = threading.Lock()
        self._st: SeededScopeImpl.State | None = None

    @property
    def scope(self) -> SeededScope:
        return self._ss

    def must_state(self) -> SeededScopeImpl.State:
        if (st := self._st) is None:
            raise ScopeNotOpenError(self._ss)
        return st

    class Manager(SeededScope.Manager, lang.Final):
        def __init__(self, ss: SeededScope, i: AsyncInjector) -> None:
            super().__init__()

            self._ss = check.isinstance(ss, SeededScope)
            self._ii = check.isinstance(i, _injector.AsyncInjectorImpl)
            self._ssi = check.isinstance(self._ii.get_scope_impl(self._ss), SeededScopeImpl)

        def __call__(self, seeds: ta.Mapping[Key, ta.Any]) -> ta.AsyncContextManager[None]:
            @contextlib.asynccontextmanager
            async def inner():
                with self._ssi._st_mtx:  # noqa
                    if self._ssi._st is not None:  # noqa
                        raise ScopeAlreadyOpenError(self._ss)
                    self._ssi._st = SeededScopeImpl.State(dict(seeds))  # noqa
                try:
                    await self._ii._instantiate_eagers(self._ss)  # noqa
                    yield
                finally:
                    with self._ssi._st_mtx:  # noqa
                        self._ssi._st = None  # noqa
            return inner()

    def auto_elements(self) -> Elements:
        return as_elements(
            Binding(
                as_key(SeededScope.Manager, tag=self._ss),
                FnProvider(lang.typed_partial(SeededScopeImpl.Manager, ss=self._ss)),
                scope=Singleton(),
            ),
        )

    async def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Any:
        st = self.must_state()
        return await st.om.provide(binding, injector)


##


SCOPE_IMPLS_BY_SCOPE: dict[type[Scope], ta.Callable[..., ScopeImpl]] = {
    Unscoped: lambda _: UnscopedScopeImpl(),
    Singleton: lambda _: SingletonScopeImpl(),
    ThreadScope: lambda _: ThreadScopeImpl(),
    SeededScope: lambda s: SeededScopeImpl(s),
}


def make_scope_impl(s: Scope) -> ScopeImpl:
    try:
        fac = SCOPE_IMPLS_BY_SCOPE[type(s)]
    except KeyError:
        pass
    else:
        return fac(s)

    raise TypeError(s)
