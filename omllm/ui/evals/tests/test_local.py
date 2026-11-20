import json
import os
import shlex
import sys
import tempfile
import unittest
from unittest import mock

from .. import commands
from .. import landlock
from .. import local
from .. import models
from ..assets import eval_resources


##


@unittest.skipUnless(sys.platform == 'linux', 'Local runtime requires Linux Landlock')
class LocalRuntimeTest(unittest.TestCase):
    def setUp(self):
        super().setUp()

        directory = tempfile.TemporaryDirectory(prefix='mini eval local ')
        self.addCleanup(directory.cleanup)
        self.directory = directory.name

        task_path = os.path.join(self.directory, 'task')
        os.makedirs(os.path.join(task_path, 'environment'))
        os.makedirs(os.path.join(task_path, 'tests'))
        self.write('task/instruction.md', 'Replace the starting file with answer.txt.\n')
        self.write('task/environment/Dockerfile', 'FROM python:3.12-slim-bookworm\nCOPY *.py ./\n')
        self.write('task/environment/base.py', 'START = True\n')
        self.write('task/tests/test.sh', (
            '#!/bin/sh\n'
            'set -eu\n'
            'test ! -e "$MINIEVAL_WORKDIR/base.py"\n'
            'test "$(cat "$MINIEVAL_WORKDIR/answer.txt")" = ok\n'
        ))
        self.task = models.Task('task', task_path, 'Replace the starting file with answer.txt.\n')

    def write(self, name, contents):
        path = os.path.join(self.directory, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(contents)
        return path

    def test_external_submission_is_graded_from_a_fresh_snapshot_and_cannot_write_outside(self):
        try:
            landlock.check_local_runtime()
        except ValueError as exc:
            self.skipTest(str(exc))
        outside = os.path.join(self.directory, 'outside.txt')
        secret = self.write('host-secret.txt', 'must-stay-private')
        self.write('task/tests/test.sh', (
            '#!/bin/sh\n'
            'set -eu\n'
            f'if cat "{secret}" >/dev/null 2>&1; then exit 1; fi\n'
            'test ! -e "$MINIEVAL_WORKDIR/base.py"\n'
            'test "$(cat "$MINIEVAL_WORKDIR/answer.txt")" = ok\n'
        ))
        adapter = self.write('adapter.py', (
            'import json\n'
            'import os\n'
            'import sys\n'
            'request = json.load(sys.stdin)\n'
            'try:\n'
            '    open(sys.argv[1], "w").write("escaped")\n'
            'except PermissionError:\n'
            '    pass\n'
            'else:\n'
            '    raise RuntimeError("outside write succeeded")\n'
            'try:\n'
            '    open(sys.argv[2]).read()\n'
            'except PermissionError:\n'
            '    pass\n'
            'else:\n'
            '    raise RuntimeError("outside read succeeded")\n'
            'os.unlink(os.path.join(request["workdir"], "base.py"))\n'
            'with open(os.path.join(request["workdir"], "answer.txt"), "w") as f:\n'
            '    f.write("ok")\n'
            'with open(os.path.join(request["artifact_dir"], "metrics.txt"), "w") as f:\n'
            '    f.write("wrote answer")\n'
        ))
        agent = models.load_agent('external', self.directory, [sys.executable, adapter, outside, secret])
        result = local.run_local_trial(
            self.task,
            agent,
            output_dir=os.path.join(self.directory, 'attempt'),
            timeout=30,
            test_timeout=30,
        )

        self.assertEqual(result['status'], 'passed', result.get('error'))
        self.assertFalse(os.path.exists(outside))
        workspace = os.path.join(self.directory, 'attempt', 'workspace')
        self.assertFalse(os.path.exists(os.path.join(workspace, 'base.py')))
        self.assertEqual(commands.read_text(os.path.join(workspace, 'answer.txt')), 'ok')
        artifacts = os.path.join(self.directory, 'attempt', 'agent-artifacts', 'metrics.txt')
        self.assertEqual(commands.read_text(artifacts), 'wrote answer')
        patch = commands.read_text(os.path.join(self.directory, 'attempt', 'patch.diff'))
        self.assertIn('deleted file mode', patch)
        self.assertIn('new file mode', patch)

    def test_scripted_backend_invokes_a_tool_and_passes_the_grader(self):
        try:
            landlock.check_local_runtime()
        except ValueError as exc:
            self.skipTest(str(exc))
        secret = self.write('host-secret.txt', 'private')
        solution = eval_resources().joinpath('tasks', 'intervals', 'solution', 'intervals.py')
        command = (
            f'if cat {shlex.quote(secret)} >/dev/null 2>&1 || '
            f'cat {shlex.quote(str(solution))} >/dev/null 2>&1 || test -n "$MINIEVAL_HOST_SECRET"; '
            'then exit 1; fi; rm base.py && printf ok > answer.txt'
        )
        script = self.write('script.json', json.dumps([
            {'tool_calls': [{
                'name': 'bash',
                'args': {'command': command},
            }]},
            {'text': 'Done.'},
        ]))
        with mock.patch.dict(os.environ, {'MINIEVAL_HOST_SECRET': 'private-value'}):
            result = local.run_local_trial(
                self.task,
                models.Agent('scripted', 'scripted'),
                output_dir=os.path.join(self.directory, 'scripted-attempt'),
                timeout=30,
                test_timeout=30,
                script=script,
            )

        log = commands.read_text(os.path.join(self.directory, 'scripted-attempt', 'agent.log'))
        self.assertEqual(result['status'], 'passed', result.get('error', log))
        self.assertIn('Agent end reason: COMPLETED', log)
        self.assertIn('Tool result script-0-0', log)
