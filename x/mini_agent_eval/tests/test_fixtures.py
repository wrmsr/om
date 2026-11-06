"""Validate the starter tasks' behavior locally, independently of Docker."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from .. import minieval


##


class FixtureTest(unittest.TestCase):
    def check_fixture(self, task, *, reference=False, visible=False):
        with tempfile.TemporaryDirectory(prefix='mini eval fixture ') as directory:
            workspace = os.path.join(directory, 'work')
            shutil.copytree(
                os.path.join(task.path, 'environment'),
                workspace,
                ignore=shutil.ignore_patterns('Dockerfile', '__pycache__', '.git'),
            )
            if reference:
                solution = os.path.join(task.path, 'solution')
                files = [name for name in os.listdir(solution) if name.endswith('.py')]
                self.assertTrue(files, f'No reference Python files found for {task.name}')
                for name in files:
                    shutil.copy2(os.path.join(solution, name), os.path.join(workspace, name))
            tests = workspace if visible else os.path.join(task.path, 'tests')
            pattern = 'test_visible.py' if visible else 'test_*.py'
            result = subprocess.run(  # noqa
                [sys.executable, '-m', 'unittest', 'discover', '-s', tests, '-p', pattern, '-v'],
                cwd=workspace,
                env=os.environ | {'PYTHONPATH': workspace, 'PYTHONDONTWRITEBYTECODE': '1'},
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=60,
            )

        self.assertRegex(result.stdout, r'Ran [1-9][0-9]* tests? in ', result.stdout)
        self.assertNotIn('Failed to import test module', result.stdout)
        self.assertEqual(result.returncode, 0 if reference or visible else 1, result.stdout)

    def get_tasks(self):
        root = os.path.dirname(os.path.abspath(minieval.__file__))
        return minieval.load_tasks(os.path.join(root, 'tasks'))

    def test_visible_tests_pass_on_starters(self):
        for task in self.get_tasks():
            with self.subTest(task=task.name):
                self.check_fixture(task, visible=True)

    def test_hidden_tests_reject_starters(self):
        for task in self.get_tasks():
            with self.subTest(task=task.name):
                self.check_fixture(task)

    def test_reference_solutions_pass_hidden_tests(self):
        for task in self.get_tasks():
            with self.subTest(task=task.name):
                self.check_fixture(task, reference=True)
