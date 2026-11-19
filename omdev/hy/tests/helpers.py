import contextlib
import functools
import os
import typing as ta
import warnings

from ..finders import PackageHyModuleFinder
from ..importing import IsolatedHyModules
from ..runtime import HyRuntime


##


# The Hy package itself, and its directory relative to the repo root (which is the tests' working directory).
PACKAGE = __package__.rpartition('.')[0]
PACKAGE_DIR = os.path.join(*PACKAGE.split('.'))

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
REPO_PYTHON = os.path.join(REPO_ROOT, 'python')


def new_test_runtime() -> HyRuntime:
    return HyRuntime(modules=functools.partial(
        IsolatedHyModules,
        finders=[PackageHyModuleFinder(prefixes=[PACKAGE])],
    ))


@contextlib.contextmanager
def filter_native_test_syntax_warnings() -> ta.Iterator[None]:
    # These tests deliberately compile literal calls to check Hy's parsing and runtime behavior, not Python's warnings.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore',
            message=r"^'str' object is not callable; perhaps you missed a comma\?$",
            category=SyntaxWarning,
            module=r'.*[/\\]native_tests[/\\](comprehensions|conditional|other|try)\.hy$',
        )
        warnings.filterwarnings(
            'ignore',
            message=r"^'NoneType' object is not callable; perhaps you missed a comma\?$",
            category=SyntaxWarning,
            module=r'.*[/\\]native_tests[/\\]setv\.hy$',
        )
        yield
