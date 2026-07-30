import contextvars
import functools
import itertools
import threading
import types
import typing as ta
import weakref

from ... import check
from ... import lang
from ...asyncs.asynclite import all as asl
from ..elements import CollectedElements
from ..errors import CyclicDependencyError
from ..errors import DeadInjectorError
from ..errors import ScopeAlreadyRegisteredError
from ..errors import ScopeEagerNonLocalError
from ..errors import ScopeNotRegisteredError
from ..errors import UnboundKeyError
from ..injector import AsyncInjector
from ..inspect import KwargsTarget
from ..keys import Key
from ..keys import as_key
from ..listeners import ProvisionListener
from ..listeners import ProvisionListenerBinding
from ..scopes import Singleton
from ..types import Scope
from ..types import Unscoped
from .concurrency import Concurrency
from .concurrency import ConcurrencyIdentity
from .elements import ElementCollection
from .inspect import build_kwargs_target
from .provision import DEFAULT_PROVISION_WAIT_TIMEOUT_S
from .scopes import DEFAULT_SCOPES
from .scopes import ScopeImpl
from .scopes import make_scope_impl


##


@ta.final
class _RequestFrame:
    """
    A node in the context-local stack of in-flight requests. Injectors are referenced weakly so contextvar residue
    (contexts captured mid-provision by spawned tasks or threads) never pins an injector - and through it its scoped
    instances.
    """

    def __init__(
            self,
            injector_ref: weakref.ref[AsyncInjectorImpl],
            request: AsyncInjectorImpl._Request,
            prev: _RequestFrame | None,
    ) -> None:
        super().__init__()

        self.injector_ref = injector_ref
        self.request = request
        self.prev = prev


# A single process-wide contextvar, per contextvars best practice. Contextvars are both task-local and thread-local,
# isolating concurrent provisions, and strict token-reset discipline leaves this empty between provisions in any given
# context - frames only outlive a provision in contexts captured mid-provision.
_CURRENT_REQUEST_STACK: contextvars.ContextVar[_RequestFrame | None] = contextvars.ContextVar(
    f'{__name__}._CURRENT_REQUEST_STACK',
    default=None,
)


@ta.final
class AsyncInjectorImpl(AsyncInjector, lang.Final):
    def __init__(
            self,
            ec: CollectedElements,
            p: AsyncInjectorImpl | None = None,
            *,
            internal_consts: dict[Key, ta.Any] | None = None,
            concurrency: Concurrency | None = None,
            weak_parent: bool = False,
    ) -> None:
        self._ec = (ec := check.isinstance(ec, ElementCollection))

        p = check.isinstance(p, (AsyncInjectorImpl, None))
        self._p: AsyncInjectorImpl | None
        self._p_ref: weakref.ref[AsyncInjectorImpl] | None
        if p is not None and weak_parent:
            # A private child is only reachable through its owner, so the owner strictly outlives every use of the
            # child - held weakly so the owner's singleton cache (which holds the child) doesn't form a cycle.
            self._p = None
            self._p_ref = weakref.ref(p)
        else:
            self._p = p
            self._p_ref = None

        if p is not None:
            check.none(concurrency)
            self._concurrency = p._concurrency  # noqa
        else:
            self._concurrency = check.not_none(concurrency)

        # Internal consts are held weakly: they are the injector itself and its facades, and strong entries would
        # make every injector a reference cycle. A dead ref (eg. a dropped sync facade whose async half outlived it)
        # is treated as absent.
        self._internal_consts: dict[Key, weakref.ref] = {
            as_key(AsyncInjector): weakref.ref(self),
            **{k: weakref.ref(v) for k, v in (internal_consts or {}).items()},
        }

        self._bim = ec.binding_impl_map()

        self._ekbs = ec.sorted_eager_keys_by_scope()

        self._pls: tuple[ProvisionListener, ...] = (
            *(
                b.listener
                for b in ec.elements_of_type(ProvisionListenerBinding)
            ),
            *(p._pls if p is not None else []),  # noqa
        )

        self._scopes: dict[Scope, ScopeImpl] = {
            s: make_scope_impl(s)
            for s in itertools.chain(
                DEFAULT_SCOPES,
                ec.scope_binding_scopes(),
            )
        }

        ancestor_scopes: set[Scope] = set()
        a: AsyncInjectorImpl | None = p
        while a is not None:
            ancestor_scopes.update(a._scopes)  # noqa
            a = a._parent()  # noqa

        # Scope redeclaration down the parent chain is forbidden: a child registering a scope an ancestor already has
        # would get its own independent state, silently shadowing the ancestor's - and 'overriding scopes' is not a
        # supported concept. Defaults count: every injector already carries them, so explicitly binding one in a
        # child is always a redeclaration.
        for s in ec.scope_binding_scopes():
            if s in ancestor_scopes:
                raise ScopeAlreadyRegisteredError(s)

        # A binding's scope must be registered locally or in an ancestor - children (privates included) may bind
        # *into* an ancestor's scope, provisioning into the owner's state (see get_scope_impl). A binding in a
        # never-registered scope is rejected here rather than dying with a raw KeyError at provision time, as with
        # unsupported eagers.
        for sc, sks in ec.keys_by_scope().items():
            if sc not in self._scopes and sc not in ancestor_scopes:
                raise ScopeNotRegisteredError(sc, next(iter(sks)))

        # Eagers, though, must be scope-local: a scope's eager instantiation point fires on the injector that owns
        # the scope (its init, or its openings), which cannot see descendants' eagers - an eager binding into an
        # ancestor's scope could never be honored, so it is rejected.
        for sc, ks in self._ekbs.items():
            if sc not in self._scopes:
                raise ScopeEagerNonLocalError(sc, ks[0])

        self._init_mtx = threading.Lock()
        self._is_initialized = False
        self._init_owner: ConcurrencyIdentity | None = None
        self._init_promise: asl.Promise[bool] | None = None  # lazily created by a contending context, under _init_mtx
        self._dead_error: BaseException | None = None

        if p is not None:
            p._add_child(self)  # noqa

    _concurrency: Concurrency

    _cs: weakref.WeakSet[AsyncInjectorImpl] | None = None  # noqa

    #

    async def _init(self) -> bool:
        my = self._concurrency.current_identity()

        ip: asl.Promise[bool] | None = None
        with self._init_mtx:
            if self._is_initialized:
                return False
            if (io := self._init_owner) is None:
                self._init_owner = my
                mine = True
            else:
                if io == my:
                    return False  # a reentrant provide during this context's own eager instantiation
                mine = False
                if (ip := self._init_promise) is None:
                    ip = self._init_promise = self._concurrency.make_promise()

        if not mine:
            ip = check.not_none(ip)  # always set on the waiter path
            await ip.wait(timeout=DEFAULT_PROVISION_WAIT_TIMEOUT_S)
            return False

        # Note: on both completion paths the promise slot must be read under the same lock acquisition that sets
        # _is_initialized - read separately, a contending context could create a promise just after the read and before
        # the flag flip, and it would never be completed.
        try:
            await self._instantiate_eagers(Unscoped())
            await self._instantiate_eagers(Singleton())
        except BaseException as e:
            # A failed init permanently kills the injector: the original error propagates to the initial creator, and
            # all other use - concurrent init waiters included - raises DeadInjectorError chained to it. The marker is
            # written before _is_initialized is set, so it is visible to anyone observing the injector as initialized.
            self._dead_error = e
            with self._init_mtx:
                self._is_initialized = True
                self._init_owner = None  # never read once initialized - only pins a thread / task identity
                ip = self._init_promise
            if ip is not None:
                ip.set_value(True)
            raise

        with self._init_mtx:
            self._is_initialized = True
            self._init_owner = None
            ip = self._init_promise
        if ip is not None:
            ip.set_value(True)
        return True

    #

    def _parent(self) -> AsyncInjectorImpl | None:
        if (pr := self._p_ref) is not None:
            if (p := pr()) is None:
                raise DeadInjectorError
            return p
        return self._p

    @property
    def root(self) -> AsyncInjectorImpl:
        i = self
        while (p := i._parent()) is not None:
            i = p
        return i

    async def _instantiate_eagers(self, sc: Scope) -> None:
        for k in self._ekbs.get(sc, ()):
            await self.provide(k)

    def get_scope_impl(self, sc: Scope) -> ScopeImpl:
        # Scope impls resolve up the parent chain: a scope is owned by the unique (per __init__'s redeclaration
        # check) injector that registered it, and a descendant binding into it provisions into the owner's state -
        # one opening spans the whole tree.
        i: AsyncInjectorImpl | None = self
        while i is not None:
            try:
                return i._scopes[sc]  # noqa
            except KeyError:
                i = i._parent()  # noqa
        raise ScopeNotRegisteredError(sc)

    def _add_child(self, c: AsyncInjectorImpl) -> AsyncInjector:
        check.isinstance(c, AsyncInjectorImpl)
        if self._cs is None:
            self._cs = weakref.WeakSet()
        self._cs.add(c)
        return c

    def _raise_error(self, e: Exception) -> ta.NoReturn:
        raise e

    class _Request:
        """Note: requests must never strongly reference their injector - see _RequestFrame."""

        def __init__(self, owner: ConcurrencyIdentity) -> None:
            super().__init__()

            self._owner = owner
            self._provisions: dict[Key, lang.Maybe] = {}
            self._seen_keys: set[Key] = set()
            self._source_stack: list[ta.Any] = []

        @property
        def owner(self) -> ConcurrencyIdentity:
            return self._owner

        def handle_key(self, key: Key) -> lang.Maybe[lang.Maybe]:
            try:
                return lang.just(self._provisions[key])
            except KeyError:
                pass
            if key in self._seen_keys:
                raise CyclicDependencyError(key)
            self._seen_keys.add(key)
            return lang.empty()

        def handle_provision(self, key: Key, mv: lang.Maybe) -> lang.Maybe:
            check.in_(key, self._seen_keys)
            check.not_in(key, self._provisions)
            self._provisions[key] = mv
            return mv

    class _RequestGuard:
        """
        Manual (non-generator) contextmanager for the ambient-request frame - this sits under every provision
        entrypoint, where generator-contextmanager machinery measurably matters (see tests/bench). `_try_provide`
        further inlines this logic wholesale; this class serves the coarser per-call entrypoints.

        A frame is only reused if it is this injector's and its request's owner matches the current context - a
        request leaked in via context inheritance (a spawned task or thread) must not be shared, and is instead
        shadowed by a fresh frame pushed at the head.
        """

        __slots__ = (
            '_injector',
            '_tok',
        )

        _tok: contextvars.Token | None

        def __init__(self, injector: AsyncInjectorImpl) -> None:
            self._injector = injector

        def __enter__(self) -> AsyncInjectorImpl._Request:
            i = self._injector
            head = _CURRENT_REQUEST_STACK.get()
            owner = i._concurrency.current_identity()  # noqa

            cur = head
            while cur is not None:
                if cur.injector_ref() is i and cur.request.owner == owner:
                    self._tok = None
                    return cur.request
                cur = cur.prev

            cr = AsyncInjectorImpl._Request(owner)
            self._tok = _CURRENT_REQUEST_STACK.set(_RequestFrame(weakref.ref(i), cr, head))
            return cr

        def __exit__(
                self,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: types.TracebackType | None,
        ) -> None:
            if (tok := self._tok) is not None:
                _CURRENT_REQUEST_STACK.reset(tok)

    def _current_request(self) -> _RequestGuard:
        return AsyncInjectorImpl._RequestGuard(self)

    async def _try_provide(self, key: ta.Any, *, source: ta.Any = None) -> lang.Maybe[ta.Any]:
        if not self._is_initialized:
            await self._init()

        if (de := self._dead_error) is not None:
            raise DeadInjectorError from de

        key = as_key(key)

        # The request-frame guard and source-stack push are inlined here rather than being contextmanagers of any
        # kind - this is the hottest path in the injector, and even manual-class contextmanager overhead measurably
        # matters (see tests/bench). Mirrors _RequestGuard exactly - keep the two in sync.
        head = _CURRENT_REQUEST_STACK.get()
        owner = self._concurrency.current_identity()

        cr: AsyncInjectorImpl._Request | None = None
        cur = head
        while cur is not None:
            if cur.injector_ref() is self and cur.request.owner == owner:
                cr = cur.request
                break
            cur = cur.prev

        tok = None
        if cr is None:
            cr = AsyncInjectorImpl._Request(owner)
            tok = _CURRENT_REQUEST_STACK.set(_RequestFrame(weakref.ref(self), cr, head))

        ss = cr._source_stack  # noqa
        ss.append(source)
        try:
            if (rv := cr.handle_key(key)).present:
                return rv.must()

            if (icr := self._internal_consts.get(key)) is not None and (ic := icr()) is not None:
                return cr.handle_provision(key, lang.just(ic))

            bi = self._bim.get(key)
            if bi is not None:
                # Compiled-plan fast path: plans are per-key caches on the (shared) ElementCollection, async-native
                # and correct under any concurrency - only listener-bearing injectors always interpret (listeners
                # wrap every provision). Sync-rooted plans complete without a coroutine.
                if not self._pls and (plan := self._ec.provision_plan(key)) is not None:
                    is_aw, v = plan._begin(self, cr, tok is None)  # noqa
                    if is_aw:
                        v = await v
                    if (mv := cr._provisions.get(key)) is not None:  # noqa  # mirroring plans mirror their own root
                        return mv
                    return cr.handle_provision(key, lang.just(v))

                sc = self.get_scope_impl(bi.scope)

                fn = lambda: sc.provide(bi, self)  # noqa
                for pl in self._pls:
                    fn = functools.partial(pl, self, key, bi.binding, fn)
                v = await fn()

                return cr.handle_provision(key, lang.just(v))

            if (pp := self._parent()) is not None:
                pv = await pp._try_provide(key, source=source)  # noqa
                if pv.present:
                    return cr.handle_provision(key, pv)

            return cr.handle_provision(key, lang.empty())

        finally:
            try:
                nsource = ss.pop()
                if source is not nsource:
                    raise Exception(f'Stack error: {source=} is not {nsource=}')
            finally:
                if tok is not None:
                    _CURRENT_REQUEST_STACK.reset(tok)

    async def _provide(self, key: ta.Any, *, source: ta.Any = None) -> ta.Any:
        v = await self._try_provide(key, source=source)
        if v.present:
            return v.must()
        self._raise_error(UnboundKeyError(key))
        raise RuntimeError  # noqa

    #

    def try_provide(self, key: ta.Any) -> ta.Awaitable[lang.Maybe[ta.Any]]:
        return self._try_provide(key)

    async def provide(self, key: ta.Any) -> ta.Any:
        v = await self._try_provide(key)
        if v.present:
            return v.must()
        self._raise_error(UnboundKeyError(key))
        raise RuntimeError  # noqa

    async def provide_kwargs(self, kt: KwargsTarget) -> ta.Mapping[str, ta.Any]:
        if not self._is_initialized:
            await self._init()

        # A single request spans all of the target's parameters - sibling provisions share memoization just as a
        # bound root's dependencies do.
        ret: dict[str, ta.Any] = {}
        with self._current_request():
            for kw in kt.kwargs:
                if kw.has_default:
                    if not (mv := await self._try_provide(kw.key, source=kt)).present:
                        continue
                    v = mv.must()
                else:
                    v = await self._provide(kw.key, source=kt)
                ret[kw.name] = v
        return ret

    async def inject(self, obj: ta.Any) -> ta.Any:
        if isinstance(obj, KwargsTarget):
            obj, kt = obj.obj, obj
        else:
            kt = build_kwargs_target(obj)

        if not self._is_initialized:
            await self._init()

        # The request also spans the injected call itself, so a constructor reentrantly using an injected Injector
        # joins it.
        with self._current_request():
            kws = await self.provide_kwargs(kt)
            return obj(**kws)


async def create_async_injector(
        ce: CollectedElements,
        p: AsyncInjector | None = None,
        *,
        concurrency: Concurrency | None = None,
        weak_parent: bool = False,
) -> AsyncInjector:
    i = AsyncInjectorImpl(
        ce,
        check.isinstance(p, (AsyncInjectorImpl, None)),
        concurrency=check.isinstance(concurrency, Concurrency) if concurrency is not None else None,
        weak_parent=weak_parent,
    )
    await i._init()  # noqa
    return i
