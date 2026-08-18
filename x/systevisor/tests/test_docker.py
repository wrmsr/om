# ruff: noqa: PT009 Q001 UP006 UP007 UP045
import json
import os
import unittest

from .docker_harness import SystevisorDockerHarness
from .docker_harness import SystevisorDockerHarnessSpec


@unittest.skipUnless(
    os.environ.get('SYSTEVISOR_DOCKER_TESTS') == '1',
    'set SYSTEVISOR_DOCKER_TESTS=1 to run isolated Docker scenarios',
)
class TestSystevisorDocker(unittest.TestCase):
    def test_amalgamated_python38_artifact_runs_as_pid_one(self) -> None:
        if not SystevisorDockerHarness.available():
            self.skipTest('Docker daemon is unavailable')
        child_source = '''
import json
import os

with open('/systevisor/checkpoints.ndjson', 'w') as checkpoint_file:
    checkpoint_file.write(json.dumps({'name': 'child', 'parent_pid': os.getppid()}) + '\\n')
'''.lstrip()
        config = {
            'manager': {
                'process_title': None,
                'log': {'stderr': True},
            },
            'units': {
                'child': {
                    'exec': {'argv': ['python3', '/systevisor/child.py']},
                    'kind': 'oneshot',
                    'autostart': False,
                    'restart': {'start_secs': 0},
                },
            },
            'collections': {
                'stack': {'units': ['child']},
            },
        }
        spec = SystevisorDockerHarnessSpec(
            command=(
                'python3',
                '/systevisor/systevisor.py',
                'run',
                'stack',
                '--config',
                '/systevisor/config.json',
            ),
            files={
                'child.py': child_source,
                'config.json': json.dumps(config),
            },
            image=os.environ.get('SYSTEVISOR_DOCKER_IMAGE', 'python:3.8-slim'),
        )

        with SystevisorDockerHarness(spec) as harness:
            checkpoint = harness.wait_checkpoint('child')
            exit_code = harness.wait()

        self.assertEqual(checkpoint.data['parent_pid'], 1)
        self.assertEqual(exit_code, 0)

    def test_self_update_preserves_pid_child_and_log_pipe(self) -> None:
        if not SystevisorDockerHarness.available():
            self.skipTest('Docker daemon is unavailable')
        child_source = r'''
import base64
import json
import os
import signal
import socket
import sys
import time

SOCKET_PATH = '/systevisor/control.sock'
DEADLINE = time.monotonic() + 30.


def request(method, target, body=None):
    encoded = b'' if body is None else json.dumps(body).encode('utf-8')
    message = (
        f'{method} {target} HTTP/1.1\r\n'
        'Host: localhost\r\n'
        'Connection: close\r\n'
        f'Content-Length: {len(encoded)}\r\n'
        + ('Content-Type: application/json\r\n' if body is not None else '')
        + '\r\n'
    ).encode('ascii') + encoded
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(SOCKET_PATH)
        client.sendall(message)
        response = bytearray()
        while True:
            data = client.recv(65536)
            if not data:
                break
            response.extend(data)
    head, _, response_body = bytes(response).partition(b'\r\n\r\n')
    status = int(head.split(b' ', 2)[1])
    return status, json.loads(response_body.decode('utf-8'))


def wait_json(target, predicate):
    last_error = None
    while time.monotonic() < DEADLINE:
        try:
            status, value = request('GET', target)
            if status < 400 and predicate(value):
                return value
        except (ConnectionError, FileNotFoundError, json.JSONDecodeError, OSError) as exc:
            last_error = exc
    raise RuntimeError(f'timed out waiting for {target}: {last_error}')


signal.signal(signal.SIGTERM, lambda _signum, _frame: sys.exit(0))
manager_pid = os.getppid()
child_pid = os.getpid()
print('before-update', flush=True)
wait_json('/v1/units', lambda value: value['instances'][0]['process_state'] == 'running')
status, update = request('POST', '/v1/_self_update', {'source': '/systevisor/systevisor.py'})
if status != 202:
    raise RuntimeError(update)
operation_id = update['operation']['operation_id']
wait_json(
    f'/v1/operations/{operation_id}',
    lambda value: value['status'] == 'succeeded',
)
with open('/systevisor/systevisor.py') as source_file:
    candidate_source = source_file.read()
needle = 'context.resume(handoff, completion_error=completion_error)'
if candidate_source.count(needle) != 1:
    raise RuntimeError('could not locate resume injection point')
candidate_source = candidate_source.replace(needle, "raise RuntimeError('injected resume failure')")
with open('/systevisor/candidate.py', 'w') as candidate_file:
    candidate_file.write(candidate_source)
status, rollback_update = request('POST', '/v1/_self_update', {'source': '/systevisor/candidate.py'})
if status != 202:
    raise RuntimeError(rollback_update)
rollback_operation_id = rollback_update['operation']['operation_id']
rollback_operation = wait_json(
    f'/v1/operations/{rollback_operation_id}',
    lambda value: value['status'] == 'failed',
)
if 'injected resume failure' not in rollback_operation['message']:
    raise RuntimeError(f'unexpected rollback message: {rollback_operation!r}')
_, log = request('GET', '/v1/logs/1/stdout?offset=0&limit=65536')
if b'before-update\n' not in base64.b64decode(log['data_base64']):
    raise RuntimeError(f'log back-buffer did not survive: {log!r}')
with open('/systevisor/checkpoints.ndjson', 'w') as checkpoint_file:
    checkpoint_file.write(json.dumps({
        'name': 'updated',
        'manager_pid_before': manager_pid,
        'manager_pid_after': os.getppid(),
        'child_pid': child_pid,
    }) + '\n')
request('POST', '/v1/_shutdown')
while True:
    signal.pause()
'''.lstrip()
        config = {
            'manager': {
                'process_title': None,
                'log': {'stderr': True},
                'observation': {'enabled': False},
            },
            'api': {'unix_socket': '/systevisor/control.sock'},
            'units': {
                'driver': {
                    'exec': {'argv': ['python3', '/systevisor/driver.py']},
                    'restart': {'mode': 'never', 'start_secs': 0},
                },
            },
        }
        spec = SystevisorDockerHarnessSpec(
            command=(
                'python3',
                '/systevisor/systevisor.py',
                'serve',
                '--config',
                '/systevisor/config.json',
            ),
            files={
                'driver.py': child_source,
                'config.json': json.dumps(config),
            },
            image=os.environ.get('SYSTEVISOR_DOCKER_IMAGE', 'python:3.8-slim'),
        )

        with SystevisorDockerHarness(spec) as harness:
            checkpoint = harness.wait_checkpoint('updated', timeout_secs=60.)
            exit_code = harness.wait()

        self.assertEqual(checkpoint.data['manager_pid_before'], 1)
        self.assertEqual(checkpoint.data['manager_pid_after'], 1)
        self.assertGreater(checkpoint.data['child_pid'], 1)
        self.assertEqual(exit_code, 0)
