"""
Provision-plan compilation: the 'shape / link / execute' layering. Experimental, impl-level api.

A ProvisionPlan compiles one root key's *local* dependency closure - resolved statically against an
ElementCollection's binding impl map - into a tree of plain sync closures, with a per-execution slot frame giving the
closed portion request-memoization semantics (diamond deps share one instance). Locally-unresolvable keys (parent
bindings, internal consts such as the Injector itself, genuinely-unbound keys) and unsupported dynamism (async
providers, multis, privates, unrecognized provider impls, ThreadScope) compile to *holes*: calls into the real
interpreter, made semantics-preserving by executing the whole plan inside the real ambient-request guard so every
hole joins one request. Scoped nodes peek the real scope impls' once-maps and route misses back through
OnceProvisionMap.provide with the compiled subtree as the compute fn, keeping the once-protocol (at-most-one
construction, coalescing, failure retry) authoritative.

Plans are pure functions of the ElementCollection: the executing injector is a runtime parameter, so one compiled
plan serves every injector over the collection - per-request children included - and plans pin no injector. They must
be compiled against the *same* collection instance the injector runs (BindingImpl identity keys the scope caches).

Mirroring - making the compiled portion's values visible to (and readable from) the ambient request, so unscoped
values shared across the compiled/interpreted boundary stay one-instance-per-request - is a compile-time decision:
a *closed* plan (no holes) provably needs none and skips it wholesale; an open plan pays a small per-node tax for
full bidirectional coherence.

Provision listeners are handled by fallback: they cannot alter elements, so the compiled shape stays true, but their
value-replacement wraps every provision - a plan executed on a listener-bearing injector (own or inherited) simply
runs fully interpreted. Plans execute at sync-facade level (holes drive the interpreter via sync_await, exactly as
the sync facade does); constructors that reentrantly provide through a stashed injector mid-call are visible to the
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
from .elements import ElementCollection
from .injector import AsyncInjectorImpl
from .providers import CallableProviderImpl
from .providers import ConstProviderImpl
from .providers import LinkProviderImpl
from .provision import OnceProvisionMap
from .scopes import DelimitedScopeImpl
from .scopes import ScopeSeededProviderImpl
from .scopes import SingletonScopeImpl


##


class _MISSING(lang.Marker):
    pass


# A node computes one key's value: (executing injector impl, slot frame, ambient request or None) -> value.
_Node = ta.Callable[[AsyncInjectorImpl, list, ta.Any], ta.Any]


class ProvisionPlan(lang.Final):
    """A compiled provision plan for one root key over one ElementCollection."""

    def __init__(self, root_key: Key, root: _Node, n_slots: int, *, is_closed: bool = False) -> None:
        super().__init__()

        self._root_key = root_key
        self._root = root
        self._n_slots = n_slots
        self._is_closed = is_closed

    @property
    def root_key(self) -> Key:
        return self._root_key

    @property
    def is_closed(self) -> bool:
        """Whether the plan compiled hole-free - closed plans skip ambient-request mirroring entirely."""

        return self._is_closed

    def provide(self, i: AsyncInjector | ta.Any) -> ta.Any:
        if isinstance(i, AsyncInjectorImpl):
            ii = i
        else:
            ii = check.isinstance(i[AsyncInjector], AsyncInjectorImpl)

        if not ii._is_initialized:  # noqa
            lang.sync_await(ii._init())  # noqa

        # Listener-bearing injectors (own or inherited) fall back to full interpretation - see module docstring.
        if ii._pls:  # noqa
            return lang.sync_await(ii.provide(self._root_key))

        # The real ambient-request guard: holes (interpreted provisions) join this same request, keeping cross-hole
        # memoization and constructor reentrancy coherent with pure interpretation.
        with ii._current_request() as cr:  # noqa
            frame = [_MISSING] * self._n_slots
            return self._root(ii, frame, None if self._is_closed else cr)


##


class ProvisionPlanCompiler(lang.Final):
    """
    Compiles root keys to ProvisionPlans against one ElementCollection. Purely collection-derived - compiled plans
    are shared by every injector over the collection, with locally-unresolvable keys left as interpreter holes.
    """

    def __init__(self, ec: CollectedElements) -> None:
        super().__init__()

        self._ec = (ec := check.isinstance(ec, ElementCollection))
        self._bim = ec.binding_impl_map()
        self._nodes: dict[Key, _Node] = {}
        self._visiting: set[Key] = set()
        self._n_slots = 0
        self._has_holes = False

    def compile(self, key: ta.Any) -> ProvisionPlan:
        k = as_key(key)
        node = self._node(k)
        # Note: hole-tracking is compiler-wide, so a root compiled after another root introduced holes is
        # conservatively treated as open - the cost is only unnecessary mirror writes, never incoherence.
        return ProvisionPlan(k, node, self._n_slots, is_closed=not self._has_holes)

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
            return self._make_hole(key, optional=False)

        pi = bi.provider
        inner: _Node

        if isinstance(pi, ConstProviderImpl):
            v = pi.p.v

            def inner(ii, frame, cr, /, _v=v):  # noqa
                return _v

        elif isinstance(pi, LinkProviderImpl):
            inner = self._node(pi.p.k)

        elif isinstance(pi, CallableProviderImpl):
            kt = pi.kt
            entries: list[tuple[str, _Node, bool]] = []
            for kw in kt.kwargs:
                if kw.has_default and self._bim.get(kw.key) is None:
                    entries.append((kw.name, self._make_hole(kw.key, optional=True), True))
                else:
                    entries.append((kw.name, self._node(kw.key), False))
            obj = kt.obj

            def inner(ii, frame, cr, /, _obj=obj, _entries=tuple(entries)):  # noqa
                kws = {}
                for name, fn, optional in _entries:
                    v = fn(ii, frame, cr)
                    if not optional or v is not _MISSING:
                        kws[name] = v
                return _obj(**kws)

        elif isinstance(pi, ScopeSeededProviderImpl):
            ss, skey = pi.p.ss, pi.p.key

            def inner(ii, frame, cr, /, _ss=ss, _skey=skey):  # noqa
                ssi = ta.cast(DelimitedScopeImpl, ii.get_scope_impl(_ss))
                return ssi.must_state().seeds[_skey]

        else:
            # AsyncCallableProviderImpl, multis, privates, and anything else unrecognized: full dynamism, via the
            # interpreter.
            return self._make_hole(key, optional=False)

        return self._wrap_scope(bi, self._wrap_slot(key, inner))

    def _make_hole(self, key: Key, *, optional: bool) -> _Node:
        self._has_holes = True

        def hole(ii, frame, cr, /):
            mv = lang.sync_await(ii._try_provide(key))  # noqa
            if mv.present:
                return mv.must()
            if optional:
                return _MISSING
            raise UnboundKeyError(key)
        return hole

    def _wrap_slot(self, key: Key, inner: _Node) -> _Node:
        # The slot frame is the compiled portion's request memoization: diamond deps within one plan execution share
        # one instance, exactly as interpreted request memoization would. With mirroring (cr not None - open plans
        # only), the ambient request is read on slot miss and written on compute, extending that sharing across the
        # compiled/interpreted boundary in both directions.
        idx = self._alloc_slot()

        def node(ii, frame, cr, /):
            if (v := frame[idx]) is not _MISSING:
                return v
            if cr is not None:
                if (mv := cr._provisions.get(key)) is not None and mv.present:  # noqa
                    frame[idx] = v = mv.must()
                    return v
            v = inner(ii, frame, cr)
            frame[idx] = v
            if cr is not None:
                cr._seen_keys.add(key)  # noqa
                cr._provisions[key] = lang.just(v)  # noqa
            return v
        return node

    def _wrap_scope(self, bi: ta.Any, inner: _Node) -> _Node:
        sc = bi.scope

        if isinstance(sc, Unscoped):
            return inner

        if isinstance(sc, Singleton):
            def node(ii, frame, cr, /):
                om = ta.cast(SingletonScopeImpl, ii.get_scope_impl(sc))._om  # noqa
                if isinstance(e := om._dct.get(bi), OnceProvisionMap._Done):  # noqa
                    return e.v

                async def compute() -> ta.Any:
                    return inner(ii, frame, cr)

                return lang.sync_await(om.provide(bi, ii, compute))
            return node

        if isinstance(sc, DelimitedScope):
            def node(ii, frame, cr, /):
                ssi = ta.cast(DelimitedScopeImpl, ii.get_scope_impl(sc))
                st = ssi.must_state()
                om = st.om
                if isinstance(e := om._dct.get(bi), OnceProvisionMap._Done):  # noqa
                    return e.v
                if st.frozen and not om.has(bi):
                    raise ScopeFrozenError(sc, bi.key)

                async def compute() -> ta.Any:
                    return inner(ii, frame, cr)

                return lang.sync_await(om.provide(bi, ii, compute))
            return node

        # ThreadScope etc.: interpreter.
        return self._make_hole(bi.key, optional=False)


##


def compile_provision_plan(ec: CollectedElements, key: ta.Any) -> ProvisionPlan:
    return ProvisionPlanCompiler(ec).compile(key)
