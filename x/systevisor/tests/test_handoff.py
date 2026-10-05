# ruff: noqa: PT009 PTH118 PTH123 S603 UP006 UP007 UP045
"""
The exec/resume/rollback spine of self-update and the manager's startup, run for real: a manager from the single-file
artifact in its own process, driven over its control socket. Candidates are that same artifact, patched where a test
needs one to misbehave at a particular point.
"""
import errno
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import typing as ta
import unittest

from ..control.client import SystevisorApiClient
from ..control.client import SystevisorApiEndpoint
from ..control.jsoncodec import SystevisorJsonCodec
from .utils import systevisor_test_artifact_source


_SYSTEVISOR_TEST_HANDOFF_TIMEOUT_SECS = 30.

_SYSTEVISOR_TEST_HANDOFF_RESUME_NEEDLE = 'context.resume(handoff, completion_error=completion_error)'
_SYSTEVISOR_TEST_HANDOFF_RESUME_ARGUMENT_NEEDLE = "self_update_resume.add_argument('--manifest', required=True)"


class SystevisorTestHandoffManager:
    def __init__(self, root: str, units: ta.Mapping[str, ta.Any]) -> None:
        self.root = root
        self.socket_path = os.path.join(root, 'control.sock')
        self.stderr_path = os.path.join(root, 'manager.stderr')
        self.config_path = os.path.join(root, 'config.json')
        with open(self.config_path, 'w') as config_file:
            json.dump({
                'manager': {'observation': {'enabled': False}},
                'api': {'unix_socket': self.socket_path},
                'units': units,
            }, config_file)
        self._candidates = 0
        self._client = SystevisorApiClient(
            SystevisorApiEndpoint(unix_socket=self.socket_path),
            SystevisorJsonCodec(),
            timeout_secs=5.,
        )
        self.running_path = self.candidate()
        with open(self.stderr_path, 'wb') as stderr_file:
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    self.running_path,
                    'serve',
                    '--config',
                    self.config_path,
                    '--state-directory',
                    os.path.join(root, 'state'),
                ],
                stdin=subprocess.DEVNULL,
                stdout=stderr_file,
                stderr=stderr_file,
            )

    def candidate(self, *replacements: ta.Tuple[str, str]) -> str:
        """Writes another copy of the artifact, with a digest of its own, optionally patched."""

        source = systevisor_test_artifact_source()
        for old, new in replacements:
            if source.count(old) != 1:
                raise AssertionError(f'could not locate injection point: {old!r}')
            source = source.replace(old, new)
        self._candidates += 1
        path = os.path.join(self.root, f'systevisor-{self._candidates}.py')
        with open(path, 'w') as candidate_file:
            candidate_file.write(source + f'\n# candidate {self._candidates}\n')
        return path

    def stderr(self) -> str:
        with open(self.stderr_path, errors='replace') as stderr_file:
            return stderr_file.read()[-4000:]

    def request(self, method: str, target: str, body: ta.Any = None) -> ta.Tuple[int, ta.Any]:
        response = self._client.request(method, target, body)
        return response.status, json.loads(response.body.decode('utf-8'))

    def wait_json(self, target: str, predicate: ta.Callable[[ta.Any], bool]) -> ta.Any:
        # Listeners are recreated across a handoff, so a refused or reset connection is part of waiting.
        deadline = time.monotonic() + _SYSTEVISOR_TEST_HANDOFF_TIMEOUT_SECS
        last: ta.Any = None
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise AssertionError(f'manager exited {self.process.returncode} while waiting:\n{self.stderr()}')
            try:
                status, last = self.request('GET', target)
            except (OSError, ValueError) as exc:
                last = exc
                continue
            if status < 400 and predicate(last):
                return last
        raise AssertionError(f'timed out waiting for {target}; last saw {last!r}\n{self.stderr()}')

    def wait_running(self) -> None:
        self.wait_json('/v1/units', lambda value: all(
            instance['process_state'] == 'running'
            for instance in value['instances']
        ))

    def update(self, source_path: str) -> str:
        status, value = self.request('POST', '/v1/_self_update', {'source': source_path})
        if status != 202:
            raise AssertionError((status, value))
        return value['operation']['operation_id']

    def wait_operation(self, operation_id: str) -> ta.Any:
        return self.wait_json(f'/v1/operations/{operation_id}', lambda value: value['status'] != 'pending')

    def wait_exit(self) -> int:
        try:
            return self.process.wait(timeout=_SYSTEVISOR_TEST_HANDOFF_TIMEOUT_SECS)
        except subprocess.TimeoutExpired:
            raise AssertionError(f'manager did not exit:\n{self.stderr()}') from None

    def close(self) -> None:
        # Only reached with the manager still running when a test has already failed. It is asked before it is killed,
        # since killing it outright would leave its children behind for whoever runs the suite.
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10.)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


def _systevisor_test_handoff_digest(path: str) -> str:
    with open(path, 'rb') as source_file:
        return hashlib.sha256(source_file.read()).hexdigest()


def _systevisor_test_handoff_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


class TestSystevisorHandoff(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = self.temp_dir.name
        self.child_pid_path = os.path.join(self.root, 'child.pid')

    def _manager(self, units: ta.Optional[ta.Mapping[str, ta.Any]] = None) -> SystevisorTestHandoffManager:
        manager = SystevisorTestHandoffManager(self.root, units if units is not None else {
            'worker': {
                'exec': {'argv': ['/bin/sh', '-c', f'echo $$ > {self.child_pid_path}; exec sleep 600']},
                'restart': {'mode': 'never', 'start_secs': 0},
            },
        })
        self.addCleanup(manager.close)
        return manager

    def _child_pid(self) -> int:
        deadline = time.monotonic() + _SYSTEVISOR_TEST_HANDOFF_TIMEOUT_SECS
        while time.monotonic() < deadline:
            try:
                with open(self.child_pid_path) as pid_file:
                    return int(pid_file.read())
            except (FileNotFoundError, ValueError):
                continue
        raise AssertionError('worker never reported its pid')

    def _assert_gone(self, pid: int) -> None:
        # The manager reaps its children before it exits, so by then the pid no longer names anything.
        self.assertFalse(_systevisor_test_handoff_alive(pid), 'the managed child outlived its manager')

    def test_updates_repeatedly_keeping_its_pid_and_its_children(self) -> None:
        manager = self._manager()
        manager.wait_running()
        child_pid = self._child_pid()
        [before] = manager.request('GET', '/v1/units')[1]['instances']

        # The second update is asked of an image that was itself resumed into rather than started.
        for _ in range(2):
            candidate_path = manager.candidate()
            operation = manager.wait_operation(manager.update(candidate_path))
            self.assertEqual(operation['status'], 'succeeded', operation)
            self.assertEqual(operation['data']['manager_pid'], manager.process.pid)
            self.assertEqual(operation['data']['source_sha256'], _systevisor_test_handoff_digest(candidate_path))
            [after] = manager.request('GET', '/v1/units')[1]['instances']
            self.assertEqual((after['run_id'], after['process_state']), (before['run_id'], 'running'))
            self.assertTrue(_systevisor_test_handoff_alive(child_pid))

        manager.request('POST', '/v1/_shutdown')
        self.assertEqual(manager.wait_exit(), 0, manager.stderr())
        self._assert_gone(child_pid)

    def test_failed_resume_rolls_back_and_the_previous_image_carries_on(self) -> None:
        manager = self._manager()
        manager.wait_running()
        child_pid = self._child_pid()

        operation = manager.wait_operation(manager.update(manager.candidate((
            _SYSTEVISOR_TEST_HANDOFF_RESUME_NEEDLE,
            "raise RuntimeError('injected resume failure')",
        ))))
        self.assertEqual(operation['status'], 'failed', operation)
        self.assertIn('injected resume failure', operation['message'])
        self.assertIsNone(manager.process.poll())
        self.assertTrue(_systevisor_test_handoff_alive(child_pid))

        # Having been through an exec out and an exec back, it can still be updated.
        operation = manager.wait_operation(manager.update(manager.candidate()))
        self.assertEqual(operation['status'], 'succeeded', operation)
        self.assertTrue(_systevisor_test_handoff_alive(child_pid))

        manager.request('POST', '/v1/_shutdown')
        self.assertEqual(manager.wait_exit(), 0, manager.stderr())
        self._assert_gone(child_pid)

    def test_candidate_that_would_not_accept_the_resume_command_is_refused_by_its_probe(self) -> None:
        manager = self._manager()
        manager.wait_running()
        child_pid = self._child_pid()

        operation = manager.wait_operation(manager.update(manager.candidate((
            _SYSTEVISOR_TEST_HANDOFF_RESUME_ARGUMENT_NEEDLE,
            "self_update_resume.add_argument('--handoff', required=True)",
        ))))
        self.assertEqual(operation['status'], 'failed', operation)
        self.assertIn('does not accept the resume command line', operation['message'])
        self.assertIsNone(manager.process.poll())
        self.assertTrue(_systevisor_test_handoff_alive(child_pid))

        manager.request('POST', '/v1/_shutdown')
        self.assertEqual(manager.wait_exit(), 0, manager.stderr())

    def test_signal_between_exec_and_resume_waits_for_handlers(self) -> None:
        manager = self._manager()
        manager.wait_running()
        child_pid = self._child_pid()
        gate_path = os.path.join(self.root, 'gate')
        os.mkfifo(gate_path)

        # The candidate stops at the gate with the exec behind it and no handler installed yet.
        manager.update(manager.candidate((
            _SYSTEVISOR_TEST_HANDOFF_RESUME_NEEDLE,
            f'(open({gate_path!r}).read(), {_SYSTEVISOR_TEST_HANDOFF_RESUME_NEEDLE})',
        )))
        deadline = time.monotonic() + _SYSTEVISOR_TEST_HANDOFF_TIMEOUT_SECS
        while True:
            try:
                gate_fd = os.open(gate_path, os.O_WRONLY | os.O_NONBLOCK)
                break
            except OSError as exc:
                if exc.errno != errno.ENXIO or time.monotonic() >= deadline:
                    raise AssertionError(f'candidate never reached the gate:\n{manager.stderr()}') from exc
        os.kill(manager.process.pid, signal.SIGTERM)
        os.close(gate_fd)

        # Delivered once there is something to deliver it to, it is an ordinary request to shut down.
        self.assertEqual(manager.wait_exit(), 0, manager.stderr())
        self._assert_gone(child_pid)

    def test_resume_that_can_be_neither_completed_nor_rolled_back_stops_the_children(self) -> None:
        manager = self._manager()
        manager.wait_running()
        child_pid = self._child_pid()

        # Fails to resume, having first altered the image it would have gone back to.
        manager.update(manager.candidate((
            _SYSTEVISOR_TEST_HANDOFF_RESUME_NEEDLE,
            "[open(manifest.previous_source_path, 'a').write('# altered'), 1 // 0]",
        )))

        self.assertEqual(manager.wait_exit(), 2, manager.stderr())
        self.assertIn('self_update_rollback_failed', manager.stderr())
        self._assert_gone(child_pid)

    def test_signal_during_startup_is_a_shutdown_and_not_a_kill(self) -> None:
        # Every unit signals the manager the moment it starts, so the first signal lands while the rest are still
        # being spawned. Each records itself first so that it can be looked for afterwards.
        pid_directory = os.path.join(self.root, 'pids')
        os.mkdir(pid_directory)
        count = 24
        manager = self._manager({
            f'unit{index:02d}': {
                'exec': {'argv': [
                    '/bin/sh',
                    '-c',
                    f'echo $$ > {pid_directory}/{index}; kill -TERM $PPID; exec sleep 600',
                ]},
                'restart': {'mode': 'never', 'start_secs': 0},
            }
            for index in range(count)
        })

        self.assertEqual(manager.wait_exit(), 0, manager.stderr())
        pids = []
        for name in os.listdir(pid_directory):
            with open(os.path.join(pid_directory, name)) as pid_file:
                pids.append(int(pid_file.read()))
        self.assertTrue(pids)
        self.assertEqual([pid for pid in pids if _systevisor_test_handoff_alive(pid)], [])
