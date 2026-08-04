"""
Measurement demo for the provision-plan compiler - see impl/plans.py for the design and tests/test_plans.py for
semantic-parity coverage. Run:

  python -m omcore.inject.tests.planning

Since the injector now consults plans automatically (per-key caches on the ElementCollection, gated on sync-drivable
concurrency and listener absence), the 'interpreted' baseline is produced by adding a passthrough provision listener -
listener-bearing injectors always interpret.
"""
import typing as ta

from ... import inject as inj
from .bench.suite import SEED_KEY
from .bench.suite import _time_batch  # noqa
from .bench.suite import chain_elements
from .bench.suite import handler_elements
from .bench.suite import service_elements


##


async def _passthrough_listener(injector: ta.Any, key: ta.Any, binding: ta.Any, fn: ta.Any) -> ta.Any:
    return await fn()


def _request_elements(ss: inj.DelimitedScope) -> tuple[ta.Any, list]:
    hels, keys = handler_elements(10, n_svcs=20, in_=ss)
    es = inj.as_elements(
        *service_elements(20),
        inj.bind_scope(ss),
        inj.bind_scope_seed(SEED_KEY, ss),
        *hels,
    )
    return es, keys


def _main() -> None:
    def rate(op: ta.Callable[[], ta.Any]) -> float:
        n = 1
        while _time_batch(op, n) < 20_000_000 and n < (1 << 20):
            n <<= 1
        return min(_time_batch(op, n) / n for _ in range(3))

    def fmt(ns: float) -> str:
        return f'{ns / 1_000:8.2f} µs'

    print(f'{"bench":34} {"interpreted":>12} {"auto-planned":>13}')

    for n in (10, 100):
        els, head = chain_elements(n)
        ip = inj.create_injector(*els, inj.bind_provision_listener(_passthrough_listener))
        i = inj.create_injector(*els)
        assert ip[head] == i[head] == n - 1
        print(f'{f"chain/{n}":34} {fmt(rate(lambda: ip[head])):>12} {fmt(rate(lambda: i[head])):>13}')

    ss = inj.DelimitedScope('planning-req')
    es, keys = _request_elements(ss)
    i = inj.create_injector(es)

    ssp = inj.DelimitedScope('planning-req-interp')
    esp, keysp = _request_elements(ssp)
    ip = inj.create_injector(esp, inj.bind_provision_listener(_passthrough_listener))

    def interp_req() -> None:
        with inj.enter_scope(ip, ssp, {SEED_KEY: 7}):
            for k in keysp:
                ip[k]

    def planned_req() -> None:
        with inj.enter_scope(i, ss, {SEED_KEY: 7}):
            for k in keys:
                i[k]

    with inj.enter_scope(i, ss, {SEED_KEY: 7}):
        vals = [i[k] for k in keys]
    with inj.enter_scope(ip, ssp, {SEED_KEY: 7}):
        assert [ip[k] for k in keysp] == vals

    print(f'{"scope/global/request-10":34} {fmt(rate(interp_req)):>12} {fmt(rate(planned_req)):>13}')


if __name__ == '__main__':
    _main()
