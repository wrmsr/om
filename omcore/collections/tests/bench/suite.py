import argparse
import csv
import gc
import json
import platform
import statistics
import sys
import time
import tracemalloc
import typing as ta

from .... import dataclasses as dc
from .implementations import IMPLEMENTATIONS
from .interfaces import SUITES
from .interfaces import BenchmarkContext
from .interfaces import BenchmarkData
from .interfaces import Implementation
from .interfaces import resolve_suites
from .workloads import WORKLOADS
from .workloads import Trial
from .workloads import Workload
from .workloads import prepare_trial


##


@dc.dataclass(frozen=True)
class BenchmarkResult:
    implementation: str
    suite: str
    operation: str
    size: int
    cycles: int
    operations: int
    runtime_min_ns_per_op: float | None
    runtime_median_ns_per_op: float | None
    runtime_spread: float | None
    memory_retained_bytes: int | None
    memory_peak_bytes: int | None
    memory_retained_bytes_per_op: float | None
    memory_peak_bytes_per_op: float | None

    def as_dict(self) -> dict[str, ta.Any]:
        return dc.asdict(self)


@dc.dataclass(frozen=True)
class RunConfig:
    sizes: tuple[int, ...]
    suites: tuple[str, ...]
    implementations: tuple[str, ...]
    name_filter: str
    repeats: int
    target_operations: int
    max_cycles: int
    max_setup_items: int
    runtime: bool
    memory: bool


##


def _choose_cycles(workload: Workload, size: int, config: RunConfig) -> int:
    operations = workload.operation_count(size)
    cycles = max(1, min(config.max_cycles, config.target_operations // operations))
    if workload.setup_per_cycle:
        cycles = min(cycles, max(1, config.max_setup_items // size))
    return cycles


def _time_trial(trial: Trial) -> int:
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        started_ns = time.perf_counter_ns()
        result = trial.run()
        elapsed_ns = time.perf_counter_ns() - started_ns
        del result
        return elapsed_ns
    finally:
        if was_enabled:
            gc.enable()


def _measure_runtime(
        context: BenchmarkContext,
        workload: Workload,
        cycles: int,
        repeats: int,
) -> tuple[float, float, float, int]:
    samples: list[float] = []
    operations = 0
    for _ in range(repeats):
        gc.collect()
        trial = prepare_trial(context, workload, cycles)
        operations = trial.operations
        samples.append(_time_trial(trial) / operations)

    samples.sort()
    minimum = samples[0]
    median = statistics.median(samples)
    spread = samples[-1] / minimum if minimum else 0.
    return minimum, median, spread, operations


def _measure_memory(
        context: BenchmarkContext,
        workload: Workload,
) -> tuple[int, int, float, float]:
    gc.collect()
    trial = prepare_trial(context, workload, 1)
    gc.collect()

    def measure(run: ta.Callable[[], ta.Any]) -> tuple[int, int]:
        tracemalloc.start(1)
        try:
            before, _ = tracemalloc.get_traced_memory()
            result = run()
            current, peak = tracemalloc.get_traced_memory()
            del result
            return max(0, current - before), max(0, peak - before)
        finally:
            tracemalloc.stop()

    overhead_retained, overhead_peak = measure(lambda: None)
    retained, peak = measure(trial.run)
    retained = max(0, retained - overhead_retained)
    peak = max(retained, peak - overhead_peak)

    return (
        retained,
        peak,
        retained / trial.operations,
        peak / trial.operations,
    )


##


def _select_implementations(config: RunConfig) -> tuple[Implementation, ...]:
    selected: list[Implementation] = []
    for implementation in IMPLEMENTATIONS:
        if not implementation.available:
            continue
        if config.implementations and not any(
                name in implementation.name
                for name in config.implementations
        ):
            continue
        selected.append(implementation)
    return tuple(selected)


def _select_workloads(implementation: Implementation, config: RunConfig) -> tuple[Workload, ...]:
    supported = set(implementation.resolved_suites)
    if config.suites:
        enabled: set[str] = set()
        for suite in config.suites:
            if suite in supported:
                enabled.update(resolve_suites((suite,)))
    else:
        enabled = supported

    return tuple(workload for workload in WORKLOADS if workload.suite in enabled)


def _matches_filter(
        implementation: Implementation,
        workload: Workload,
        size: int,
        name_filter: str,
) -> bool:
    name = f'{implementation.name}/{workload.suite}/{workload.name}/{size}'
    return name_filter in name


@dc.dataclass(frozen=True)
class _BenchmarkParams:
    config: RunConfig
    implementation: Implementation
    size: int
    context: BenchmarkContext
    workload: Workload


def _run_benchmark(params: _BenchmarkParams) -> BenchmarkResult:
    cycles = _choose_cycles(
        params.workload,
        params.size,
        params.config,
    )

    runtime_min: float | None = None
    runtime_median: float | None = None
    runtime_spread: float | None = None
    operations = params.workload.operation_count(params.size)
    if params.config.runtime:
        (
            runtime_min,
            runtime_median,
            runtime_spread,
            operations,
        ) = _measure_runtime(
            params.context,
            params.workload,
            cycles,
            params.config.repeats,
        )

    memory_retained: int | None = None
    memory_peak: int | None = None
    memory_retained_per_op: float | None = None
    memory_peak_per_op: float | None = None
    if params.config.memory:
        (
            memory_retained,
            memory_peak,
            memory_retained_per_op,
            memory_peak_per_op,
        ) = _measure_memory(params.context, params.workload)

    return BenchmarkResult(
        implementation=params.implementation.name,
        suite=params.workload.suite,
        operation=params.workload.name,
        size=params.size,
        cycles=cycles,
        operations=operations,
        runtime_min_ns_per_op=runtime_min,
        runtime_median_ns_per_op=runtime_median,
        runtime_spread=runtime_spread,
        memory_retained_bytes=memory_retained,
        memory_peak_bytes=memory_peak,
        memory_retained_bytes_per_op=memory_retained_per_op,
        memory_peak_bytes_per_op=memory_peak_per_op,
    )


def run(config: RunConfig) -> ta.Iterator[BenchmarkResult]:
    runs: list[_BenchmarkParams] = []

    for implementation in _select_implementations(config):
        workloads = _select_workloads(implementation, config)
        for size in config.sizes:
            context = BenchmarkContext(implementation, BenchmarkData.make(size))
            for workload in workloads:
                if not _matches_filter(implementation, workload, size, config.name_filter):
                    continue

                runs.append(_BenchmarkParams(
                    config,
                    implementation,
                    size,
                    context,
                    workload,
                ))

    for params in runs:
        yield _run_benchmark(params)


##


def _format_ns(value: float | None) -> str:
    if value is None:
        return '-'
    if value < 1_000:
        return f'{value:.1f} ns'
    if value < 1_000_000:
        return f'{value / 1_000:.2f} us'
    return f'{value / 1_000_000:.2f} ms'


def _format_bytes(value: int | None) -> str:
    if value is None:
        return '-'
    if value < 1024:
        return f'{value} B'
    if value < 1024 * 1024:
        return f'{value / 1024:.1f} KiB'
    return f'{value / (1024 * 1024):.2f} MiB'


def _print_human_result(result: BenchmarkResult) -> None:
    noisy = ' !' if result.runtime_spread is not None and result.runtime_spread > 1.5 else ''
    name = f'{result.suite}/{result.operation}'
    print(
        f'{result.implementation:30} '
        f'{name:42} '
        f'n={result.size:<6} '
        f'min={_format_ns(result.runtime_min_ns_per_op):>10} '
        f'median={_format_ns(result.runtime_median_ns_per_op):>10} '
        f'peak={_format_bytes(result.memory_peak_bytes):>10}'
        f'{noisy}',
    )


def _print_json(results: ta.Sequence[BenchmarkResult]) -> None:
    print(json.dumps({
        'platform': platform.platform(),
        'python': platform.python_version(),
        'results': [result.as_dict() for result in results],
    }, indent=2))


def _print_csv(results: ta.Sequence[BenchmarkResult]) -> None:
    if not results:
        return
    rows = [result.as_dict() for result in results]
    writer = csv.DictWriter(sys.stdout, fieldnames=tuple(rows[0]))
    writer.writeheader()
    writer.writerows(rows)


def _print_implementations() -> None:
    for implementation in IMPLEMENTATIONS:
        status = 'available' if implementation.available else f'unavailable: {implementation.unavailable_reason}'
        print(
            f'{implementation.name:32} '
            f'{",".join(implementation.suites):42} '
            f'{implementation.key_kind.value:6} '
            f'{status}',
        )


##


def _parse_sizes(value: str) -> tuple[int, ...]:
    try:
        sizes = tuple(int(part) for part in value.split(','))
    except ValueError:
        raise argparse.ArgumentTypeError(value) from None
    if not sizes or any(size <= 0 for size in sizes):
        raise argparse.ArgumentTypeError(value)
    return sizes


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(value) from None
    if parsed <= 0:
        raise argparse.ArgumentTypeError(value)
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Benchmark omcore collection implementations by interface.')
    parser.add_argument('-k', '--filter', default='', help='substring filter over implementation/suite/operation/size')
    parser.add_argument('--sizes', type=_parse_sizes, default=(10, 100, 1000, 10_000))
    parser.add_argument('-s', '--suite', action='append', choices=tuple(SUITES), default=[])
    parser.add_argument('-i', '--implementation', action='append', default=[], help='implementation-name substring')
    parser.add_argument('--repeats', type=_positive_int, default=5)
    parser.add_argument('--target-operations', type=_positive_int, default=2048)
    parser.add_argument('--max-cycles', type=_positive_int, default=256)
    parser.add_argument('--max-setup-items', type=_positive_int, default=20_000)
    parser.add_argument('--fast', action='store_true', help='use fewer repetitions and target operations')
    measurement = parser.add_mutually_exclusive_group()
    measurement.add_argument('--runtime-only', action='store_true')
    measurement.add_argument('--memory-only', action='store_true')
    output = parser.add_mutually_exclusive_group()
    output.add_argument('-j', '--json', action='store_true', dest='as_json')
    output.add_argument('--csv', action='store_true', dest='as_csv')
    parser.add_argument('-l', '--list', action='store_true', dest='list_implementations')
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.list_implementations:
        _print_implementations()
        return

    repeats = 3 if args.fast else args.repeats
    target_operations = 256 if args.fast else args.target_operations
    max_setup_items = 2_000 if args.fast else args.max_setup_items

    config = RunConfig(
        sizes=args.sizes,
        suites=tuple(args.suite),
        implementations=tuple(args.implementation),
        name_filter=args.filter,
        repeats=repeats,
        target_operations=target_operations,
        max_cycles=args.max_cycles,
        max_setup_items=max_setup_items,
        runtime=not args.memory_only,
        memory=not args.runtime_only,
    )

    if not args.as_json and not args.as_csv:
        print(f'python {platform.python_version()} on {platform.platform()}')
        print('runtime is per logical operation; memory retained/peak is the one-cycle tracemalloc delta')

    results: list[BenchmarkResult] = []
    for result in run(config):
        results.append(result)
        if not args.as_json and not args.as_csv:
            _print_human_result(result)

    if args.as_json:
        _print_json(results)
    elif args.as_csv:
        _print_csv(results)


if __name__ == '__main__':
    main()
