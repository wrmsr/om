# ruff: noqa: SLF001
"""
EXPERIMENTAL: provision-plan compilation - a prototype of the 'shape / link / execute' layering discussed for the
'pre-generate, or cache, KT -> provision / injection action graph' TODO. Run the demo:

  python -m omcore.inject.tests.planning

The idea, in this prototype's terms:

- **Shape (EC-level, shareable)**: for a root key, statically resolve the *local* dependency closure against an
  ElementCollection's binding_impl_map and compile it to a tree of plain sync closures, with a slot-frame giving
  diamond deps request-memoization semantics for the closed portion. Locally-unbound keys (parent-bound, internal
  consts, seeds of other scopes, ...) become *holes*; unsupported dynamism (async providers, multis, privates,
  unrecognized provider impls) becomes holes too. This is a pure function of the EC - in a real integration it would
  be a weak-instance `cached_function` on ElementCollection, shared by every injector over it.

- **Link (nothing, by construction)**: plans take the executing injector as a *runtime parameter* - providers already
  do - so a plan closes over no injector (preserving the gc story) and one compiled plan serves every injector over
  the EC lineage, per-request children included.

- **Execute**: plan execution wraps itself in the real ambient-request guard, so every hole - which simply calls the
  real interpreter - joins the same request, keeping memoization and reentrancy coherent with interpreted semantics.
  Compiled values are (optionally) mirrored into the ambient request so interpreted holes see them. Scoped nodes
  peek/store the real scope impls' once-maps directly - experimental shortcut: this bypasses in-flight coalescing,
  so this prototype is single-context; a real integration would route misses through OnceProvisionMap properly.

Deliberate bail-outs, preserving full dynamic semantics: provision listeners (their value-replacement must wrap every
node, and their reentrant provisions need the ambient request - this prototype just detects them at execution and
falls back to full interpretation); anything provided by an unrecognized ProviderImpl; async subtrees. Compilation is
also where local cycles surface: a cyclic graph raises CyclicDependencyError at *compile* time, before any provision.
"""
import typing as ta

from ... import check
from ... import inject as inj
from ... import lang
from ..impl.elements import ElementCollection
from ..impl.injector import AsyncInjectorImpl
from ..impl.providers import CallableProviderImpl
from ..impl.providers import ConstProviderImpl
from ..impl.providers import LinkProviderImpl
from ..impl.provision import OnceProvisionMap
from ..impl.scopes import DelimitedScopeImpl
from ..impl.scopes import ScopeSeededProviderImpl
from ..impl.scopes import SingletonScopeImpl
from ..keys import Key
from ..keys import as_key
from ..scopes import DelimitedScope
from ..scopes import Singleton
from ..types import Unscoped


##


_MISSING = object()

# A node computes one key's value: (executing injector impl, slot frame, ambient request or None) -> value.
_Node = ta.Callable[[AsyncInjectorImpl, list, ta.Any], ta.Any]


class Plan(lang.Final):
    """A compiled provision plan for one root key over one ElementCollection."""

    def __init__(self, root_key: Key, root: _Node, n_slots: int, *, mirror: bool = True) -> None:
        super().__init__()

        self._root_key = root_key
        self._root = root
        self._n_slots = n_slots
        self._mirror = mirror

    @property
    def root_key(self) -> Key:
        return self._root_key

    def provide(self, i: ta.Any) -> ta.Any:
        if isinstance(i, AsyncInjectorImpl):
            ii = i
        else:
            ii = check.isinstance(i[inj.AsyncInjector], AsyncInjectorImpl)

        if not ii._is_initialized:
            lang.sync_await(ii._init())

        # Provision listeners wrap and may replace *every* provision - honoring that per-node is future work, so
        # their presence (theirs or any ancestor's) falls back to full interpretation. They cannot alter elements,
        # so the compiled shape remains *true* either way - this is purely a fast-path eligibility check.
        if ii._pls:
            return lang.sync_await(ii.provide(self._root_key))

        # The real ambient-request guard: holes (interpreted provisions) join this same request, keeping cross-hole
        # memoization and constructor reentrancy coherent with pure interpretation.
        with ii._current_request() as cr:
            frame = [_MISSING] * self._n_slots
            return self._root(ii, frame, cr if self._mirror else None)


##


class PlanCompiler(lang.Final):
    """
    Compiles root keys to Plans against one ElementCollection. Purely EC-derived - compiled plans are shared by every
    injector over the collection, with parent-bound keys left as interpreter holes.
    """

    def __init__(self, ec: ta.Any) -> None:
        super().__init__()

        self._ec = check.isinstance(inj.collect_elements(ec), ElementCollection)
        self._bim = self._ec.binding_impl_map()
        self._nodes: dict[Key, _Node] = {}
        self._visiting: set[Key] = set()
        self._n_slots = 0

    def compile(self, key: ta.Any, **plan_kwargs: ta.Any) -> Plan:
        k = as_key(key)
        return Plan(k, self._node(k), self._n_slots, **plan_kwargs)

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
            raise inj.CyclicDependencyError(key)

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
        def hole(ii, frame, cr, /):
            mv = lang.sync_await(ii._try_provide(key))
            if mv.present:
                return mv.must()
            if optional:
                return _MISSING
            raise inj.UnboundKeyError(key)
        return hole

    def _wrap_slot(self, key: Key, inner: _Node) -> _Node:
        # The slot frame is the compiled portion's request memoization: diamond deps within one plan execution share
        # one instance, exactly as interpreted request memoization would. Mirroring the value into the ambient
        # request (when enabled) extends that sharing to any interpreted holes that also need the key.
        idx = self._alloc_slot()

        def node(ii, frame, cr, /):
            if (v := frame[idx]) is not _MISSING:
                return v
            v = inner(ii, frame, cr)
            frame[idx] = v
            if cr is not None:
                cr._seen_keys.add(key)
                cr._provisions[key] = lang.just(v)
            return v
        return node

    def _wrap_scope(self, bi: ta.Any, inner: _Node) -> _Node:
        sc = bi.scope

        if isinstance(sc, Unscoped):
            return inner

        if isinstance(sc, Singleton):
            # EXPERIMENTAL shortcut: peek/store the real once-map directly. Correct single-context; a real
            # integration would route misses through OnceProvisionMap.provide for cross-context coalescing.
            def node(ii, frame, cr, /):
                om = ta.cast(SingletonScopeImpl, ii.get_scope_impl(sc))._om
                if isinstance(e := om._dct.get(bi), OnceProvisionMap._Done):
                    return e.v
                v = inner(ii, frame, cr)
                with om._mtx:
                    om._dct[bi] = OnceProvisionMap._Done(v)
                return v
            return node

        if isinstance(sc, DelimitedScope):
            def node(ii, frame, cr, /):
                ssi = ta.cast(DelimitedScopeImpl, ii.get_scope_impl(sc))
                st = ssi.must_state()
                om = st.om
                if isinstance(e := om._dct.get(bi), OnceProvisionMap._Done):
                    return e.v
                if st.frozen:
                    raise inj.ScopeFrozenError(sc, bi.key)
                v = inner(ii, frame, cr)
                with om._mtx:
                    om._dct[bi] = OnceProvisionMap._Done(v)
                return v
            return node

        # ThreadScope etc.: interpreter.
        return self._make_hole(bi.key, optional=False)


##


def compile_plan(es: ta.Any, key: ta.Any, **plan_kwargs: ta.Any) -> Plan:
    return PlanCompiler(es).compile(key, **plan_kwargs)


##
# Demo: verification against interpreted semantics, then measurement.


class _DemoLeaf:
    pass


class _DemoLeft:
    def __init__(self, leaf: _DemoLeaf) -> None:
        self.leaf = leaf


class _DemoRight:
    def __init__(self, leaf: _DemoLeaf) -> None:
        self.leaf = leaf


class _DemoRoot:
    def __init__(self, left: _DemoLeft, right: _DemoRight) -> None:
        self.left = left
        self.right = right


def _verify() -> None:
    ok: list[str] = []

    def chk(name: str, cond: bool) -> None:
        if not cond:
            raise AssertionError(name)
        ok.append(name)

    # Diamond sharing within one execution, fresh across executions - interpreted request-memo semantics:
    es = inj.as_elements(
        inj.bind(_DemoLeaf),
        inj.bind(_DemoLeft),
        inj.bind(_DemoRight),
        inj.bind(_DemoRoot),
    )
    ce = inj.collect_elements(es)
    i = inj.create_injector(ce)
    ii = i[inj.AsyncInjector]
    p = compile_plan(ce, _DemoRoot)
    r = p.provide(ii)
    chk('diamond shares within execution', r.left.leaf is r.right.leaf)
    chk('fresh across executions', p.provide(ii).left.leaf is not r.left.leaf)

    # Singleton cache shared both ways with the interpreter:
    # NOTE: plans must be compiled against the *same* ElementCollection the injector runs - BindingImpl identity
    # (eq=False) keys the scope caches, so re-collecting the same Elements yields foreign cache keys. The natural
    # home fixes this by construction: shapes as cached_functions *on* the EC.
    sce = inj.collect_elements(inj.as_elements(inj.bind(_DemoLeaf, singleton=True)))
    si = inj.create_injector(sce)
    sp = compile_plan(sce, _DemoLeaf)
    first = sp.provide(si[inj.AsyncInjector])
    chk('plan-filled singleton serves interpreter', si[_DemoLeaf] is first)

    # Delimited scope: per-opening caching, seeds, freeze - against the real scope impls:
    ss = inj.DelimitedScope('planning-demo')
    hels = inj.as_elements(
        inj.bind_scope(ss),
        inj.bind_scope_seed(float, ss),
        inj.bind(str, in_=ss, to_fn=inj.target(f=float)(lambda f: f'f={f}')),
        inj.bind(int, in_=ss, to_fn=inj.target()(lambda: 420)),
    )
    dce = inj.collect_elements(hels)
    di = inj.create_injector(dce)
    dii = di[inj.AsyncInjector]
    dp = compile_plan(dce, str)
    with inj.enter_scope(di, ss, {inj.as_key(float): 4.2}):
        v = dp.provide(dii)
        chk('seeded value', v == 'f=4.2')
        chk('cached per opening', dp.provide(dii) is v)
        chk('interpreter sees plan-filled scope cache', di[str] is v)
    with inj.enter_scope(di, ss, {inj.as_key(float): 5.2}):
        chk('fresh per opening', dp.provide(dii) == 'f=5.2')

    # Unbound and cyclic failure parity:
    try:
        compile_plan(inj.as_elements(
            inj.bind(str, to_fn=inj.target(x=int)(lambda x: '')),
            inj.bind(int, to_fn=inj.target(x=str)(lambda x: 0)),
        ), str)
    except inj.CyclicDependencyError:
        ok.append('cycle detected at compile time')
    else:
        raise AssertionError('cycle undetected')

    # Async providers and listener-bearing injectors: correct via fallback/holes:
    async def render(n: int) -> str:
        return f'#{n}'

    aes = inj.as_elements(inj.bind(420), inj.bind(render), inj.bind(float, to_fn=inj.target(s=str)(lambda s: 1.0)))
    ace = inj.collect_elements(aes)
    ai = inj.create_injector(ace)
    ap = compile_plan(ace, float)
    chk('async subtree served via hole', ap.provide(ai[inj.AsyncInjector]) == 1.0)

    async def exclaim(injector: ta.Any, key: ta.Any, binding: ta.Any, fn: ta.Any) -> ta.Any:
        v = await fn()
        return v + '!' if isinstance(v, str) else v

    les = inj.as_elements(inj.bind('hi'), inj.bind_provision_listener(exclaim))
    lce = inj.collect_elements(les)
    li = inj.create_injector(lce)
    lp = compile_plan(lce, str)
    chk('listeners fall back to interpretation', lp.provide(li[inj.AsyncInjector]) == 'hi!')

    # Parent delegation through holes - one shared plan over the child EC serves any child of any parent:
    pes = inj.as_elements(inj.bind(_DemoLeaf, singleton=True))
    cce = inj.collect_elements(inj.as_elements(inj.bind(_DemoLeft)))
    parent = inj.create_injector(pes)
    child = inj.create_injector(cce, parent=parent)
    cp = compile_plan(cce, _DemoLeft)
    chk('parent-bound dep via hole', cp.provide(child[inj.AsyncInjector]).leaf is parent[_DemoLeaf])

    print(f'verified: {len(ok)} checks')
    for name in ok:
        print(f'  ok: {name}')


def _measure() -> None:
    from .bench.bench import _time_batch
    from .bench.bench import chain_elements
    from .bench.bench import request_injector

    def rate(op: ta.Callable[[], ta.Any]) -> float:
        n = 1
        while _time_batch(op, n) < 20_000_000 and n < (1 << 20):
            n <<= 1
        return min(_time_batch(op, n) / n for _ in range(3))

    def fmt(ns: float) -> str:
        return f'{ns / 1_000:8.2f} µs'

    print()
    print(f'{"bench":34} {"interpreted":>12} {"planned":>12} {"planned-nomirror":>17}')

    for n in (10, 100):
        els, head = chain_elements(n)
        es = inj.as_elements(*els)
        ce = inj.collect_elements(es)
        i = inj.create_injector(ce)
        ii = check.isinstance(i[inj.AsyncInjector], AsyncInjectorImpl)
        pm = compile_plan(ce, head)
        pn = compile_plan(ce, head, mirror=False)
        assert i[head] == pm.provide(ii) == pn.provide(ii) == n - 1
        print(
            f'{f"chain/{n}":34}'
            f' {fmt(rate(lambda: i[head])):>12}'
            f' {fmt(rate(lambda: pm.provide(ii))):>12}'
            f' {fmt(rate(lambda: pn.provide(ii))):>17}',
        )

    ss = inj.DelimitedScope('planning-req')
    ri, keys = request_injector(ss)
    rii = check.isinstance(ri[inj.AsyncInjector], AsyncInjectorImpl)
    rce = rii._ec
    plans = [compile_plan(rce, k, mirror=False) for k in keys]
    seed_key = as_key(int, tag='req-seed')

    def interp_req() -> None:
        with inj.enter_scope(ri, ss, {seed_key: 7}):
            for k in keys:
                ri[k]

    def planned_req() -> None:
        with inj.enter_scope(ri, ss, {seed_key: 7}):
            for p in plans:
                p.provide(rii)

    with inj.enter_scope(ri, ss, {seed_key: 7}):
        assert [ri[k] for k in keys] == [p.provide(rii) for p in plans]
    print(f'{"scope/global/request-10":34} {fmt(rate(interp_req)):>12} {fmt(rate(planned_req)):>12}')


def _main() -> None:
    _verify()
    _measure()


if __name__ == '__main__':
    _main()
