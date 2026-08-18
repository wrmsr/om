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
