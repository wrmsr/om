import os
import tempfile
import threading

from ... import dataclasses as dc
from ..daemon import Daemon
from ..services import Service
from ..services import ServiceDaemon
from ..spawning import MultiprocessingSpawning
from ..spawning import ThreadSpawning
from .helpers import ControlledService
from .testing import TEST_TIMEOUT_S
from .testing import accept_worker
from .testing import find_multiprocessing_child
from .testing import join_multiprocessing_child
from .testing import make_unix_listener
from .testing import read_locked_pidfile
from .testing import release_worker
from .testing import wait_pidfile_unlocked


##


class SharedStateService(Service['SharedStateService.Config']):
    @dc.dataclass(frozen=True)
    class Config(Service.Config):
        pass

    def __init__(
            self,
            config: Config,
            started: threading.Event,
            release: threading.Event,
            finished: threading.Event,
    ) -> None:
        super().__init__(config)

        self.started = started
        self.release = release
        self.finished = finished
        self.worker_thread_id: int | None = None

    def _run(self) -> None:
        self.worker_thread_id = threading.get_ident()
        self.started.set()
        self.release.wait()
        self.finished.set()


def test_service_daemon_runs_in_process_without_serializing_shared_state():
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    service = SharedStateService(SharedStateService.Config(), started, release, finished)
    service_daemon: ServiceDaemon[SharedStateService, SharedStateService.Config] = ServiceDaemon(
        service,
        Daemon.Config(
            spawning=ThreadSpawning(linger=True),
        ),
    )

    try:
        assert service_daemon.daemon_().launch_no_wait()
        assert started.wait(TEST_TIMEOUT_S)
        assert service.worker_thread_id is not None
        assert service.worker_thread_id != threading.get_ident()
    finally:
        release.set()

    assert finished.wait(TEST_TIMEOUT_S)


##


def test_service_daemon_runs_configured_service_in_spawned_process():
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')
        pid_file = os.path.join(temp_dir, 'service.pid')

        service_daemon: ServiceDaemon[ControlledService, ControlledService.Config] = ServiceDaemon(
            ControlledService.Config(
                control_path=control_path,
                label='configured-service',
            ),
            Daemon.Config(
                spawning=MultiprocessingSpawning(
                    start_method=MultiprocessingSpawning.StartMethod.SPAWN,
                ),
                pid_file=pid_file,
            ),
        )

        with make_unix_listener(control_path) as listener:
            assert service_daemon.daemon_().launch_no_wait()

            conn, info = accept_worker(listener)
            worker_pid = info['pid']
            process = find_multiprocessing_child(worker_pid)

            assert info['label'] == 'configured-service'
            assert read_locked_pidfile(pid_file) == worker_pid

            release_worker(conn)
            wait_pidfile_unlocked(pid_file)

            assert join_multiprocessing_child(process) == 0
