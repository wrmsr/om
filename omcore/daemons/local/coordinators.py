import abc
import enum
import threading
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ..runtime import Activity
from ..runtime import ActivityRejectedError
from ..runtime import ServiceRuntime
from .workers import LocalWorkerContext
from .workers import LocalWorkerRunner
from .workers import LocalWorkerSpec


T = ta.TypeVar('T')
R = ta.TypeVar('R')


##


class LocalWorkerState(enum.Enum):
    STOPPED = enum.auto()
    STARTING = enum.auto()
    RUNNING = enum.auto()
    STOPPING = enum.auto()
    FAILED = enum.auto()


@dc.dataclass(frozen=True, kw_only=True)
class LocalWorkerFailure:
    exception_type: str
    message: str

    @classmethod
    def of(cls, exc: BaseException) -> ta.Self:
        return cls(
            exception_type=f'{type(exc).__module__}.{type(exc).__qualname__}',
            message=str(exc),
        )


@dc.dataclass(frozen=True, kw_only=True)
class LocalWorkerInspection:
    worker: LocalWorkerSpec[ta.Any]
    state: LocalWorkerState
    generation: int

    thread_ident: int | None = None
    active_count: int = 0
    failure: LocalWorkerFailure | None = None
    coordinator_closed: bool = False

    @property
    def running(self) -> bool:
        return self.state is LocalWorkerState.RUNNING

    @property
    def stopped(self) -> bool:
        return self.state in (LocalWorkerState.STOPPED, LocalWorkerState.FAILED)


##


class LocalWorkerError(RuntimeError):
    pass


class LocalWorkerCoordinatorClosedError(LocalWorkerError):
    pass


class LocalWorkerPublicationError(LocalWorkerError):
    pass


class LocalWorkerUnexpectedExitError(LocalWorkerError):
    pass


class LocalWorkerDrainTimeoutError(LocalWorkerError, TimeoutError):
    pass


class LocalWorkerStopTimeoutError(LocalWorkerError, TimeoutError):
    pass


class LocalWorkerGenerationError(LocalWorkerError):
    def __init__(
            self,
            worker: LocalWorkerSpec[ta.Any],
            generation: int,
            cause: BaseException,
    ) -> None:
        super().__init__(f'Local worker generation {generation} failed: {worker!r}')

        self._worker = worker
        self._generation = generation
        self._cause = cause

    @property
    def worker(self) -> LocalWorkerSpec[ta.Any]:
        return self._worker

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def cause(self) -> BaseException:
        return self._cause


class LocalWorkerStartError(LocalWorkerGenerationError):
    pass


class LocalWorkerFailedError(LocalWorkerGenerationError):
    pass


##


class LocalWorkerLease(lang.Final, ta.Generic[T]):
    def __init__(
            self,
            *,
            worker: LocalWorkerSpec[T],
            generation: int,
            interface: T,
            activity: Activity,
    ) -> None:
        super().__init__()

        self._worker = worker
        self._generation = generation
        self._interface = interface
        self._activity = activity

    @property
    def worker(self) -> LocalWorkerSpec[T]:
        return self._worker

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def interface(self) -> T:
        return self._interface

    def close(self) -> bool:
        return self._activity.close()

    def __enter__(self) -> T:
        return self._interface

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


##


class LocalWorkerCoordinator(lang.Abstract):
    @abc.abstractmethod
    def acquire(
            self,
            worker: LocalWorkerSpec[T],
            *,
            timeout: lang.TimeoutLike = None,
    ) -> LocalWorkerLease[T]:
        raise NotImplementedError

    def call(
            self,
            worker: LocalWorkerSpec[T],
            fn: ta.Callable[[T], R],
            *,
            timeout: lang.TimeoutLike = None,
    ) -> R:
        with self.acquire(worker, timeout=timeout) as interface:
            return fn(interface)

    @abc.abstractmethod
    def inspect(self, worker: LocalWorkerSpec[ta.Any]) -> LocalWorkerInspection:
        raise NotImplementedError

    @abc.abstractmethod
    def request_shutdown(self, worker: LocalWorkerSpec[ta.Any]) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def wait_stopped(
            self,
            worker: LocalWorkerSpec[ta.Any],
            *,
            timeout: lang.TimeoutLike = None,
    ) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def shutdown(
            self,
            worker: LocalWorkerSpec[ta.Any],
            *,
            timeout: lang.TimeoutLike = 10.,
    ) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def close(self, *, timeout: lang.TimeoutLike = 10.) -> bool:
        raise NotImplementedError

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


##


_NOT_PUBLISHED = object()


class _Generation:
    def __init__(self, number: int) -> None:
        super().__init__()

        self.number = number

        self.thread: threading.Thread | None = None
        self.runtime: ServiceRuntime | None = None
        self.startup_activity: Activity | None = None

        self.interface: ta.Any = _NOT_PUBLISHED
        self.published = False
        self.stop_requested = False


class _Entry:
    def __init__(self, worker: LocalWorkerSpec[ta.Any]) -> None:
        super().__init__()

        self.worker = worker
        self.state = LocalWorkerState.STOPPED
        self.generation = 0
        self.current: _Generation | None = None

        self.last_thread_ident: int | None = None
        self.last_failure: BaseException | None = None
        self.last_published = False


##


class ThreadedLocalWorkerCoordinator(LocalWorkerCoordinator, lang.Final):
    def __init__(self) -> None:
        super().__init__()

        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)

        self._entries: dict[LocalWorkerSpec[ta.Any], _Entry] = {}
        self._threads: set[threading.Thread] = set()

        self._closing = False
        self._closed = False

    def _check_open_locked(self) -> None:
        if self._closing or self._closed:
            raise LocalWorkerCoordinatorClosedError('Local worker coordinator is closing or closed')

    def _entry_for_locked(self, worker: LocalWorkerSpec[ta.Any]) -> _Entry:
        try:
            return self._entries[worker]
        except KeyError:
            entry = self._entries[worker] = _Entry(worker)
            return entry

    def _prune_threads_locked(self) -> None:
        for thread in tuple(self._threads):
            if not thread.is_alive():
                thread.join()
                self._threads.remove(thread)

    def _start_entry_locked(self, entry: _Entry) -> _Generation:
        check.state(entry.state in (LocalWorkerState.STOPPED, LocalWorkerState.FAILED))
        check.none(entry.current)

        self._prune_threads_locked()

        generation = _Generation(entry.generation + 1)
        entry.generation = generation.number
        entry.current = generation
        entry.state = LocalWorkerState.STARTING
        entry.last_failure = None
        entry.last_published = False

        config = entry.worker.config
        thread = generation.thread = threading.Thread(
            target=self._run_generation,
            args=(entry, generation),
            name=config.thread_name or f'LocalWorker-{id(entry.worker):x}-{generation.number}',
            daemon=not config.keep_process_alive,
        )
        self._threads.add(thread)

        try:
            thread.start()
        except Exception as exc:  # noqa
            self._threads.remove(thread)
            entry.current = None
            entry.state = LocalWorkerState.FAILED
            entry.last_failure = exc
            self._condition.notify_all()

        return generation

    def _attach_runtime(
            self,
            entry: _Entry,
            generation: _Generation,
            runtime: ServiceRuntime,
            startup_activity: Activity,
    ) -> bool:
        with self._condition:
            check.is_(entry.current, generation)
            generation.runtime = runtime
            generation.startup_activity = startup_activity

            if generation.stop_requested or self._closing or self._closed:
                generation.stop_requested = True
                entry.state = LocalWorkerState.STOPPING
                runtime.shutdown.request(message='local-worker-coordinator-closing')
                self._condition.notify_all()
                return False

            self._condition.notify_all()
            return True

    def _publish(
            self,
            entry: _Entry,
            generation: _Generation,
            interface: ta.Any,
    ) -> None:
        with self._condition:
            if entry.current is not generation or entry.state is not LocalWorkerState.STARTING:
                raise LocalWorkerPublicationError('Local worker generation is no longer starting')
            if generation.published:
                raise LocalWorkerPublicationError('Local worker generation published more than once')

            generation.interface = interface
            generation.published = True
            entry.state = LocalWorkerState.RUNNING

            startup_activity = generation.startup_activity
            generation.startup_activity = None

        if startup_activity is not None:
            startup_activity.close()

        with self._condition:
            self._condition.notify_all()

    def _begin_stopping(
            self,
            entry: _Entry,
            generation: _Generation,
            runtime: ServiceRuntime,
    ) -> Activity | None:
        with self._condition:
            if entry.current is generation:
                generation.stop_requested = True
                entry.state = LocalWorkerState.STOPPING
                runtime.shutdown.request(message='local-worker-runner-exiting')

                startup_activity = generation.startup_activity
                generation.startup_activity = None

                self._condition.notify_all()
                return startup_activity

            return None

    def _finish_generation(
            self,
            entry: _Entry,
            generation: _Generation,
            failure: BaseException | None,
    ) -> None:
        with self._condition:
            if entry.current is generation:
                entry.current = None
                entry.last_thread_ident = check.not_none(generation.thread).ident
                entry.last_failure = failure
                entry.last_published = generation.published
                entry.state = LocalWorkerState.FAILED if failure is not None else LocalWorkerState.STOPPED
                self._condition.notify_all()

    def _run_generation(self, entry: _Entry, generation: _Generation) -> None:
        config = entry.worker.config
        runtime = ServiceRuntime(ServiceRuntime.Config(
            idle_timeout_s=config.linger_s,
            drain_timeout_s=config.drain_timeout_s,
            no_signals=True,
        ))
        failure: BaseException | None = None
        startup_activity: Activity | None = None

        try:
            startup_activity = runtime.activity.acquire()
            with runtime:
                try:
                    if self._attach_runtime(entry, generation, runtime, startup_activity):
                        runner = check.isinstance(entry.worker.runner_factory(), LocalWorkerRunner)
                        runner.run(LocalWorkerContext(
                            worker=entry.worker,
                            generation=generation.number,
                            runtime=runtime,
                            publish=lambda interface: self._publish(entry, generation, interface),
                        ))

                        if not runtime.shutdown.requested:
                            failure = LocalWorkerUnexpectedExitError(
                                'Local worker runner returned without a shutdown request',
                            )

                except BaseException as exc:  # noqa
                    failure = exc

                finally:
                    if (remaining_startup_activity := self._begin_stopping(
                            entry,
                            generation,
                            runtime,
                    )) is not None:
                        remaining_startup_activity.close()
                    startup_activity = None

                if not runtime.activity.wait_inactive(config.drain_timeout_s):
                    if failure is None:
                        failure = LocalWorkerDrainTimeoutError(
                            f'Local worker generation {generation.number} did not drain',
                        )

        except BaseException as exc:  # noqa
            if failure is None:
                failure = exc

        finally:
            if startup_activity is not None:
                startup_activity.close()
            self._finish_generation(entry, generation, failure)

    @staticmethod
    def _wait_locked(condition: threading.Condition, timeout: lang.Timeout) -> bool:
        if timeout.can_expire:
            if timeout.expired():
                return False
            condition.wait(timeout.remaining())
        else:
            condition.wait()
        return True

    @staticmethod
    def _raise_generation_failure(entry: _Entry) -> ta.NoReturn:
        failure = check.not_none(entry.last_failure)
        error_cls = LocalWorkerFailedError if entry.last_published else LocalWorkerStartError
        raise error_cls(entry.worker, entry.generation, failure) from failure

    def acquire(
            self,
            worker: LocalWorkerSpec[T],
            *,
            timeout: lang.TimeoutLike = None,
    ) -> LocalWorkerLease[T]:
        timeout_ = lang.Timeout.of(timeout)
        observed_generation: int | None = None

        while True:
            with self._condition:
                self._check_open_locked()
                entry = self._entry_for_locked(worker)

                if (
                        observed_generation is not None and
                        entry.generation == observed_generation and
                        entry.state in (LocalWorkerState.STOPPED, LocalWorkerState.FAILED)
                ):
                    if entry.last_failure is not None:
                        self._raise_generation_failure(entry)
                    observed_generation = None

                if entry.state in (LocalWorkerState.STOPPED, LocalWorkerState.FAILED):
                    generation = self._start_entry_locked(entry)
                    observed_generation = generation.number
                    if entry.state is LocalWorkerState.FAILED:
                        continue

                elif entry.state is LocalWorkerState.RUNNING:
                    generation = check.not_none(entry.current)
                    runtime = check.not_none(generation.runtime)
                    try:
                        activity = runtime.activity.acquire()
                    except (ActivityRejectedError, RuntimeError):
                        generation.stop_requested = True
                        entry.state = LocalWorkerState.STOPPING
                        runtime.shutdown.request(message='local-worker-activity-rejected')
                        observed_generation = generation.number
                        self._condition.notify_all()
                    else:
                        interface = generation.interface
                        check.state(interface is not _NOT_PUBLISHED)
                        return LocalWorkerLease(
                            worker=worker,
                            generation=generation.number,
                            interface=ta.cast(T, interface),
                            activity=activity,
                        )

                else:
                    generation = check.not_none(entry.current)
                    observed_generation = generation.number

                if not self._wait_locked(self._condition, timeout_):
                    raise TimeoutError(f'Timed out acquiring local worker: {worker!r}')

    def inspect(self, worker: LocalWorkerSpec[ta.Any]) -> LocalWorkerInspection:
        with self._condition:
            self._prune_threads_locked()
            entry = self._entry_for_locked(worker)
            generation = entry.current
            runtime = generation.runtime if generation is not None else None
            thread = generation.thread if generation is not None else None

            return LocalWorkerInspection(
                worker=worker,
                state=entry.state,
                generation=entry.generation,
                thread_ident=thread.ident if thread is not None else entry.last_thread_ident,
                active_count=runtime.activity.active_count if runtime is not None else 0,
                failure=LocalWorkerFailure.of(entry.last_failure) if entry.last_failure is not None else None,
                coordinator_closed=self._closing or self._closed,
            )

    def request_shutdown(self, worker: LocalWorkerSpec[ta.Any]) -> bool:
        startup_activity: Activity | None = None
        with self._condition:
            try:
                entry = self._entries[worker]
            except KeyError:
                return False

            if (generation := entry.current) is None:
                return False

            generation.stop_requested = True
            entry.state = LocalWorkerState.STOPPING
            if (runtime := generation.runtime) is not None:
                runtime.shutdown.request(message='local-worker-shutdown-requested')
            startup_activity = generation.startup_activity
            generation.startup_activity = None
            self._condition.notify_all()

        if startup_activity is not None:
            startup_activity.close()
        return True

    def wait_stopped(
            self,
            worker: LocalWorkerSpec[ta.Any],
            *,
            timeout: lang.TimeoutLike = None,
    ) -> bool:
        timeout_ = lang.Timeout.of(timeout)
        with self._condition:
            while True:
                try:
                    entry = self._entries[worker]
                except KeyError:
                    return True

                if entry.state in (LocalWorkerState.STOPPED, LocalWorkerState.FAILED):
                    return True

                if not self._wait_locked(self._condition, timeout_):
                    return False

    def shutdown(
            self,
            worker: LocalWorkerSpec[ta.Any],
            *,
            timeout: lang.TimeoutLike = 10.,
    ) -> bool:
        timeout_ = lang.Timeout.of(timeout)
        with self._condition:
            entry = self._entries.get(worker)
            thread = entry.current.thread if entry is not None and entry.current is not None else None

        requested = self.request_shutdown(worker)
        if not self.wait_stopped(worker, timeout=timeout_):
            raise LocalWorkerStopTimeoutError(f'Timed out stopping local worker: {worker!r}')

        if thread is not None and thread is not threading.current_thread():
            if timeout_.expired():
                raise LocalWorkerStopTimeoutError(f'Timed out joining local worker: {worker!r}')
            thread.join(timeout_.remaining_or(None))
            if thread.is_alive():
                raise LocalWorkerStopTimeoutError(f'Timed out joining local worker: {worker!r}')

        with self._condition:
            self._prune_threads_locked()
        return requested

    def close(self, *, timeout: lang.TimeoutLike = 10.) -> bool:
        timeout_ = lang.Timeout.of(timeout)
        startup_activities: list[Activity] = []

        with self._condition:
            if self._closed:
                return False
            self._closing = True

            for entry in self._entries.values():
                if (generation := entry.current) is None:
                    continue
                generation.stop_requested = True
                entry.state = LocalWorkerState.STOPPING
                if (runtime := generation.runtime) is not None:
                    runtime.shutdown.request(message='local-worker-coordinator-closing')
                if (startup_activity := generation.startup_activity) is not None:
                    generation.startup_activity = None
                    startup_activities.append(startup_activity)

            threads = tuple(self._threads)
            self._condition.notify_all()

        for activity in startup_activities:
            activity.close()

        for thread in threads:
            if thread is threading.current_thread():
                raise RuntimeError('Local worker coordinator cannot join its current worker thread')
            if timeout_.expired():
                raise LocalWorkerStopTimeoutError('Timed out closing local worker coordinator')
            thread.join(timeout_.remaining_or(None))
            if thread.is_alive():
                raise LocalWorkerStopTimeoutError('Timed out closing local worker coordinator')

        with self._condition:
            self._prune_threads_locked()
            self._closed = True
            self._condition.notify_all()
        return True
