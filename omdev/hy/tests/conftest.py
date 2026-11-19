import functools
import importlib.util
import os.path
import sys

import pytest

from .. import globalruntime
from ..finders import PackageHyModuleFinder
from ..importing import IsolatedHyModules
from ..runtime import HyRuntime
from .helpers import filter_native_test_syntax_warnings


##


class _HyNativeTestModule(pytest.Module):
    def _getobj(self):
        name = f'{__package__}.native_tests.{self.path.stem}'
        if self.config.getoption('hy_global_tests'):
            loader = globalruntime.HyLoader(name, str(self.path))
            spec = importlib.util.spec_from_loader(name, loader)
            assert spec is not None
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            with filter_native_test_syntax_warnings():
                loader.exec_module(module)
            return module

        pkg = __package__.rpartition('.')[0]
        runtime = HyRuntime(modules=functools.partial(
            IsolatedHyModules,
            finders=[PackageHyModuleFinder(prefixes=[pkg])],
        ))
        with filter_native_test_syntax_warnings():
            module = runtime.import_module(name)
        assert sys.modules.get(name) is not module
        return module


_HY_GLOBAL_NATIVE_TESTS = {
    'hy_misc.hy': {'test_hyI_mangle_chain'},
    'import.hy': {'test_no_surprise_shadow'},
    'other.hy': {'test_pydoc'},
}
_HY_NATIVE_TEST_DIR = os.path.join(os.path.dirname(__file__), 'native_tests')


def pytest_addoption(parser):
    parser.addoption('--hy-global-tests', action='store_true', help='Run quarantined Hy global runtime cases')


def pytest_sessionstart(session):
    if session.config.getoption('hy_global_tests'):
        globalruntime.install()


def pytest_collect_file(file_path, parent):
    if (
        file_path.suffix == '.hy' and
        'native_tests' in os.path.relpath(file_path, os.path.dirname(__file__)).split(os.path.sep) and
        file_path.name != '__init__.hy'
    ):
        if file_path.name in ('hy_inspect.hy', 'repl.hy') and not parent.config.getoption('hy_global_tests'):
            return None
        return _HyNativeTestModule.from_parent(parent, path=file_path)
    return None


def pytest_collection_modifyitems(config, items):
    if config.getoption('hy_global_tests'):
        return

    kept = []
    quarantined = []
    for item in items:
        if (
            os.path.dirname(str(item.path)) == _HY_NATIVE_TEST_DIR and
            item.name in _HY_GLOBAL_NATIVE_TESTS.get(item.path.name, ())
        ):
            quarantined.append(item)
        else:
            kept.append(item)
    items[:] = kept
    if quarantined:
        config.hook.pytest_deselected(items=quarantined)
