import json
import os
import select
import signal
import subprocess
import sys
import tempfile
import unittest

from .. import minieval


##


class FailingDocker(minieval.Docker):
    def __init__(self, failure):
        super().__init__(
            executable='unused',
            platform=None,
            timeout=5,
            log_path=os.devnull,
        )

        self.failure = failure
        self.calls = []

    def call(self, args, **kwargs):
        self.calls.append(list(args))
        if args[0] == self.failure:
            if self.failure == 'create':
                raise KeyboardInterrupt
            raise minieval.CommandError('Injected start failure')
        return minieval.CommandResult(0, 0.0, stdout=('a' * 64 + '\n').encode())


class RunnerTest(unittest.TestCase):
    def setUp(self):
        super().setUp()

        directory = tempfile.TemporaryDirectory(prefix='mini eval tests ')
        self.addCleanup(directory.cleanup)
        self.directory = directory.name

    def write(self, name, contents):
        path = os.path.join(self.directory, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(contents)
        return path

    def task(self, name):
        self.write(name + '/instruction.md', '# Repair the example\n')
        self.write(name + '/environment/Dockerfile', 'FROM scratch\n')
        self.write(name + '/tests/test.sh', 'exit 1\n')
        return os.path.join(self.directory, name)

    def test_command_preserves_arguments_and_binary_input(self):
        args = ['a b', '$(touch unwanted)', '`touch unwanted`', '{"x": "y"}', "it's quoted"]
        source = (
            'import json\n'
            'import sys\n'
            'print(json.dumps([sys.argv[1:], sys.stdin.buffer.read().hex()]))\n'
            'print("diagnostic", file=sys.stderr)\n'
        )
        log = os.path.join(self.directory, 'command.log')
        result = minieval.run_command(
            [sys.executable, '-c', source, *args],
            log_path=log,
            timeout=10,
            input_data=b'hello\x00\xff\n',
            capture=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertFalse(result.timed_out)
        self.assertEqual(json.loads(result.stdout), [args, '68656c6c6f00ff0a'])
        self.assertIn('diagnostic', minieval.read_text(log))

    def test_timeout_kills_a_resistant_descendant(self):
        marker = os.path.join(self.directory, 'child.pid')
        child_source = (
            'import os\n'
            'import signal\n'
            'import sys\n'
            'signal.signal(signal.SIGTERM, signal.SIG_IGN)\n'
            'with open(sys.argv[1], "w") as f: f.write(str(os.getpid()))\n'
            'signal.pause()\n'
        )
        parent_source = (
            'import signal\n'
            'import subprocess\n'
            'import sys\n'
            'subprocess.Popen([sys.executable, "-c", sys.argv[1], sys.argv[2]])\n'
            'signal.pause()\n'
        )
        result = minieval.run_command(
            [sys.executable, '-c', parent_source, child_source, marker],
            log_path=os.path.join(self.directory, 'timeout.log'),
            timeout=1,
            capture=True,
        )

        self.assertTrue(result.timed_out)
        self.assertNotEqual(result.returncode, 0)
        self.assertLess(result.seconds, 8)
        pid = int(minieval.read_text(marker))
        state = subprocess.run(
            ['ps', '-p', str(pid), '-o', 'stat='],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        ).stdout.strip()
        # An orphan may remain briefly as a zombie under the host's PID 1.
        if state and not state.startswith('Z'):
            os.kill(pid, signal.SIGKILL)
        self.assertTrue(not state or state.startswith('Z'), state)

    def test_interrupt_cleans_up_the_active_command(self):
        marker = os.path.join(self.directory, 'command.pid')
        os.mkfifo(marker)
        child_source = (
            'import os\n'
            'import signal\n'
            'import sys\n'
            'with open(sys.argv[1], "w") as f: f.write(str(os.getpid()))\n'
            'signal.pause()\n'
        )
        runner_source = (
            'import sys\n'
            'import minieval\n'
            'minieval.run_command(\n'
            '    [sys.executable, "-c", sys.argv[1], sys.argv[2]],\n'
            '    log_path=sys.argv[3], timeout=60, capture=True,\n'
            ')\n'
        )
        ready_fd = os.open(marker, os.O_RDWR | os.O_NONBLOCK)
        try:
            with subprocess.Popen(
                    [
                        sys.executable,
                        '-c',
                        runner_source,
                        child_source,
                        marker,
                        os.path.join(self.directory, 'interrupt.log'),
                    ],
                    cwd=os.path.dirname(os.path.abspath(minieval.__file__)),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
            ) as process:
                try:
                    ready, _, _ = select.select([ready_fd], [], [], 10)
                    self.assertTrue(ready, 'The command did not signal readiness')
                    pid = int(os.read(ready_fd, 64))
                    process.send_signal(signal.SIGINT)
                    process.wait(timeout=10)
                finally:
                    if process.poll() is None:
                        minieval.stop_process(process)
        finally:
            os.close(ready_fd)

        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_task_discovery_ignores_desktop_metadata(self):
        self.task('one')
        self.task('two')
        self.write('.DS_Store', 'Finder metadata')
        self.write('README.md', 'Task collection')

        self.assertEqual([task.name for task in minieval.load_tasks(self.directory)], ['one', 'two'])
        selected = minieval.load_tasks(self.directory, ['two', 'one'])
        self.assertEqual([task.name for task in selected], ['two', 'one'])

    def test_task_selection_rejects_escape_and_duplicate(self):
        self.task('one')
        for names in (['../one'], ['one', 'one'], ['missing']):
            with self.subTest(names=names):
                with self.assertRaises(ValueError):
                    minieval.load_tasks(self.directory, names)

    def test_template_substitution_is_literal_and_nonrecursive(self):
        value = 'python {instruction_file} {workdir} {"ordinary": "braces"}'
        tokens = {
            'instruction_file': '/tmp/run {workdir}/instruction.md',  # noqa
            'workdir': '/work',
        }
        self.assertEqual(
            minieval.replace_tokens(value, tokens),
            'python /tmp/run {workdir}/instruction.md /work {"ordinary": "braces"}',
        )

    def test_remove_path_does_not_follow_a_symlink(self):
        target = self.write('original/file.txt', 'keep me')
        link = os.path.join(self.directory, 'link')
        os.symlink(os.path.dirname(target), link)
        minieval.remove_path(link)

        self.assertFalse(os.path.lexists(link))
        self.assertEqual(minieval.read_text(target), 'keep me')

    def test_task_hash_ignores_generated_metadata(self):
        root = self.task('one')
        before = minieval.hash_tree(root)
        self.write('one/.git/config', 'generated metadata')
        self.write('one/__pycache__/cached.pyc', 'generated metadata')
        self.assertEqual(minieval.hash_tree(root), before)
        self.write('one/instruction.md', '# A changed assignment\n')
        self.assertNotEqual(minieval.hash_tree(root), before)

    def test_task_hash_covers_directory_symlinks(self):
        root = self.task('one')
        os.mkdir(os.path.join(self.directory, 'target-a'))
        os.mkdir(os.path.join(self.directory, 'target-b'))
        link = os.path.join(root, 'linked-data')
        os.symlink('../target-a', link)
        before = minieval.hash_tree(root)
        os.unlink(link)
        os.symlink('../target-b', link)

        self.assertNotEqual(minieval.hash_tree(root), before)

    def test_failed_or_timed_out_agent_cannot_claim_success(self):
        passed = minieval.CommandResult(0, 0.1)
        failed = minieval.CommandResult(1, 0.1)
        timeout = minieval.CommandResult(-9, 0.1, timed_out=True)
        cases = [
            (failed, passed, 'agent_error'),
            (timeout, passed, 'agent_timeout'),
            (passed, failed, 'failed'),
            (passed, timeout, 'test_timeout'),
            (passed, minieval.CommandResult(2, 0.1), 'grader_error'),
            (passed, passed, 'passed'),
        ]
        for agent, verifier, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(minieval.classify_result(agent, verifier), expected)

    def test_external_adapter_receives_the_request_and_clean_argument_boundaries(self):
        path = self.write('capture.py', (
            'import json\n'
            'import sys\n'
            'with open(sys.argv[1], "w") as f:\n'
            '    json.dump({"args": sys.argv[2:], "request": json.load(sys.stdin)}, f)\n'
        ))
        capture_path = os.path.join(self.directory, 'request.json')
        request = {
            'container_id': 'a' * 64,
            'output_dir': self.directory,
            'instruction_file': '/tmp/a task/instruction.md',  # noqa
            'instruction': 'Fix the example.\nKeep the interface unchanged.',
        }
        agent = minieval.load_agent(
            'external',
            self.directory,
            [sys.executable, path, capture_path, '{container_id}', '{instruction_file}'],
        )
        task = minieval.Task('example', self.directory, request['instruction'])
        result = minieval.run_agent(
            None,  # type: ignore
            agent,
            task,
            request,
            timeout=10,
            extra_args=['{"literal": "braces"}'],
            extra_env=[],
        )

        self.assertEqual(result.returncode, 0)
        captured = json.loads(minieval.read_text(capture_path))
        self.assertEqual(captured['request'], request)
        self.assertEqual(captured['args'], [
            'a' * 64,
            '/tmp/a task/instruction.md',  # noqa
            '{"literal": "braces"}',
        ])

    def test_bundled_container_agent_configs_load(self):
        root = os.path.dirname(os.path.abspath(minieval.__file__))
        for name in ('codex', 'claude', 'pi'):
            with self.subTest(name=name):
                agent = minieval.load_agent(name, os.path.join(root, 'agents'), [])
                self.assertEqual(agent.kind, 'container')
                self.assertEqual(agent.user, 'agent')
                self.assertTrue(agent.command)
                self.assertTrue(os.path.isfile(os.path.join(agent.directory, agent.dockerfile)))

    def test_start_failure_still_removes_the_created_container(self):
        path = self.task('example')
        docker = FailingDocker('start')
        result = minieval.run_trial(
            docker,
            minieval.Task('example', path, 'Repair this task'),
            minieval.Agent('nop', 'nop'),
            task_image='test-image',
            agent_image='test-image',
            output_dir=os.path.join(self.directory, 'attempt'),
            timeout=1,
            test_timeout=1,
        )

        self.assertEqual(result['status'], 'infrastructure_error')
        self.assertIn(['rm', '-f', 'a' * 64], docker.calls)
        self.assertFalse(result.get('cleanup_errors'))

    def test_interrupted_creation_cleans_up_by_registered_name(self):
        path = self.task('example')
        docker = FailingDocker('create')
        output = os.path.join(self.directory, 'attempt')
        with self.assertRaises(KeyboardInterrupt):
            minieval.run_trial(
                docker,
                minieval.Task('example', path, 'Repair this task'),
                minieval.Agent('nop', 'nop'),
                task_image='test-image',
                agent_image='test-image',
                output_dir=output,
                timeout=1,
                test_timeout=1,
            )

        result = json.loads(minieval.read_text(os.path.join(output, 'result.json')))
        self.assertEqual(result['status'], 'interrupted')
        self.assertEqual(len(result['containers']), 1)
        name = result['containers'][0]
        self.assertTrue(name.startswith('minieval-'))
        self.assertIn(['rm', '-f', name], docker.calls)
