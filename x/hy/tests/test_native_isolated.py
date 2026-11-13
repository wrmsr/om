"""
The native tests are normally run by importing them through the global runtime - here, they're additionally each run
inside of a fresh, isolated runtime (which finds them, and the resources they import, through a
`PackageHyModuleFinder`). Native tests requiring fixtures are skipped.
"""
import asyncio
import functools
import inspect
import os
import sys

import pytest

from ..finders import PackageHyModuleFinder
from ..importing import IsolatedHyModules
from ..runtime import HyRuntime


##


_NATIVE_TESTS_DIR = os.path.join(os.path.dirname(__file__), 'native_tests')

_NATIVE_TEST_MODULES = sorted(
    os.path.splitext(f)[0]
    for f in os.listdir(_NATIVE_TESTS_DIR)
    if f.endswith('.hy') and f != '__init__.hy'
)

# Source inspection requires the `inspect` patching done only by installing the global runtime.
_GLOBAL_ONLY_TESTS = {
    ('hy_inspect', 'test_reader'),
    ('hy_inspect', 'test_getdoc_inherited'),
    ('hy_inspect', 'test_getcomments'),
    ('hy_inspect', 'test_getsource'),
}


@pytest.mark.parametrize('name', _NATIVE_TEST_MODULES)
def test_native_isolated(name):
    pkg = __package__.rpartition('.')[0]
    mod_name = f'{__package__}.native_tests.{name}'

    rt = HyRuntime(modules=functools.partial(IsolatedHyModules, finders=[PackageHyModuleFinder(prefixes=[pkg])]))
    mod = rt.import_module(mod_name)
    assert sys.modules.get(mod_name) is not mod

    failures = []
    for k, v in list(vars(mod).items()):
        if not k.startswith('test_') or not callable(v) or inspect.signature(v).parameters:
            continue
        if (name, k) in _GLOBAL_ONLY_TESTS:
            continue

        try:
            if inspect.iscoroutine(r := v()):
                asyncio.run(r)
        except Exception as e:  # noqa: BLE001
            failures.append(f'{k}: {type(e).__name__}: {e}')

    assert not failures
