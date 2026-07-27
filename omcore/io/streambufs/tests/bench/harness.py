# ruff: noqa: UP006 UP045
# @om-lite
"""
A deliberately tiny, informal, DIY benchmark harness. Not wired into any test or verification machinery - modules using
it are meant to be run by hand (via `python -m ...`) to suss out relative costs and verify hotspot guesses.
"""
import gc
import time
import typing as ta


##


class BenchResult(ta.NamedTuple):
    name: str
    s_per_op: float
    ops: int
    bytes_per_op: ta.Optional[int]


def _time_n(fn: ta.Callable[[], ta.Any], n: int) -> float:
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        return time.perf_counter() - t0
    finally:
        if was_enabled:
            gc.enable()


def bench(
        name: str,
        fn: ta.Callable[[], ta.Any],
        *,
        bytes_per_op: ta.Optional[int] = None,
        target_time: float = .2,
        repeat: int = 3,
) -> BenchResult:
    fn()  # warmup

    # Calibrate iteration count to roughly target_time per repetition, timeit-style.
    n = 1
    while (t := _time_n(fn, n)) < (target_time / 10.) and n < (1 << 22):
        n *= 4
    if t > 0:
        n = max(1, min(int(n * target_time / t), 1 << 22))

    best = min(_time_n(fn, n) for _ in range(repeat))
    return BenchResult(name, best / n, n, bytes_per_op)


def fmt_time(s: float) -> str:
    if s < 1e-6:
        return f'{s * 1e9:8.1f} ns'
    elif s < 1e-3:
        return f'{s * 1e6:8.1f} us'
    elif s < 1.:
        return f'{s * 1e3:8.1f} ms'
    else:
        return f'{s:8.2f} s '


def report(
        title: str,
        results: ta.Sequence[BenchResult],
        *,
        baseline: ta.Optional[str] = None,
) -> None:
    """Print a table of results. Relative multiples are vs the named baseline, defaulting to the first result."""

    print()
    print(f'== {title}')

    base: ta.Optional[BenchResult] = None
    if results:
        if baseline is not None:
            base = next(r for r in results if r.name == baseline)
        else:
            base = results[0]

    nw = max([len(r.name) for r in results] + [4])
    for r in results:
        parts = [
            f'  {r.name:<{nw}}',
            fmt_time(r.s_per_op),
        ]

        if r.bytes_per_op is not None:
            mbs = r.bytes_per_op / r.s_per_op / 1e6
            parts.append(f'{mbs:10.1f} MB/s')

        if base is not None and base.s_per_op > 0:
            parts.append(f'{r.s_per_op / base.s_per_op:8.2f} x')

        print('  '.join(parts))
