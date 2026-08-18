# ruff: noqa: PTH100 PTH118 PTH123 PT009 UP006 UP007 UP045
import ast
import os.path
import typing as ta
import unittest


_SYSTEVISOR_TEST_SOURCE_ROOT = os.path.dirname(os.path.dirname(__file__))

_SYSTEVISOR_TEST_GLOBAL_NAME_PREFIXES = (
    'Systevisor',
    'SYSTEVISOR_',
    '_SYSTEVISOR_',
    'systevisor_',
    '_systevisor_',
    '__',
)

_SYSTEVISOR_TEST_PROCESS_CALL_ALLOWLIST = {
    os.path.join('runtime', 'processes.py'): {
        ('os', 'kill'),
        ('os', 'killpg'),
        ('os', 'wait'),
        ('os', 'wait3'),
        ('os', 'wait4'),
        ('os', 'waitid'),
        ('os', 'waitpid'),
        ('signal', 'pidfd_send_signal'),
    },
}

_SYSTEVISOR_TEST_PROCESS_CALLS = {
    ('os', 'kill'),
    ('os', 'killpg'),
    ('os', 'wait'),
    ('os', 'wait3'),
    ('os', 'wait4'),
    ('os', 'waitid'),
    ('os', 'waitpid'),
    ('signal', 'pidfd_send_signal'),
}


def _systevisor_test_source_paths() -> ta.Iterator[str]:
    for dir_path, dir_names, file_names in os.walk(_SYSTEVISOR_TEST_SOURCE_ROOT):
        dir_names[:] = [
            name
            for name in dir_names
            if name not in {'_bin', '_devdocs', '__pycache__', 'tests'}
        ]
        for file_name in file_names:
            if file_name.endswith('.py'):
                yield os.path.join(dir_path, file_name)


def _systevisor_test_parse_source(path: str) -> ast.Module:
    with open(path) as source_file:
        return ast.parse(source_file.read(), filename=path)


def _systevisor_test_assigned_names(node: ast.AST) -> ta.Iterator[str]:
    if isinstance(node, ast.Name):
        yield node.id
    elif isinstance(node, (ast.Tuple, ast.List)):
        for element in node.elts:
            yield from _systevisor_test_assigned_names(element)


class TestSystevisorSourceGuards(unittest.TestCase):
    def test_amalgamation_safe_global_names(self) -> None:
        bad: ta.List[ta.Tuple[str, int, str]] = []
        for path in _systevisor_test_source_paths():
            tree = _systevisor_test_parse_source(path)
            for node in tree.body:
                names: ta.Iterable[str]
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    names = [node.name]
                elif isinstance(node, ast.Assign):
                    names = [
                        name
                        for target in node.targets
                        for name in _systevisor_test_assigned_names(target)
                    ]
                elif isinstance(node, ast.AnnAssign):
                    names = list(_systevisor_test_assigned_names(node.target))
                else:
                    continue

                for name in names:
                    if not name.startswith(_SYSTEVISOR_TEST_GLOBAL_NAME_PREFIXES):
                        bad.append((os.path.relpath(path, _SYSTEVISOR_TEST_SOURCE_ROOT), node.lineno, name))

        self.assertEqual(bad, [])

    def test_process_control_calls_are_confined(self) -> None:
        bad: ta.List[ta.Tuple[str, int, str]] = []
        for path in _systevisor_test_source_paths():
            relative_path = os.path.relpath(path, _SYSTEVISOR_TEST_SOURCE_ROOT)
            allowed = _SYSTEVISOR_TEST_PROCESS_CALL_ALLOWLIST.get(relative_path, set())
            tree = _systevisor_test_parse_source(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if not isinstance(node.func.value, ast.Name):
                    continue
                call = (node.func.value.id, node.func.attr)
                if call in _SYSTEVISOR_TEST_PROCESS_CALLS and call not in allowed:
                    bad.append((relative_path, node.lineno, '.'.join(call)))

        self.assertEqual(bad, [])

    def test_process_control_imports_are_confined(self) -> None:
        bad: ta.List[ta.Tuple[str, int, str]] = []
        protected_names = {
            call_name
            for module_name, call_name in _SYSTEVISOR_TEST_PROCESS_CALLS
            if module_name == 'os'
        }
        for path in _systevisor_test_source_paths():
            relative_path = os.path.relpath(path, _SYSTEVISOR_TEST_SOURCE_ROOT)
            if relative_path in _SYSTEVISOR_TEST_PROCESS_CALL_ALLOWLIST:
                continue
            tree = _systevisor_test_parse_source(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or node.module != 'os':
                    continue
                for alias in node.names:
                    if alias.name in protected_names:
                        bad.append((relative_path, node.lineno, alias.name))

        self.assertEqual(bad, [])

    def test_no_subprocess_runtime(self) -> None:
        bad: ta.List[ta.Tuple[str, int, str]] = []
        for path in _systevisor_test_source_paths():
            relative_path = os.path.relpath(path, _SYSTEVISOR_TEST_SOURCE_ROOT)
            tree = _systevisor_test_parse_source(path)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    modules = (
                        [alias.name for alias in node.names]
                        if isinstance(node, ast.Import)
                        else [node.module or '']
                    )
                    for module in modules:
                        if module == 'subprocess' or module.startswith('asyncio.subprocess'):
                            bad.append((relative_path, node.lineno, module))

        self.assertEqual(bad, [])
