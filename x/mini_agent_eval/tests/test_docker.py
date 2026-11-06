# ruff: noqa: Q001
"""Opt-in integration tests: MINIEVAL_DOCKER_TESTS=1 python -m unittest tests.test_docker -v."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

from .. import minieval


##


class DockerTest(unittest.TestCase):
    def setUp(self):
        super().setUp()

        if os.environ.get('MINIEVAL_DOCKER_TESTS') != '1':
            self.skipTest('Set MINIEVAL_DOCKER_TESTS=1 to run real Docker integration tests')
        self.docker = os.environ.get('MINIEVAL_DOCKER', 'docker')
        if not shutil.which(self.docker):
            self.fail(f'Docker executable is unavailable: {self.docker}')
        subprocess.run(
            [self.docker, 'info'],
            check=True,
            stdout=subprocess.DEVNULL,
            timeout=30,
        )
        directory = tempfile.TemporaryDirectory(prefix='mini eval docker tests ')
        self.addCleanup(directory.cleanup)
        self.directory = directory.name
        self.root = os.path.dirname(os.path.abspath(minieval.__file__))

    def write(self, name, contents):
        path = os.path.join(self.directory, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(textwrap.dedent(contents).lstrip('\n'))
        return path

    def invoke(
            self,
            action,
            *,
            run_id,
            options=(),
            command=(),
            expected_returncode=0,
    ):
        args = [
            sys.executable,
            '-m',
            'minieval',
            action,
            '--docker',
            self.docker,
            '--runs',
            os.path.join(self.directory, 'runs'),
            '--run-id',
            run_id,
        ]
        if platform := os.environ.get('MINIEVAL_PLATFORM'):
            args.extend(['--platform', platform])
        args.extend(options)
        if command:
            args.extend(['--', *command])
        result = subprocess.run(  # noqa
            args,
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=1800,
        )
        self.assertEqual(result.returncode, expected_returncode, result.stdout)
        run_dir = os.path.join(self.directory, 'runs', run_id)
        with open(os.path.join(run_dir, 'results.jsonl'), encoding='utf-8') as f:
            results = [json.loads(line) for line in f]
        for trial in results:
            self.assertFalse(trial.get('cleanup_errors'), trial)
            for container in trial['containers']:
                inspected = subprocess.run(
                    [self.docker, 'container', 'inspect', container],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    timeout=30,
                )
                self.assertNotEqual(inspected.returncode, 0, f'Container was leaked: {container}')
        return run_dir, results

    def test_starter_tasks_have_valid_positive_and_negative_controls(self):
        _, results = self.invoke('check', run_id='controls')
        tasks = minieval.load_tasks(os.path.join(self.root, 'tasks'))
        self.assertEqual(len(results), 2 * len(tasks))
        self.assertEqual(
            {(r['task'], r['agent'], r['status']) for r in results},
            {(t.name, 'nop', 'failed') for t in tasks} | {(t.name, 'oracle', 'passed') for t in tasks},
        )

    def test_external_reference_agent_and_repeats(self):
        run_dir, results = self.invoke(
            'run',
            run_id='external',
            options=['--agent', 'external', '--task', 'lines', '--repeat', '2'],
            command=[sys.executable, '-m', 'examples.externaloracle', '--solutions', 'tasks'],
        )
        self.assertEqual([r['status'] for r in results], ['passed', 'passed'])
        self.assertNotEqual(results[0]['containers'], results[1]['containers'])
        for attempt in (1, 2):
            workspace = os.path.join(run_dir, f'lines-external-{attempt}', 'workspace')
            self.assertTrue(os.path.isfile(os.path.join(workspace, 'lines.py')))
            self.assertFalse(os.path.lexists(os.path.join(workspace, '.git')))

    def test_snapshot_includes_new_committed_staged_untracked_and_deleted_files(self):
        self.write('tasks/snapshot/instruction.md', '# Exercise workspace transfer\n')
        self.write('tasks/snapshot/environment/Dockerfile', '''
            FROM python:3.12-slim-bookworm
            RUN apt-get update && apt-get install -y --no-install-recommends git \\
                && rm -rf /var/lib/apt/lists/*
            RUN useradd --create-home --uid 1000 agent
            WORKDIR /work
            COPY edit.txt gone.txt /work/
            RUN chown -R agent:agent /work
        ''')
        self.write('tasks/snapshot/environment/edit.txt', 'original\n')
        self.write('tasks/snapshot/environment/gone.txt', 'delete this\n')
        self.write(
            'tasks/snapshot/tests/test.sh',
            'set -eu\npython -m unittest discover -s /tests -p verify.py -v\n',
        )
        self.write('tasks/snapshot/tests/verify.py', '''
            import os
            import subprocess
            import unittest


            class SnapshotTest(unittest.TestCase):
                def test_final_state(self):
                    for name in ('edit.txt', 'committed.txt', 'staged.txt', 'untracked.txt'):
                        with open(name) as f:
                            self.assertEqual(f.read(), 'changed\\n')
                    self.assertFalse(os.path.exists('gone.txt'))
                    self.assertFalse(os.path.exists('/tmp/agent-was-here'))
                    identity = subprocess.check_output(['git', 'config', 'user.name'], text=True).strip()
                    self.assertEqual(identity, 'Mini Eval')
        ''')
        driver = self.write('external.py', '''
            import json
            import subprocess
            import sys


            def _main():
                request = json.load(sys.stdin)
                script = """
                    set -eu
                    git config user.name ChangedByAgent
                    printf 'changed\\n' > edit.txt
                    printf 'changed\\n' > committed.txt
                    git add edit.txt committed.txt
                    git commit -qm 'Agent committed a partial fix'
                    printf 'changed\\n' > staged.txt
                    git add staged.txt
                    printf 'changed\\n' > untracked.txt
                    rm gone.txt
                    touch /tmp/agent-was-here
                """
                subprocess.run([
                    request['docker_executable'], 'exec', '--user', 'agent', '--workdir', '/work',
                    request['container_id'], 'sh', '-c', script,
                ], check=True)


            if __name__ == '__main__':
                _main()
        ''')
        options = ['--agent', 'external', '--tasks', os.path.join(self.directory, 'tasks')]
        run_dir, results = self.invoke(
            'run',
            run_id='snapshot',
            options=options,
            command=[sys.executable, driver],
        )
        self.assertEqual(results[0]['status'], 'passed', results)
        patch = minieval.read_text(os.path.join(run_dir, 'snapshot-external-1', 'patch.diff'))
        for name in ('edit.txt', 'gone.txt', 'committed.txt', 'staged.txt', 'untracked.txt'):
            self.assertIn(name, patch)

        _, results = self.invoke(
            'run',
            run_id='timeout',
            options=[*options, '--timeout', '1'],
            command=[sys.executable, '-c', 'import signal; signal.pause()'],
            expected_returncode=1,
        )
        self.assertEqual(results[0]['status'], 'agent_timeout', results)
