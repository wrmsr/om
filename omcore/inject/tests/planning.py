"""
Measurement demo for the (experimental, impl-level) provision-plan compiler - see impl/plans.py for the design and
tests/test_plans.py for semantic-parity coverage. Run:

  python -m omcore.inject.tests.planning
"""
import typing as ta

from ... import check
from ... import inject as inj
from ..impl.injector import AsyncInjectorImpl
from ..impl.plans import compile_provision_plan
from ..keys import as_key


##


def _main() -> None:
    from .bench.bench import _time_batch  # noqa
    from .bench.bench import chain_elements
    from .bench.bench import request_injector

    def rate(op: ta.Callable[[], ta.Any]) -> float:
        n = 1
        while _time_batch(op, n) < 20_000_000 and n < (1 << 20):
            n <<= 1
        return min(_time_batch(op, n) / n for _ in range(3))

    def fmt(ns: float) -> str:
        return f'{ns / 1_000:8.2f} µs'

    print(f'{"bench":34} {"interpreted":>12} {"planned":>12}')

    for n in (10, 100):
        els, head = chain_elements(n)
        ce = inj.collect_elements(inj.as_elements(*els))
        i = inj.create_injector(ce)
        ii = check.isinstance(i[inj.AsyncInjector], AsyncInjectorImpl)
        p = compile_provision_plan(ce, head)
        assert p.is_closed  # chains are hole-free: no mirroring tax
        assert i[head] == p.provide(ii) == n - 1
        print(f'{f"chain/{n}":34} {fmt(rate(lambda: i[head])):>12} {fmt(rate(lambda: p.provide(ii))):>12}')

    ss = inj.DelimitedScope('planning-req')
    ri, keys = request_injector(ss)
    rii = check.isinstance(ri[inj.AsyncInjector], AsyncInjectorImpl)
    rce = rii._ec  # noqa
    plans = [compile_provision_plan(rce, k) for k in keys]
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


if __name__ == '__main__':
    _main()
