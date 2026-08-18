import abc
import math
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ..runtime import ServiceRuntime


T = ta.TypeVar('T')


##


@dc.dataclass(frozen=True, kw_only=True)
class LocalWorkerConfig:
    linger_s: float | None = 30.
    drain_timeout_s: float | None = 30.

    keep_process_alive: bool = False
    thread_name: str | None = None

    def __post_init__(self) -> None:
        for timeout_s in (self.linger_s, self.drain_timeout_s):
            if timeout_s is not None:
                check.arg(math.isfinite(timeout_s))
                check.arg(timeout_s > 0.)
        if self.thread_name is not None:
            check.non_empty_str(self.thread_name)


@dc.dataclass(frozen=True, eq=False, kw_only=True)
class LocalWorkerSpec(ta.Generic[T]):
    runner_factory: ta.Callable[[], LocalWorkerRunner[T]]
    config: LocalWorkerConfig = LocalWorkerConfig()

    def __post_init__(self) -> None:
        check.callable(self.runner_factory)
        check.isinstance(self.config, LocalWorkerConfig)


class LocalWorkerContext(lang.Final, ta.Generic[T]):
    def __init__(
            self,
            *,
            worker: LocalWorkerSpec[T],
            generation: int,
            runtime: ServiceRuntime,
            publish: ta.Callable[[T], None],
    ) -> None:
        super().__init__()

        self._worker = worker
        self._generation = generation
        self._runtime = runtime
        self._publish = publish

    @property
    def worker(self) -> LocalWorkerSpec[T]:
        return self._worker

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def runtime(self) -> ServiceRuntime:
        return self._runtime

    def publish(self, interface: T) -> None:
        self._publish(interface)


class LocalWorkerRunner(lang.Abstract, ta.Generic[T]):
    @abc.abstractmethod
    def run(self, ctx: LocalWorkerContext[T]) -> None:
        raise NotImplementedError


@dc.dataclass(frozen=True)
class FnLocalWorkerRunner(LocalWorkerRunner[T]):
    fn: ta.Callable[[LocalWorkerContext[T]], None]

    def run(self, ctx: LocalWorkerContext[T]) -> None:
        self.fn(ctx)
