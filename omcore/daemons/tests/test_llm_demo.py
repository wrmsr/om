import os
import signal
import subprocess
import sys
import tempfile

from .testing import TEST_TIMEOUT_S
from .testing import read_locked_daemon_pidfile_info
from .testing import wait_pidfile_unlocked


##


def test_llm_demo_cli_lazily_spawns_then_connects_to_same_service():
    with tempfile.TemporaryDirectory(prefix='omd-') as state_dir:
        pid_file = os.path.join(state_dir, 'llm.pid')

        def run(message: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [
                    sys.executable,
                    '-m',
                    'omcore.daemons.tests.demos.llm',
                    '--state-dir',
                    state_dir,
                    '--linger',
                    '30',
                    '--timeout',
                    str(TEST_TIMEOUT_S),
                    '--message',
                    message,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=TEST_TIMEOUT_S,
            )

        worker_pid = None
        try:
            first = run('background workers')
            assert first.stdout.strip() == 'Fascintating! Tell me more about background workers'

            first_info = read_locked_daemon_pidfile_info(pid_file)
            worker_pid = first_info.pid

            second = run('Unix sockets')
            assert second.stdout.strip() == 'Fascintating! Tell me more about Unix sockets'

            second_info = read_locked_daemon_pidfile_info(pid_file)
            assert second_info.pid == worker_pid
            assert second_info.instance_id == first_info.instance_id

        finally:
            if worker_pid is not None:
                try:
                    os.kill(worker_pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                else:
                    wait_pidfile_unlocked(pid_file)
