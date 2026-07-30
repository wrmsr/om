"""
A DIY benchmarking / profiling suite for omcore.inject - there is no standardized internal benchmarking scaffold, so
this is deliberately belt-and-suspenders and self-contained. Run as a module:

  python -m omcore.inject.tests.bench.bench                # everything
  python -m omcore.inject.tests.bench.bench -k request     # name-filtered
  python -m omcore.inject.tests.bench.bench --fast         # quicker, noisier
  python -m omcore.inject.tests.bench.bench --json         # machine-readable results
  python -m omcore.inject.tests.bench.bench --profile provision/chain/100   # cProfile a bench, print hotspots

Latency benchmarks auto-calibrate iteration counts timeit-style (batches grown until they take long enough to trust),
run several batches with gc disabled, and report the *minimum* per-op time (least-noise estimator) alongside the
median and the max/min spread - a spread much above ~1.5x means a noisy run, rerun before believing it. Sync-facade
provisions are what's measured unless a bench says asyncio - that's the realistic common path, sync_await included.

Memory benchmarks report tracemalloc-measured *retained* bytes for built structures, and sys.getallocatedblocks
net-blocks-per-op leak checks for steady-state operations (expected ~0.0 - anything persistently positive is a leak).

Nothing here competes with anything; the point is a real number sense of the machinery's overhead, and a stable place
to catch regressions.
"""
import argparse
import asyncio
import contextvars
import cProfile
import gc
import json
import platform
import pstats
import statistics
import sys
import time
import tracemalloc
import typing as ta

from .... import inject as inj
from ...impl.elements import ElementCollection


##


class LatResult(ta.NamedTuple):
    name: str
    n: int
    min_ns: float
    median_ns: float
    spread: float


class LatBench(ta.NamedTuple):
    name: str
    make: ta.Callable[[], ta.Callable[[], ta.Any]]
    is_async: bool


LAT_BENCHES: list[LatBench] = []


def lat_bench(name: str, *, is_async: bool = False) -> ta.Callable[[ta.Callable], ta.Callable]:
    def install(fn: ta.Callable) -> ta.Callable:
        LAT_BENCHES.append(LatBench(name, fn, is_async))
        return fn
    return install


class MemBench(ta.NamedTuple):
    name: str
    fn: ta.Callable[[], ta.Any]  # returns (label, retained_bytes) pairs


MEM_BENCHES: list[MemBench] = []


def mem_bench(name: str) -> ta.Callable[[ta.Callable], ta.Callable]:
    def install(fn: ta.Callable) -> ta.Callable:
        MEM_BENCHES.append(MemBench(name, fn))
        return fn
    return install


##


def _time_batch(op: ta.Callable[[], ta.Any], n: int) -> int:
    was = gc.isenabled()
    gc.collect()
    gc.disable()
    try:
        t0 = time.perf_counter_ns()
        for _ in range(n):
            op()
        return time.perf_counter_ns() - t0
    finally:
        if was:
            gc.enable()


def _time_batch_async(op: ta.Callable[[], ta.Awaitable[ta.Any]], n: int) -> int:
    async def inner() -> int:
        was = gc.isenabled()
        gc.collect()
        gc.disable()
        try:
            t0 = time.perf_counter_ns()
            for _ in range(n):
                await op()
            return time.perf_counter_ns() - t0
        finally:
            if was:
                gc.enable()

    return asyncio.run(inner())


def run_lat_bench(b: LatBench, *, target_batch_ns: int, batches: int) -> LatResult:
    op = b.make()
    tb = _time_batch_async if b.is_async else _time_batch

    n = 1
    while tb(op, n) < target_batch_ns and n < (1 << 22):
        n <<= 1

    per_op = sorted(tb(op, n) / n for _ in range(batches))
    return LatResult(
        b.name,
        n,
        per_op[0],
        statistics.median(per_op),
        per_op[-1] / per_op[0] if per_op[0] else 0.,
    )


def measure_retained(fn: ta.Callable[[], ta.Any]) -> int:
    """Bytes retained by (all objects reachable from) fn's return value, per tracemalloc."""

    gc.collect()
    tracemalloc.start()
    try:
        before = tracemalloc.take_snapshot()
        obj = fn()
        gc.collect()
        after = tracemalloc.take_snapshot()
        total = sum(s.size_diff for s in after.compare_to(before, 'filename'))
        del obj
        return total
    finally:
        tracemalloc.stop()


def measure_leak_blocks(op: ta.Callable[[], ta.Any], n: int) -> float:
    """Net allocated-blocks change per op over n steady-state ops - expected ~0.0."""

    for _ in range(64):
        op()
    gc.collect()
    b0 = sys.getallocatedblocks()
    for _ in range(n):
        op()
    gc.collect()
    return (sys.getallocatedblocks() - b0) / n


##
# Fixtures. Binding graphs are generated: 'c' consts stand in for config-ish constants, 'svc' singletons for shared
# services, chains and fans for deep and wide dependency shapes, and the request fixtures model the web/llm loop this
# machinery exists for.


def const_elements(n: int) -> list:
    return [inj.bind(i, tag=('c', i)) for i in range(n)]


def chain_elements(n: int) -> tuple[list, ta.Any]:
    els: list = [inj.bind(0, tag=('ch', 0))]
    for i in range(1, n):
        els.append(inj.bind(
            inj.as_key(int, tag=('ch', i)),
            to_fn=inj.target(prev=inj.as_key(int, tag=('ch', i - 1)))(lambda prev: prev + 1),
        ))
    return els, inj.as_key(int, tag=('ch', n - 1))


def wide_elements(n: int) -> tuple[list, ta.Any]:
    els = const_elements(n)
    root = inj.as_key(int, tag='wide-root')
    els.append(inj.bind(
        root,
        to_fn=inj.target(**{f'a{i}': inj.as_key(int, tag=('c', i)) for i in range(n)})(lambda **kws: len(kws)),
    ))
    return els, root


def service_elements(n: int) -> list:
    els = const_elements(n)
    for i in range(n):
        els.append(inj.bind(
            inj.as_key(int, tag=('svc', i)),
            singleton=True,
            to_fn=inj.target(c=inj.as_key(int, tag=('c', i)))(lambda c: c * 2),
        ))
    return els


def collect_forced(es: ta.Any) -> ElementCollection:
    """Collects and pre-forces the collection's lazy caches - the 'warm EC' the pattern amortizes."""

    ec = inj.collect_elements(es)
    assert isinstance(ec, ElementCollection)
    ec.binding_impl_map()
    return ec


SEED_KEY = inj.as_key(int, tag='req-seed')


def handler_elements(n: int, *, n_svcs: int, in_: ta.Any = None, seeded: bool = True) -> tuple[list, list]:
    els: list = []
    keys: list = []
    for i in range(n):
        k = inj.as_key(int, tag=('h', i))
        keys.append(k)
        svc = inj.as_key(int, tag=('svc', i % n_svcs))
        if seeded:
            fn = inj.target(seed=SEED_KEY, svc=svc)(lambda seed, svc: seed + svc)
        else:
            fn = inj.target(svc=svc)(lambda svc: svc + 1)
        els.append(inj.bind(k, to_fn=fn, **({'in_': in_} if in_ is not None else {})))
    return els, keys


BENCH_VAR: contextvars.ContextVar = contextvars.ContextVar(f'{__name__}.BENCH_VAR')


def request_injector(ss: ta.Any) -> tuple[ta.Any, list]:
    hels, keys = handler_elements(10, n_svcs=20, in_=ss)
    i = inj.create_injector(
        *service_elements(20),
        inj.bind_scope(ss),
        inj.bind_scope_seed(SEED_KEY, ss),
        *hels,
    )
    return i, keys


##
# Creation: the ElementCollection is the precomputable half; injectors are meant to be relatively cheap to spin up
# from one. 'cold' includes collection, 'warm-ec' amortizes it.


def _install_creation_benches() -> None:
    for n in (10, 100, 1000):
        def make_collect(n: int = n) -> ta.Callable[[], ta.Any]:
            es = inj.as_elements(*const_elements(n))

            def op() -> None:
                collect_forced(es)
            return op

        lat_bench(f'create/collect-cold/{n}')(make_collect)

        def make_warm(n: int = n) -> ta.Callable[[], ta.Any]:
            ce = collect_forced(inj.as_elements(*const_elements(n)))

            def op() -> None:
                inj.create_injector(ce)
            return op

        lat_bench(f'create/injector-warm-ec/{n}')(make_warm)

        def make_cold(n: int = n) -> ta.Callable[[], ta.Any]:
            es = inj.as_elements(*const_elements(n))

            def op() -> None:
                inj.create_injector(es)
            return op

        lat_bench(f'create/injector-cold/{n}')(make_cold)


_install_creation_benches()


@lat_bench('create/child-warm-ec/100-parent')
def _bench_child_creation() -> ta.Callable[[], ta.Any]:
    parent = inj.create_injector(*const_elements(100))
    ce = collect_forced(inj.as_elements(*const_elements(3)))

    def op() -> None:
        inj.create_injector(ce, parent=parent)
    return op


@lat_bench('create/child-warm-ec/depth-16')
def _bench_deep_child_creation() -> ta.Callable[[], ta.Any]:
    ce = collect_forced(inj.as_elements(*const_elements(3)))
    p = inj.create_injector(*const_elements(10))
    for _ in range(16):
        p = inj.create_injector(ce, parent=p)

    def op() -> None:
        inj.create_injector(ce, parent=p)
    return op


##
# Provision: warm paths are per-op steady state; 'cold' includes injector creation and init.


@lat_bench('provision/const/warm')
def _bench_const_warm() -> ta.Callable[[], ta.Any]:
    i = inj.create_injector(*const_elements(100))
    k = inj.as_key(int, tag=('c', 50))

    def op() -> None:
        i[k]
    return op


@lat_bench('provision/singleton/warm-hit')
def _bench_singleton_warm() -> ta.Callable[[], ta.Any]:
    i = inj.create_injector(*service_elements(20))
    k = inj.as_key(int, tag=('svc', 10))
    i[k]

    def op() -> None:
        i[k]
    return op


@lat_bench('provision/singleton/cold-first')
def _bench_singleton_cold() -> ta.Callable[[], ta.Any]:
    ce = collect_forced(inj.as_elements(*service_elements(20)))
    k = inj.as_key(int, tag=('svc', 10))

    def op() -> None:
        inj.create_injector(ce)[k]
    return op


def _install_chain_benches() -> None:
    for n in (10, 100):
        def make(n: int = n) -> ta.Callable[[], ta.Any]:
            els, head = chain_elements(n)
            i = inj.create_injector(*els)
            assert i[head] == n - 1

            def op() -> None:
                i[head]
            return op

        lat_bench(f'provision/chain/{n}')(make)


_install_chain_benches()


@lat_bench('provision/wide/100')
def _bench_wide() -> ta.Callable[[], ta.Any]:
    els, root = wide_elements(100)
    i = inj.create_injector(*els)
    assert i[root] == 100

    def op() -> None:
        i[root]
    return op


@lat_bench('provision/kwargs/10')
def _bench_kwargs() -> ta.Callable[[], ta.Any]:
    i = inj.create_injector(*const_elements(10))
    kt = inj.target(**{f'a{j}': inj.as_key(int, tag=('c', j)) for j in range(10)})(lambda **kws: len(kws))
    assert len(i.provide_kwargs(kt)) == 10

    def op() -> None:
        i.provide_kwargs(kt)
    return op


def _install_parent_depth_benches() -> None:
    for d in (1, 4, 16):
        def make(d: int = d) -> ta.Callable[[], ta.Any]:
            ce = inj.collect_elements(inj.as_elements(inj.bind('leafy')))
            root = inj.create_injector(*const_elements(10))
            i = root
            for _ in range(d):
                i = inj.create_injector(ce, parent=i)
            k = inj.as_key(int, tag=('c', 5))
            assert i[k] == 5

            def op() -> None:
                i[k]
            return op

        lat_bench(f'provision/parent-depth/{d}')(make)


_install_parent_depth_benches()


@lat_bench('provision/miss/try_provide')
def _bench_miss() -> ta.Callable[[], ta.Any]:
    i = inj.create_injector(*const_elements(100))

    def op() -> None:
        i.try_provide(str)
    return op


##
# Scopes and request strategies - the three ways to do per-request state, side by side: an injector-global delimited
# scope, a contextvar-contextual one, and a child injector per request.


def _install_scope_benches() -> None:
    for label, ctx in [
        ('global', None),
        ('cv', inj.ContextVarScopeContext(BENCH_VAR)),
    ]:
        def make_empty(label: str = label, ctx: ta.Any = ctx) -> ta.Callable[[], ta.Any]:
            ss = inj.DelimitedScope(('bench-empty', label), context=ctx)
            i = inj.create_injector(inj.bind_scope(ss))

            def op() -> None:
                with inj.enter_scope(i, ss):
                    pass
            return op

        lat_bench(f'scope/{label}/cycle-empty')(make_empty)

        def make_request(label: str = label, ctx: ta.Any = ctx) -> ta.Callable[[], ta.Any]:
            ss = inj.DelimitedScope(('bench-req', label), context=ctx)
            i, keys = request_injector(ss)
            seeds = {SEED_KEY: 7}

            def op() -> None:
                with inj.enter_scope(i, ss, seeds):
                    for k in keys:
                        i[k]
            return op

        lat_bench(f'scope/{label}/request-10')(make_request)


_install_scope_benches()


@lat_bench('scope/child-per-request/precollected-10')
def _bench_child_request_precollected() -> ta.Callable[[], ta.Any]:
    # Seedless variant: the child EC is precollected once, handlers depend only on parent singletons.
    parent = inj.create_injector(*service_elements(20))
    hels, keys = handler_elements(10, n_svcs=20, seeded=False)
    ce = collect_forced(inj.as_elements(*hels))

    def op() -> None:
        c = inj.create_injector(ce, parent=parent)
        for k in keys:
            c[k]
    return op


@lat_bench('scope/child-per-request/recollect-10')
def _bench_child_request_recollect() -> ta.Callable[[], ta.Any]:
    # Seeded variant: the per-request seed is a fresh const binding, forcing re-collection every request - the honest
    # cost of seeding via elements rather than scope state.
    parent = inj.create_injector(*service_elements(20))
    hels, keys = handler_elements(10, n_svcs=20)
    hes = inj.as_elements(*hels)

    def op() -> None:
        c = inj.create_injector(hes, inj.bind(SEED_KEY, to_const=7), parent=parent)
        for k in keys:
            c[k]
    return op


@lat_bench('scope/seed/warm-hit')
def _bench_seed_hit() -> ta.Callable[[], ta.Any]:
    ss = inj.DelimitedScope('bench-seed')
    i = inj.create_injector(inj.bind_scope(ss), inj.bind_scope_seed(SEED_KEY, ss))
    cm = inj.enter_scope(i, ss, {SEED_KEY: 7})
    cm.__enter__()

    def op(_cm: ta.Any = cm) -> None:  # the default arg pins the deliberately-left-open cm for the bench's lifetime
        i[SEED_KEY]
    return op


@lat_bench('scope/thread/warm-hit')
def _bench_thread_hit() -> ta.Callable[[], ta.Any]:
    i = inj.create_injector(inj.bind(int, to_fn=inj.target()(lambda: 420), in_=inj.ThreadScope()))
    i[int]

    def op() -> None:
        i[int]
    return op


@lat_bench('scope/asyncio-cv/request-10', is_async=True)
def _bench_asyncio_request() -> ta.Callable[[], ta.Awaitable[ta.Any]]:
    # The flagship shape: create_asyncio_injector + contextvar scope, as a concurrent server would run it. Built
    # fresh per event loop via a lazy holder since injectors are loop-agnostic but the bench recreates loops.
    ss = inj.DelimitedScope('bench-aio', context=inj.ContextVarScopeContext(BENCH_VAR))
    hels, keys = handler_elements(10, n_svcs=20, in_=ss)
    es = inj.as_elements(
        *service_elements(20),
        inj.bind_scope(ss),
        inj.bind_scope_seed(SEED_KEY, ss),
        *hels,
    )
    holder: list = []

    async def op() -> None:
        if not holder:
            holder.append(await inj.create_asyncio_injector(es))
        i = holder[0]
        async with inj.async_enter_scope(i, ss, {SEED_KEY: 7}):
            for k in keys:
                await i.provide(k)
    return op


##
# Memory: tracemalloc-retained bytes for built structures, and net-allocated-blocks leak checks for steady state.


@mem_bench('retained')
def _mem_retained() -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []

    for n in (10, 100, 1000):
        es = inj.as_elements(*const_elements(n))

        def build_ec(es: ta.Any = es) -> ta.Any:
            return collect_forced(es)

        out.append((f'ec/{n}', float(measure_retained(build_ec))))

        ce = build_ec()

        def build_injector(ce: ta.Any = ce) -> ta.Any:
            return inj.create_injector(ce)

        out.append((f'injector-over-ec/{n}', float(measure_retained(build_injector))))

    parent = inj.create_injector(*const_elements(100))
    ce = collect_forced(inj.as_elements(*const_elements(3)))

    def build_children() -> ta.Any:
        return [inj.create_injector(ce, parent=parent) for _ in range(64)]

    out.append(('child-incremental (each, of 64)', measure_retained(build_children) / 64))

    return out


@mem_bench('leak-check (net blocks/op, ~0.0 expected)')
def _mem_leaks() -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []

    i = inj.create_injector(*const_elements(10))
    k = inj.as_key(int, tag=('c', 5))
    out.append(('provision/const/warm', measure_leak_blocks(lambda: i[k], 5000)))

    els, head = chain_elements(10)
    ic = inj.create_injector(*els)
    out.append(('provision/chain/10', measure_leak_blocks(lambda: ic[head], 2000)))

    for label, ctx in [
        ('global', None),
        ('cv', inj.ContextVarScopeContext(BENCH_VAR)),
    ]:
        ss = inj.DelimitedScope(('bench-leak', label), context=ctx)
        ir, keys = request_injector(ss)

        def op(ir: ta.Any = ir, ss: ta.Any = ss, keys: list = keys) -> None:
            with inj.enter_scope(ir, ss, {SEED_KEY: 7}):
                for kk in keys:
                    ir[kk]

        out.append((f'scope/{label}/request-10', measure_leak_blocks(op, 1000)))

    parent = inj.create_injector(*service_elements(20))
    hels, keys = handler_elements(10, n_svcs=20, seeded=False)
    cce = collect_forced(inj.as_elements(*hels))

    def child_op() -> None:
        c = inj.create_injector(cce, parent=parent)
        for kk in keys:
            c[kk]

    out.append(('scope/child-per-request-10', measure_leak_blocks(child_op, 1000)))

    return out


##


def _fmt_ns(ns: float) -> str:
    if ns < 1_000:
        return f'{ns:8.1f} ns'
    if ns < 1_000_000:
        return f'{ns / 1_000:8.2f} µs'
    return f'{ns / 1_000_000:8.2f} ms'


def _fmt_bytes(b: float) -> str:
    if abs(b) < 1024 * 1024:
        return f'{b / 1024:10.1f} KiB'
    return f'{b / (1024 * 1024):10.2f} MiB'


def _profile_bench(b: LatBench, *, target_batch_ns: int) -> None:
    op = b.make()
    tb = _time_batch_async if b.is_async else _time_batch
    n = 1
    while tb(op, n) < target_batch_ns and n < (1 << 22):
        n <<= 1

    print(f'\n== profile: {b.name} (n={n}) ==')
    pr = cProfile.Profile()
    if b.is_async:
        async def loop() -> None:
            for _ in range(n):
                await op()

        pr.enable()
        asyncio.run(loop())
        pr.disable()
    else:
        pr.enable()
        for _ in range(n):
            op()
        pr.disable()

    pstats.Stats(pr).strip_dirs().sort_stats('cumulative').print_stats(25)


def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-k', '--filter', default='', help='substring filter on bench names')
    ap.add_argument('--fast', action='store_true', help='smaller batches - quicker, noisier')
    ap.add_argument('--no-mem', action='store_true', help='skip memory benches')
    ap.add_argument('--json', action='store_true', dest='as_json', help='emit results as json')
    ap.add_argument('--profile', default='', metavar='FILTER', help='cProfile matching latency benches instead')
    args = ap.parse_args()

    target_batch_ns = 10_000_000 if args.fast else 50_000_000
    batches = 3 if args.fast else 5

    if args.profile:
        for b in LAT_BENCHES:
            if args.profile in b.name:
                _profile_bench(b, target_batch_ns=target_batch_ns)
        return

    lat_results: list[LatResult] = []
    mem_results: list[tuple[str, str, float]] = []

    if not args.as_json:
        print(f'python {platform.python_version()} on {platform.platform()}')

    group = ''
    for b in LAT_BENCHES:
        if args.filter not in b.name:
            continue
        r = run_lat_bench(b, target_batch_ns=target_batch_ns, batches=batches)
        lat_results.append(r)
        if not args.as_json:
            if (g := b.name.split('/')[0]) != group:
                group = g
                print(f'\n== {group} ==')
            noisy = '  !' if r.spread > 1.5 else ''
            print(f'{r.name:44} {_fmt_ns(r.min_ns)}/op   (median {_fmt_ns(r.median_ns).strip()}, x{r.spread:.2f}, n={r.n}){noisy}')  # noqa

    if not args.no_mem:
        for mb in MEM_BENCHES:
            rows = [(nm, v) for nm, v in mb.fn() if args.filter in nm]
            if rows and not args.as_json:
                print(f'\n== mem: {mb.name} ==')
            for nm, v in rows:
                mem_results.append((mb.name, nm, v))
                if not args.as_json:
                    if mb.name.startswith('leak'):
                        print(f'{nm:44} {v:10.3f} blocks/op')
                    else:
                        print(f'{nm:44} {_fmt_bytes(v)}')

    if args.as_json:
        print(json.dumps({
            'platform': platform.platform(),
            'python': platform.python_version(),
            'latency': [r._asdict() for r in lat_results],
            'memory': [{'bench': g, 'name': nm, 'value': v} for g, nm, v in mem_results],
        }, indent=2))


if __name__ == '__main__':
    _main()
