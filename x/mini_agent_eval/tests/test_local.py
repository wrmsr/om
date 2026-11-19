import json
import os
import sys
import tempfile
import unittest
from unittest import mock

from .. import minieval


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
        self.task = minieval.Task('task', task_path, 'Replace the starting file with answer.txt.\n')

    def write(self, name, contents):
        path = os.path.join(self.directory, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(contents)
        return path

    def test_external_submission_is_graded_from_a_fresh_snapshot_and_cannot_write_outside(self):
        try:
            minieval.check_local_runtime()
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
        agent = minieval.load_agent('external', self.directory, [sys.executable, adapter, outside, secret])
        result = minieval.run_local_trial(
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
        self.assertEqual(minieval.read_text(os.path.join(workspace, 'answer.txt')), 'ok')
        artifacts = os.path.join(self.directory, 'attempt', 'agent-artifacts', 'metrics.txt')
        self.assertEqual(minieval.read_text(artifacts), 'wrote answer')
        patch = minieval.read_text(os.path.join(self.directory, 'attempt', 'patch.diff'))
        self.assertIn('deleted file mode', patch)
        self.assertIn('new file mode', patch)

    def test_scripted_backend_invokes_a_tool_and_passes_the_grader(self):
        try:
            minieval.check_local_runtime()
        except ValueError as exc:
            self.skipTest(str(exc))
        script = self.write('script.json', json.dumps([
            {'tool_calls': [{
                'name': 'bash',
                'args': {'command': 'rm base.py && python -c "open(\'answer.txt\', \'w\').write(\'ok\')"'},
            }]},
            {'text': 'Done.'},
        ]))
        result = minieval.run_local_trial(
            self.task,
            minieval.Agent('scripted', 'scripted'),
            output_dir=os.path.join(self.directory, 'scripted-attempt'),
            timeout=30,
            test_timeout=30,
            script=script,
        )

        self.assertEqual(result['status'], 'passed', result.get('error'))
        log = minieval.read_text(os.path.join(self.directory, 'scripted-attempt', 'agent.log'))
        self.assertIn('Agent end reason: COMPLETED', log)
        self.assertIn('Tool result script-0-0', log)

    def test_live_agent_receives_only_selected_key_on_stdin(self):
        request = {
            'runtime': 'local',
            'workdir': os.path.join(self.directory, 'work'),
            'output_dir': self.directory,
            'instruction_file': os.path.join(self.directory, 'instruction.md'),
            'artifact_dir': os.path.join(self.directory, 'artifacts'),
        }
        with mock.patch.object(minieval, 'local_om_api_key', return_value='fake-selected-key') as key:
            with mock.patch.object(minieval, 'run_command', return_value=minieval.CommandResult(0, 0)) as command:
                minieval.run_local_agent(
                    minieval.Agent('om', 'om'),
                    self.task,
                    request,
                    scratch=os.path.join(self.directory, 'scratch'),
                    timeout=30,
                    extra_args=(),
                    extra_env=(),
                    script=None,
                )
        key.assert_called_once_with('gpt')
        kwargs = command.call_args.kwargs
        self.assertEqual(json.loads(kwargs['input_data']), {'request': request, 'api_key': 'fake-selected-key'})
        self.assertNotIn('fake-selected-key', repr(kwargs['env']))
        self.assertNotIn('OM_SECRETS', kwargs['env'])
        self.assertNotIn('OPENAI_API_KEY', kwargs['env'])
        self.assertIsNotNone(kwargs['local_read_access'])
