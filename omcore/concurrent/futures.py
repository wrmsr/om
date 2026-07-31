import concurrent.futures as cf
import time
import typing as ta


T = ta.TypeVar('T')


##


class FutureError(Exception, ta.Generic[T]):
    def __init__(self, future: cf.Future, target: T | None = None) -> None:
        super().__init__()

        self._future = future
        self._target = target

    @property
    def future(self) -> cf.Future:
        return self._future

    @property
    def target(self) -> T | None:
        return self._target

    def __repr__(self) -> str:
        if self._future.cancelled():
            exception: BaseException | None = cf.CancelledError()
        elif self._future.done():
            exception = self._future.exception()
        else:
            exception = None

        return (
            f'{self.__class__.__qualname__}('
            f'exception={exception!r}, '
            f'future={self._future!r}, '
            f'target={self._target})'
        )

    __str__ = __repr__


class FutureTimeoutError(Exception):
    pass


def wait_futures(
        futures: ta.Sequence[cf.Future],
        *,
        timeout_s: float = 60,
        tick_interval_s: float = .5,
        tick_fn: ta.Callable[..., bool] = lambda: True,
        raise_exceptions: bool = False,
        cancel_on_exception: bool = False,
) -> bool:
    # TODO:
    #  - raise_exceptions 'at_end', ExceptionGroup
    #  - more responsive than tick_interval_s - semaphore, add callbacks to each fut to decrement, sleep with a timed
    #    wait on sem
    #  - cancel_on_timeout
    #  - obviate wait_all_futures_or_raise

    not_done = set(futures)
    if not not_done:
        return True

    start = time.monotonic()
    while tick_fn():
        done = {f for f in not_done if f.done()}
        if raise_exceptions:
            for fut in done:
                if fut.cancelled():
                    exc: BaseException | None = cf.CancelledError()
                else:
                    exc = fut.exception()
                if exc is not None:
                    if cancel_on_exception:
                        for cancel_fut in not_done:
                            cancel_fut.cancel()
                    raise FutureError(fut) from exc

        not_done -= done
        if not not_done:
            return True

        if time.monotonic() >= (start + timeout_s):
            raise FutureTimeoutError
        time.sleep(tick_interval_s)

    return False


def wait_all_futures_or_raise(futures: ta.Sequence[cf.Future]) -> None:
    done, not_done = cf.wait(futures, return_when=cf.ALL_COMPLETED)
    if not_done:
        raise RuntimeError(f'Not all futures finished: {not_done}')

    excs: list[Exception] = []
    for f in done:
        try:
            f.result()
        except Exception as e:  # noqa
            excs.append(e)

    if len(excs) == 1:
        raise excs[0]
    elif excs:
        raise ExceptionGroup('One or more futures failed', excs)


def wait_dependent_futures(
        executor: cf.Executor,
        dependency_sets_by_fn: ta.Mapping[ta.Callable, ta.AbstractSet[ta.Callable]],
        *,
        timeout_s: float = 60,
        tick_interval_s: float = .5,
        tick_fn: ta.Callable[..., bool] = lambda: True,
) -> ta.Mapping[ta.Callable, cf.Future]:
    for fn, deps in dependency_sets_by_fn.items():
        for dep in deps:
            if dep == fn:
                raise ValueError(fn)
            if dep not in dependency_sets_by_fn:
                raise KeyError(dep)
            if fn in dependency_sets_by_fn[dep]:
                raise Exception(f'Cyclic dependencies: {fn} <-> {dep}', fn, dep)

    dependent_sets_by_fn: dict[ta.Callable, set[ta.Callable]] = {fn: set() for fn in dependency_sets_by_fn}
    for fn, deps in dependency_sets_by_fn.items():
        for dep in deps:
            dependent_sets_by_fn[dep].add(fn)
    remaining_dep_sets_by_fn = {
        fn: set(dependencies) for fn, dependencies in dependency_sets_by_fn.items()
    }
    root_fns = {fn for fn, deps in remaining_dep_sets_by_fn.items() if not deps}
    fns_by_fut: dict[cf.Future, ta.Callable] = {}

    def cancel() -> None:
        for cancel_fut in fns_by_fut:
            cancel_fut.cancel()

    try:
        for fn in root_fns:
            if (fut := executor.submit(fn)) is not None:
                fns_by_fut[fut] = fn
    except BaseException:
        cancel()
        raise

    start = time.monotonic()
    not_done = set(fns_by_fut.keys())
    while not_done and tick_fn():
        done, not_done = cf.wait(not_done, timeout=tick_interval_s, return_when=cf.FIRST_COMPLETED)
        not_done = set(not_done)

        for fut in done:
            fn = fns_by_fut[fut]

            if fut.cancelled():
                exc: BaseException | None = cf.CancelledError()
            else:
                exc = fut.exception()
            if exc is not None:
                cancel()
                raise FutureError(fut, fn) from exc

            for dependent_fn in dependent_sets_by_fn.get(fn, set()):
                remaining_deps = remaining_dep_sets_by_fn[dependent_fn]
                remaining_deps.remove(fn)
                if not remaining_deps:
                    try:
                        downstream_fut = executor.submit(dependent_fn)
                    except BaseException:
                        cancel()
                        raise
                    if downstream_fut is not None:
                        fns_by_fut[downstream_fut] = dependent_fn
                        not_done.add(downstream_fut)

        if not_done and not all(fut.done() for fut in not_done) and time.monotonic() >= (start + timeout_s):
            cancel()
            raise FutureTimeoutError

    unprocessed_fns = {fns_by_fut[fut] for fut in not_done}
    remaining_fns = {
        fn: deps
        for fn, deps in remaining_dep_sets_by_fn.items()
        if deps or fn in unprocessed_fns
    }
    if remaining_fns:
        raise Exception(f'Unfinished fns: {remaining_fns}', remaining_fns)

    futs_by_fn = {fn: fut for fut, fn in fns_by_fut.items()}
    return futs_by_fn
