import os
import tempfile

from ..daemon import Daemon
from ..services import ServiceDaemon
from ..spawning import MultiprocessingSpawning
from .helpers import ControlledService
from .testing import accept_worker
from .testing import find_multiprocessing_child
from .testing import join_multiprocessing_child
from .testing import make_unix_listener
from .testing import read_locked_pidfile
from .testing import release_worker
from .testing import wait_pidfile_unlocked


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
