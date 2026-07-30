"""
Provision-plan compilation: the 'shape / link / execute' layering. Impl-level api.

A ProvisionPlan compiles one root key's *local* dependency closure - resolved statically against an
ElementCollection's binding impl map - into a tree of plain closures, with a per-execution slot frame giving the
closed portion request-memoization semantics (diamond deps share one instance). Locally-unresolvable keys (parent
bindings, internal consts such as the Injector itself, genuinely-unbound keys) and unsupported dynamism (async
providers, multis, privates, unrecognized provider impls, ThreadScope) compile to *holes*: calls into the real
interpreter, made semantics-preserving by executing the whole plan inside the real ambient-request guard so every
hole joins one request. Scoped nodes peek the real scope impls' once-maps and route misses back through
OnceProvisionMap.provide with the compiled subtree as the compute fn, keeping the once-protocol (at-most-one
construction, coalescing, failure retry) authoritative.

Plans are async-native, like the rest of the injector, and two-colored to stay fast: provably-suspension-free
subtrees compile to plain sync closures (a coroutine frame per node is most of the interpreter overhead plans
exist to remove), while nodes that may genuinely suspend - holes and scope wrappers, whose misses may await promise
coalescing, plus their ancestors - compile to async closures that await only where needed. The executor branches on
the root's color, so a sync-rooted plan (a pure computation chain, a const) executes with no coroutine at all, and
plans are correct under any concurrency - event-loop included - with no sync driving anywhere.

Plans are pure functions of the ElementCollection: the executing injector is a runtime parameter, so one compiled
plan serves every injector over the collection - per-request children included - and plans pin no injector. They must
be compiled against the *same* collection instance the injector runs (BindingImpl identity keys the scope caches).

Mirroring - making the compiled portion's values visible to (and readable from) the ambient request, so unscoped
values shared across the compiled/interpreted boundary stay one-instance-per-request - is decided at compile time
by plan closedness and at execution time by request sharedness: a *closed* plan (no holes) running in its own fresh
request provably has no other party to cohere with and skips it wholesale; an open plan, or any plan running within
a larger pre-existing request (reentrant provisions, per-param provisions under inject/provide_kwargs), pays a small
per-node tax for full bidirectional coherence.

Provision listeners are handled by fallback: they cannot alter elements, so the compiled shape stays true, but their
value-replacement wraps every provision - a plan executed on a listener-bearing injector (own or inherited) simply
runs fully interpreted. Constructors that reentrantly provide through a stashed injector mid-call are visible to the
interpreter but not to static analysis - the sanctioned reentrancy channel, injecting the Injector, is a hole and
behaves identically to interpretation.
"""
import typing as ta

from ... import check
from ... import lang
from ..elements import CollectedElements
from ..errors import CyclicDependencyError
from ..errors import ScopeFrozenError
from ..errors import UnboundKeyError
from ..injector import AsyncInjector
from ..keys import Key
from ..keys import as_key
from ..scopes import DelimitedScope
from ..scopes import Singleton
from ..types import Unscoped
from .providers import CallableProviderImpl
from .providers import ConstProviderImpl
from .providers import LinkProviderImpl
from .provision import OnceProvisionMap
from .scopes import DelimitedScopeImpl
from .scopes import ScopeSeededProviderImpl
from .scopes import SingletonScopeImpl


if ta.TYPE_CHECKING:
    from . import elements as _elements
    from . import injector as _injector
else:
    _elements = lang.proxy_import('.elements', __package__)
    _injector = lang.proxy_import('.injector', __package__)


##


class _MISSING(lang.Marker):
    pass


class _Node(ta.NamedTuple):
    """
    One compiled key: fn(executing injector impl, slot frame, ambient request or None). A sync node returns the
    value directly; an async node returns an awaitable of it - callers dispatch on `is_async`.
    """

    fn: ta.Callable[[ta.Any, list, ta.Any], ta.Any]
    is_async: bool


class ProvisionPlan(lang.Final):
    """A compiled provision plan for one root key over one ElementCollection."""

    def __init__(
            self,
            root_key: Key,
            root: _Node,
            n_slots: int,
            *,
            is_closed: bool = False,
            is_degenerate: bool = False,
    ) -> None:
        super().__init__()

        self._root_key = root_key
        self._root = root
        self._n_slots = n_slots
        self._is_closed = is_closed
        self._is_degenerate = is_degenerate

    @property
    def root_key(self) -> Key:
        return self._root_key

    @property
    def is_closed(self) -> bool:
        """Whether the plan compiled hole-free - closed plans in fresh requests skip ambient-request mirroring."""

        return self._is_closed

    @property
    def is_degenerate(self) -> bool:
        """
        Whether the root itself compiled to a hole - such a plan is just the interpreter with extra steps, and
        must never be installed as a fast path (a fast path that re-enters the interpreter would recurse).
        """

        return self._is_degenerate

    async def provide(self, i: AsyncInjector | ta.Any) -> ta.Any:
        if isinstance(i, _injector.AsyncInjectorImpl):
            ii = i
        else:
            ii = check.isinstance(i[AsyncInjector], _injector.AsyncInjectorImpl)

        if not ii._is_initialized:  # noqa
            await ii._init()  # noqa

        # Listener-bearing injectors (own or inherited) fall back to full interpretation - see module docstring.
        if ii._pls:  # noqa
            return await ii.provide(self._root_key)

        # The real ambient-request guard: holes (interpreted provisions) join this same request, keeping cross-hole
        # memoization and constructor reentrancy coherent with pure interpretation.
        with (rg := ii._current_request()) as cr:  # noqa
            is_aw, v = self._begin(ii, cr, rg._tok is None)  # noqa
            return (await v) if is_aw else v

    def _begin(self, ii: ta.Any, cr: ta.Any, shared: bool) -> tuple[bool, ta.Any]:
        """
        Starts an execution, returning (is_awaitable, value_or_awaitable) - sync-rooted plans complete right here,
        coroutine-free. Caller guarantees an initialized, listener-free injector with an ambient request active.
        `shared` is whether that request predates this execution (a reused frame): a plan running *within* a larger
        request must mirror regardless of its own closedness - the ambient request may already hold values for keys
        it covers, and its values may be needed by provisions after it - while a closed plan opening its own fresh
        request provably has no other party to cohere with.
        """

        frame: list = [_MISSING] * self._n_slots
        mcr = cr if (shared or not self._is_closed) else None
        root = self._root
        return root.is_async, root.fn(ii, frame, mcr)


##


class ProvisionPlanCompiler(lang.Final):
    """
    Compiles root keys to ProvisionPlans against one ElementCollection. Purely collection-derived - compiled plans
    are shared by every injector over the collection, with locally-unresolvable keys left as interpreter holes.
    """

    def __init__(self, ec: CollectedElements) -> None:
        super().__init__()

        self._ec = (ec := check.isinstance(ec, _elements.ElementCollection))
        self._bim = ec.binding_impl_map()
        self._nodes: dict[Key, _Node] = {}
        self._visiting: set[Key] = set()
        self._n_slots = 0
        self._has_holes = False
        self._hole_keys: set[Key] = set()

    def compile(self, key: ta.Any) -> ProvisionPlan:
        k = as_key(key)
        node = self._node(k)
        # Note: hole-tracking is compiler-wide, so a root compiled after another root introduced holes is
        # conservatively treated as open - the cost is only unnecessary mirror writes, never incoherence.
        return ProvisionPlan(
            k,
            node,
            self._n_slots,
            is_closed=not self._has_holes,
            is_degenerate=k in self._hole_keys,
        )

    ##

    def _alloc_slot(self) -> int:
        idx = self._n_slots
        self._n_slots += 1
        return idx

    def _node(self, key: Key) -> _Node:
        try:
            return self._nodes[key]
        except KeyError:
            pass

        # Local cycles surface at compile time - before any provision - rather than at first provision:
        if key in self._visiting:
            raise CyclicDependencyError(key)

        self._visiting.add(key)
        try:
            node = self._make_node(key)
        finally:
            self._visiting.discard(key)

        self._nodes[key] = node
        return node

    def _make_node(self, key: Key) -> _Node:
        if (bi := self._bim.get(key)) is None:
            # Not locally bound: parent bindings, internal consts (the Injector itself), and genuinely-unbound keys
            # all resolve - or fail, with the real errors - through the interpreter.
            return self._make_hole(key, optional=False)

        pi = bi.provider
        inner: _Node

        if isinstance(pi, ConstProviderImpl):
            v = pi.p.v

            def const_fn(ii, frame, cr, /, _v=v):  # noqa
                return _v

            inner = _Node(const_fn, False)

        elif isinstance(pi, LinkProviderImpl):
            inner = self._node(pi.p.k)

        elif isinstance(pi, CallableProviderImpl):
            kt = pi.kt
            entries: list[tuple[str, ta.Any, bool, bool]] = []
            for kw in kt.kwargs:
                optional = kw.has_default and self._bim.get(kw.key) is None
                dn = self._make_hole(kw.key, optional=True) if optional else self._node(kw.key)
                entries.append((kw.name, dn.fn, dn.is_async, optional))
            inner = self._make_call_node(kt.obj, entries)

        elif isinstance(pi, ScopeSeededProviderImpl):
            ss, skey = pi.p.ss, pi.p.key

            def seed_fn(ii, frame, cr, /, _ss=ss, _skey=skey):  # noqa
                ssi = ta.cast(DelimitedScopeImpl, ii.get_scope_impl(_ss))
                return ssi.must_state().seeds[_skey]

            inner = _Node(seed_fn, False)

        else:
            # AsyncCallableProviderImpl, multis, privates, and anything else unrecognized: full dynamism, via the
            # interpreter.
            return self._make_hole(key, optional=False)

        return self._wrap_scope(bi, self._wrap_slot(key, inner))

    def _make_call_node(self, obj: ta.Any, entries: list[tuple[str, ta.Any, bool, bool]]) -> _Node:
        ets = tuple(entries)

        if not any(is_a for _, _, is_a, _ in ets):
            def sync_call(ii, frame, cr, /, _obj=obj, _ets=ets):  # noqa
                kws = {}
                for name, fn, _, optional in _ets:
                    v = fn(ii, frame, cr)
                    if not optional or v is not _MISSING:
                        kws[name] = v
                return _obj(**kws)

            return _Node(sync_call, False)

        async def async_call(ii, frame, cr, /, _obj=obj, _ets=ets):  # noqa
            kws = {}
            for name, fn, is_a, optional in _ets:
                v = fn(ii, frame, cr)
                if is_a:
                    v = await v
                if not optional or v is not _MISSING:
                    kws[name] = v
            return _obj(**kws)

        return _Node(async_call, True)

    def _make_hole(self, key: Key, *, optional: bool) -> _Node:
        self._has_holes = True
        self._hole_keys.add(key)

        async def hole(ii, frame, cr, /):
            mv = await ii._try_provide(key)  # noqa
            if mv.present:
                return mv.must()
            if optional:
                return _MISSING
            raise UnboundKeyError(key)
        return _Node(hole, True)

    def _wrap_slot(self, key: Key, inner: _Node) -> _Node:
        # The slot frame is the compiled portion's request memoization: diamond deps within one plan execution share
        # one instance, exactly as interpreted request memoization would. With mirroring (cr not None), the ambient
        # request is read on slot miss and written on compute, extending that sharing across the compiled/interpreted
        # boundary in both directions.
        idx = self._alloc_slot()
        inner_fn = inner.fn

        if not inner.is_async:
            def sync_slot(ii, frame, cr, /):
                if (v := frame[idx]) is not _MISSING:
                    return v
                if cr is not None:
                    if (mv := cr._provisions.get(key)) is not None and mv.present:  # noqa
                        frame[idx] = v = mv.must()
                        return v
                v = inner_fn(ii, frame, cr)
                frame[idx] = v
                if cr is not None:
                    cr._seen_keys.add(key)  # noqa
                    cr._provisions[key] = lang.just(v)  # noqa
                return v

            return _Node(sync_slot, False)

        async def async_slot(ii, frame, cr, /):
            if (v := frame[idx]) is not _MISSING:
                return v
            if cr is not None:
                if (mv := cr._provisions.get(key)) is not None and mv.present:  # noqa
                    frame[idx] = v = mv.must()
                    return v
            v = await inner_fn(ii, frame, cr)
            frame[idx] = v
            if cr is not None:
                cr._seen_keys.add(key)  # noqa
                cr._provisions[key] = lang.just(v)  # noqa
            return v

        return _Node(async_slot, True)

    def _wrap_scope(self, bi: ta.Any, inner: _Node) -> _Node:
        # Scope nodes are async: their hit path never suspends, but a miss routes through the real once-protocol,
        # which may await promise coalescing under contention.
        sc = bi.scope

        if isinstance(sc, Unscoped):
            return inner

        inner_fn = inner.fn
        inner_async = inner.is_async

        def make_compute(ii: ta.Any, frame: list, cr: ta.Any) -> ta.Any:
            if inner_async:
                return lambda: inner_fn(ii, frame, cr)

            async def compute() -> ta.Any:
                return inner_fn(ii, frame, cr)
            return compute

        if isinstance(sc, Singleton):
            async def singleton_node(ii, frame, cr, /):
                om = ta.cast(SingletonScopeImpl, ii.get_scope_impl(sc))._om  # noqa
                if isinstance(e := om._dct.get(bi), OnceProvisionMap._Done):  # noqa
                    return e.v
                return await om.provide(bi, ii, make_compute(ii, frame, cr))
            return _Node(singleton_node, True)

        if isinstance(sc, DelimitedScope):
            async def delimited_node(ii, frame, cr, /):
                ssi = ta.cast(DelimitedScopeImpl, ii.get_scope_impl(sc))
                st = ssi.must_state()
                om = st.om
                if isinstance(e := om._dct.get(bi), OnceProvisionMap._Done):  # noqa
                    return e.v
                if st.frozen and not om.has(bi):
                    raise ScopeFrozenError(sc, bi.key)
                return await om.provide(bi, ii, make_compute(ii, frame, cr))
            return _Node(delimited_node, True)

        # ThreadScope etc.: interpreter.
        return self._make_hole(bi.key, optional=False)


##


def compile_provision_plan(ec: CollectedElements, key: ta.Any) -> ProvisionPlan:
    return ProvisionPlanCompiler(ec).compile(key)
