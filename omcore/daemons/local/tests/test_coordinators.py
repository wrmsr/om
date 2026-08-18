import concurrent.futures
import threading

import pytest

from ...tests.testing import TEST_TIMEOUT_S
from .. import FnLocalWorkerRunner
from .. import LocalWorkerConfig
from .. import LocalWorkerContext
from .. import LocalWorkerCoordinatorClosedError
from .. import LocalWorkerRunner
from .. import LocalWorkerSpec
from .. import LocalWorkerStartError
from .. import LocalWorkerState
from .. import ThreadedLocalWorkerCoordinator
from .. import acquire_local_worker
from .. import call_local_worker
from .. import global_local_worker_coordinator


##


class _TestInterface:
    def __init__(
            self,
            generation: int,
            thread_ident: int,
            thread_daemon: bool,
    ) -> None:
        super().__init__()

        self.generation = generation
        self.thread_ident = thread_ident
        self.thread_daemon = thread_daemon


class _WorkerHarness:
    def __init__(
            self,
            *,
            fail_before_publish: set[int] | None = None,
            fail_after_release: dict[int, threading.Event] | None = None,
    ) -> None:
        super().__init__()

        self._fail_before_publish = fail_before_publish or set()
        self._fail_after_release = fail_after_release or {}

        self._lock = threading.Lock()
        self.factory_calls = 0
        self.interfaces: list[_TestInterface] = []

    def __call__(self) -> LocalWorkerRunner[_TestInterface]:
        with self._lock:
            self.factory_calls += 1
        return FnLocalWorkerRunner(self._run)

    def _run(self, ctx: LocalWorkerContext[_TestInterface]) -> None:
        if ctx.generation in self._fail_before_publish:
            raise RuntimeError(f'start failure {ctx.generation}')

        thread = threading.current_thread()
        interface = _TestInterface(
            ctx.generation,
            threading.get_ident(),
            thread.daemon,
        )
        with self._lock:
            self.interfaces.append(interface)
        ctx.publish(interface)

        if (release := self._fail_after_release.get(ctx.generation)) is not None:
            if not release.wait(TEST_TIMEOUT_S):
                raise TimeoutError('Test did not release local worker failure')
            raise RuntimeError(f'run failure {ctx.generation}')

        if ctx.runtime.shutdown.wait(TEST_TIMEOUT_S) is None:
            raise TimeoutError('Test local worker did not receive shutdown')


def _worker(
        harness: _WorkerHarness,
        *,
        linger_s: float | None = None,
        keep_process_alive: bool = False,
) -> LocalWorkerSpec[_TestInterface]:
    return LocalWorkerSpec(
        runner_factory=harness,
        config=LocalWorkerConfig(
            linger_s=linger_s,
            drain_timeout_s=TEST_TIMEOUT_S,
            keep_process_alive=keep_process_alive,
        ),
    )


##


def test_concurrent_acquisitions_share_one_worker_generation() -> None:
    num_callers = 8
    harness = _WorkerHarness()
    worker = _worker(harness)
    coordinator = ThreadedLocalWorkerCoordinator()
    acquired = threading.Barrier(num_callers + 1)
    release = threading.Event()
    interfaces: list[_TestInterface] = []
    interfaces_lock = threading.Lock()

    def call() -> None:
        with coordinator.acquire(worker, timeout=TEST_TIMEOUT_S) as interface:
            with interfaces_lock:
                interfaces.append(interface)
            acquired.wait(TEST_TIMEOUT_S)
            assert release.wait(TEST_TIMEOUT_S)

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_callers) as executor:
            futures = [executor.submit(call) for _ in range(num_callers)]
            try:
                acquired.wait(TEST_TIMEOUT_S)
                assert harness.factory_calls == 1
                assert len(interfaces) == num_callers
                assert all(interface is interfaces[0] for interface in interfaces)
                assert interfaces[0].thread_ident != threading.get_ident()

                inspection = coordinator.inspect(worker)
                assert inspection.state is LocalWorkerState.RUNNING
                assert inspection.generation == 1
                assert inspection.active_count == num_callers
            finally:
                release.set()

            for future in futures:
                future.result(TEST_TIMEOUT_S)
    finally:
        coordinator.close(timeout=TEST_TIMEOUT_S)


def test_activity_prevents_idle_exit_and_next_use_restarts_worker() -> None:
    harness = _WorkerHarness()
    worker = _worker(harness, linger_s=.05)

    with ThreadedLocalWorkerCoordinator() as coordinator:
        first = coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)
        assert first.interface.generation == 1
        assert not coordinator.wait_stopped(worker, timeout=.1)
        assert coordinator.inspect(worker).active_count == 1

        assert first.close()
        assert not first.close()
        assert coordinator.wait_stopped(worker, timeout=TEST_TIMEOUT_S)

        second = coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)
        assert second.generation == 2
        assert second.interface.generation == 2
        assert second.interface is not first.interface

        assert coordinator.request_shutdown(worker)
        second.close()
        assert coordinator.wait_stopped(worker, timeout=TEST_TIMEOUT_S)

    assert harness.factory_calls == 2


def test_acquisition_during_shutdown_waits_for_a_new_generation() -> None:
    harness = _WorkerHarness()
    worker = _worker(harness)

    with ThreadedLocalWorkerCoordinator() as coordinator:
        first = coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)
        assert coordinator.request_shutdown(worker)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            next_acquisition = executor.submit(coordinator.acquire, worker, timeout=TEST_TIMEOUT_S)
            assert not next_acquisition.done()

            first.close()
            second = next_acquisition.result(TEST_TIMEOUT_S)

        assert second.generation == 2
        assert second.interface.generation == 2
        assert harness.factory_calls == 2
        coordinator.request_shutdown(worker)
        second.close()
        assert coordinator.wait_stopped(worker, timeout=TEST_TIMEOUT_S)


def test_same_worker_has_independent_coordinator_instances() -> None:
    harness = _WorkerHarness()
    worker = _worker(harness)

    with (
            ThreadedLocalWorkerCoordinator() as first_coordinator,
            ThreadedLocalWorkerCoordinator() as second_coordinator,
    ):
        first = first_coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)
        second = second_coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)
        try:
            assert first.generation == second.generation == 1
            assert first.interface is not second.interface
            assert first.interface.thread_ident != second.interface.thread_ident
            assert harness.factory_calls == 2
        finally:
            first.close()
            second.close()


def test_start_failure_is_reported_and_a_later_acquisition_retries() -> None:
    harness = _WorkerHarness(fail_before_publish={1})
    worker = _worker(harness)

    with ThreadedLocalWorkerCoordinator() as coordinator:
        with pytest.raises(LocalWorkerStartError) as exc_info:
            coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)

        assert isinstance(exc_info.value.cause, RuntimeError)
        inspection = coordinator.inspect(worker)
        assert inspection.state is LocalWorkerState.FAILED
        assert inspection.generation == 1
        assert inspection.failure is not None
        assert inspection.failure.message == 'start failure 1'

        lease = coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)
        assert lease.generation == 2
        coordinator.request_shutdown(worker)
        lease.close()


def test_failure_after_publication_is_inspectable_and_restartable() -> None:
    fail = threading.Event()
    harness = _WorkerHarness(fail_after_release={1: fail})
    worker = _worker(harness)

    with ThreadedLocalWorkerCoordinator() as coordinator:
        first = coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)
        fail.set()
        first.close()
        assert coordinator.wait_stopped(worker, timeout=TEST_TIMEOUT_S)

        inspection = coordinator.inspect(worker)
        assert inspection.state is LocalWorkerState.FAILED
        assert inspection.failure is not None
        assert inspection.failure.message == 'run failure 1'

        second = coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)
        assert second.generation == 2
        coordinator.request_shutdown(worker)
        second.close()


def test_close_stops_persistent_daemon_thread_and_rejects_new_work() -> None:
    harness = _WorkerHarness()
    worker = _worker(harness)
    coordinator = ThreadedLocalWorkerCoordinator()
    lease = coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)
    assert lease.interface.thread_daemon
    lease.close()
    assert not coordinator.wait_stopped(worker, timeout=.05)

    assert coordinator.close(timeout=TEST_TIMEOUT_S)
    assert not coordinator.close(timeout=TEST_TIMEOUT_S)
    inspection = coordinator.inspect(worker)
    assert inspection.state is LocalWorkerState.STOPPED
    assert inspection.coordinator_closed

    with pytest.raises(LocalWorkerCoordinatorClosedError):
        coordinator.acquire(worker)


def test_worker_can_explicitly_keep_the_process_alive() -> None:
    harness = _WorkerHarness()
    worker = _worker(harness, keep_process_alive=True)

    with ThreadedLocalWorkerCoordinator() as coordinator:
        lease = coordinator.acquire(worker, timeout=TEST_TIMEOUT_S)
        assert not lease.interface.thread_daemon
        coordinator.request_shutdown(worker)
        lease.close()


def test_global_local_worker_conveniences_use_the_default_coordinator() -> None:
    harness = _WorkerHarness()
    worker = _worker(harness)
    coordinator = global_local_worker_coordinator()
    assert coordinator is global_local_worker_coordinator()

    lease = acquire_local_worker(worker, timeout=TEST_TIMEOUT_S)
    assert lease.interface.generation == 1
    assert call_local_worker(worker, lambda interface: interface, timeout=TEST_TIMEOUT_S) is lease.interface

    coordinator.request_shutdown(worker)
    lease.close()
    assert coordinator.wait_stopped(worker, timeout=TEST_TIMEOUT_S)
