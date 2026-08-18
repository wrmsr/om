# ruff: noqa: PTH100 PTH118 PTH123 PT009 UP006 UP007 UP036 UP045
import ast
import os.path
import runpy
import sys
import tempfile
import types
import typing as ta
import unittest


_SYSTEVISOR_TEST_AMALG_ROOT = os.path.dirname(os.path.dirname(__file__))
_SYSTEVISOR_TEST_AMALG_MAIN = os.path.join(_SYSTEVISOR_TEST_AMALG_ROOT, '__main__.py')
_SYSTEVISOR_TEST_AMALG_ARTIFACT = os.path.join(_SYSTEVISOR_TEST_AMALG_ROOT, '_bin', 'systevisor.py')
_SYSTEVISOR_TEST_AMALG_REPO_ROOT = os.path.abspath(os.path.join(_SYSTEVISOR_TEST_AMALG_ROOT, '..', '..'))
_SYSTEVISOR_TEST_AMALG_STDLIB_ROOTS = {
    'abc',
    'argparse',
    'base64',
    'collections',
    'configparser',
    'contextlib',
    'contextvars',
    'ctypes',
    'dataclasses',
    'datetime',
    'decimal',
    'enum',
    'errno',
    'fcntl',
    'fractions',
    'functools',
    'grp',
    'hashlib',
    'heapq',
    'http',
    'inspect',
    'io',
    'json',
    'logging',
    'math',
    'operator',
    'os',
    'pwd',
    're',
    'resource',
    'select',
    'signal',
    'socket',
    'stat',
    'string',
    'sys',
    'syslog',
    'tempfile',
    'threading',
    'time',
    'traceback',
    'types',
    'typing',
    'urllib',
    'uuid',
    'weakref',
    'xml',
    'zlib',
}


def _systevisor_test_generate_amalgamation() -> str:
    from omdev.amalg.gen.gen import AmalgGenerator

    return AmalgGenerator(
        _SYSTEVISOR_TEST_AMALG_MAIN,
        mounts={'omcore': os.path.join(_SYSTEVISOR_TEST_AMALG_REPO_ROOT, 'omcore')},
        output_dir=os.path.dirname(_SYSTEVISOR_TEST_AMALG_ARTIFACT),
    ).gen_amalg()


class TestSystevisorAmalgamation(unittest.TestCase):
    _source: ta.ClassVar[str]

    @classmethod
    def setUpClass(cls) -> None:
        if sys.version_info >= (3, 9):
            cls._source = _systevisor_test_generate_amalgamation()
        else:
            with open(_SYSTEVISOR_TEST_AMALG_ARTIFACT) as artifact_file:
                cls._source = artifact_file.read()

    def test_is_self_contained_and_loadable(self) -> None:
        tree = ast.parse(self._source, filename='systevisor.py')
        imported_roots: ta.Set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.partition('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                if node.module is not None:
                    imported_roots.add(node.module.partition('.')[0])
        self.assertEqual(imported_roots - _SYSTEVISOR_TEST_AMALG_STDLIB_ROOTS, set())

        module_name = 'systevisor_amalgamation_test'
        module = types.ModuleType(module_name)
        sys.modules[module_name] = module
        try:
            exec(compile(tree, 'systevisor.py', 'exec'), module.__dict__)
        finally:
            del sys.modules[module_name]
        self.assertIn('systevisor_main', module.__dict__)

    @unittest.skipIf(sys.version_info < (3, 9), 'the development amalgamator requires Python 3.9+')
    def test_matches_checked_in_artifact(self) -> None:
        with open(_SYSTEVISOR_TEST_AMALG_ARTIFACT) as artifact_file:
            self.assertEqual(artifact_file.read(), self._source)

    def test_runs_without_package_imports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = os.path.join(temp_dir, 'systevisor.py')
            with open(artifact_path, 'w') as artifact_file:
                artifact_file.write(self._source)
            namespace = runpy.run_path(artifact_path, run_name='systevisor_amalgamation_isolated_test')
            self.assertIn(namespace['__package__'], (None, ''))
            self.assertTrue(callable(namespace['systevisor_main']))
