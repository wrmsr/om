import contextlib
import contextvars
import functools
import itertools
import threading
import typing as ta
import weakref

from ... import check
from ... import lang
from ...asyncs.asynclite import all as asl
from ...logs import all as logs
from ..elements import CollectedElements
from ..errors import CyclicDependencyError
from ..errors import DeadInjectorError
from ..errors import UnboundKeyError
from ..injector import AsyncInjector
from ..inspect import KwargsTarget
from ..keys import Key
from ..keys import as_key
from ..listeners import ProvisionListener
from ..listeners import ProvisionListenerBinding
from ..scopes import Singleton
from ..scopes import ThreadScope
from ..types import Scope
from ..types import Unscoped
from .elements import ElementCollection
from .inspect import build_kwargs_target
from .scopes import DEFAULT_PROVISION_WAIT_TIMEOUT_S
from .scopes import ScopeImpl
from .scopes import make_scope_impl


log = logs.get_module_logger(globals())


##


DEFAULT_SCOPES: list[Scope] = [
    Unscoped(),
    Singleton(),
    ThreadScope(),
]


class Asynclite(
    asl.Promises,
    asl.Identities,
    lang.Intersection,
):
    pass


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
            al: Asynclite | None = None,
    ) -> None:
        self._ec = (ec := check.isinstance(ec, ElementCollection))
        self._p: AsyncInjectorImpl | None = check.isinstance(p, (AsyncInjectorImpl, None))

        if p is not None:
            check.none(al)
            self._al = p._al  # noqa
        else:
            self._al = check.not_none(al)

        self._internal_consts: dict[Key, ta.Any] = {
            as_key(AsyncInjector): self,
            **(internal_consts or {}),
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

        self._root: AsyncInjectorImpl = p._root if p is not None else self  # noqa

        self._scopes: dict[Scope, ScopeImpl] = {
            s: make_scope_impl(s)
            for s in itertools.chain(
                DEFAULT_SCOPES,
                ec.scope_binding_scopes(),
            )
        }

        self._init_mtx = threading.Lock()
        self._init_promise: asl.Promise[bool] | None = None
        self._init_owner: tuple[int, ta.Any] | None = None
        self._dead_error: BaseException | None = None

        if self._p is not None:
            self._p._add_child(self)  # noqa

    _al: Asynclite

    _cs: weakref.WeakSet[AsyncInjectorImpl] | None = None  # noqa

    #

    def _current_owner(self) -> tuple[int, ta.Any]:
        """Identifies the current provisioning context - the OS thread plus the backend's task identity, if any."""

        return (threading.get_ident(), self._al.current_identity())

    #

    async def _init(self) -> bool:
        with self._init_mtx:
            if (ip := self._init_promise) is None:
                ip = self._init_promise = self._al.make_promise()
                self._init_owner = self._current_owner()
                mine = True
            else:
                mine = False

        if not mine:
            if not ip.is_done() and self._init_owner == self._current_owner():
                return False  # a reentrant provide during this context's own eager instantiation
            await ip.wait(timeout=DEFAULT_PROVISION_WAIT_TIMEOUT_S)
            return False

        try:
            await self._instantiate_eagers(Unscoped())
            await self._instantiate_eagers(Singleton())
        except BaseException as e:
            # A failed init permanently kills the injector: the original error propagates to the initial creator, and
            # all other use - concurrent init waiters included - raises DeadInjectorError chained to it. The marker is
            # written before the init promise completes, so it is visible to anyone observing the promise as done.
            self._dead_error = e
            ip.set_value(True)
            self._init_owner = None  # never read once the init promise is done - only pins a thread / task identity
            raise

        ip.set_value(True)
        self._init_owner = None
        return True

    #

    _root: AsyncInjectorImpl

    async def _instantiate_eagers(self, sc: Scope) -> None:
        for k in self._ekbs.get(sc, ()):
            await self.provide(k)

    def get_scope_impl(self, sc: Scope) -> ScopeImpl:
        return self._scopes[sc]

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

        def __init__(self, owner: tuple[int, ta.Any]) -> None:
            super().__init__()

            self._owner = owner
            self._provisions: dict[Key, lang.Maybe] = {}
            self._seen_keys: set[Key] = set()
            self._source_stack: list[ta.Any] = []

        @property
        def owner(self) -> tuple[int, ta.Any]:
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

        @contextlib.contextmanager
        def push_source(self, source: ta.Any) -> ta.Iterator[None]:
            self._source_stack.append(source)
            try:
                yield
            finally:
                nsource = self._source_stack.pop()
                if source is not nsource:
                    raise Exception(f'Stack error: {source=} is not {nsource=}')

    @contextlib.contextmanager
    def _current_request(self) -> ta.Generator[_Request]:
        # A frame is only reused if it is this injector's and its request's owner matches the current context - a
        # request leaked in via context inheritance (a spawned task or thread) must not be shared, and is instead
        # shadowed by a fresh frame pushed at the head.
        head = _CURRENT_REQUEST_STACK.get()
        owner = self._current_owner()

        cur = head
        while cur is not None:
            if cur.injector_ref() is self and cur.request.owner == owner:
                yield cur.request
                return
            cur = cur.prev

        cr = self._Request(owner)
        tok = _CURRENT_REQUEST_STACK.set(_RequestFrame(weakref.ref(self), cr, head))
        try:
            yield cr
        finally:
            _CURRENT_REQUEST_STACK.reset(tok)

    async def _try_provide(self, key: ta.Any, *, source: ta.Any = None) -> lang.Maybe[ta.Any]:
        if (ip := self._init_promise) is None or not ip.is_done():
            await self._init()

        if (de := self._dead_error) is not None:
            raise DeadInjectorError from de

        key = as_key(key)

        cr: AsyncInjectorImpl._Request
        with self._current_request() as cr:
            with cr.push_source(source):
                if (rv := cr.handle_key(key)).present:
                    return rv.must()

                ic = self._internal_consts.get(key)
                if ic is not None:
                    return cr.handle_provision(key, lang.just(ic))

                bi = self._bim.get(key)
                if bi is not None:
                    sc = self._scopes[bi.scope]

                    fn = lambda: sc.provide(bi, self)  # noqa
                    for pl in self._pls:
                        fn = functools.partial(pl, self, key, bi.binding, fn)
                    v = await fn()

                    return cr.handle_provision(key, lang.just(v))

                if self._p is not None:
                    pv = await self._p._try_provide(key, source=source)  # noqa
                    if pv.present:
                        return cr.handle_provision(key, pv)

                return cr.handle_provision(key, lang.empty())

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
        ret: dict[str, ta.Any] = {}
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
        kws = await self.provide_kwargs(kt)
        # FIXME: still 'injecting' (as in has a req) if ctor needs and uses Injector
        return obj(**kws)


async def create_async_injector(ce: CollectedElements, p: AsyncInjector | None = None) -> AsyncInjector:
    i = AsyncInjectorImpl(
        ce,
        check.isinstance(p, (AsyncInjectorImpl, None)),
        al=ta.cast(ta.Any, asl.asyncio.All()) if p is None else None,
    )
    await i._init()  # noqa
    return i
