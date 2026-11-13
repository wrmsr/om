import os

from ..globalruntime import get_global_runtime
from ..runtime import HyNamespace


##


# The Hy package itself, and its directory relative to the repo root (which is the tests' working directory).
PACKAGE = __package__.rpartition('.')[0]
PACKAGE_DIR = os.path.join(*PACKAGE.split('.'))

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
REPO_PYTHON = os.path.join(REPO_ROOT, 'python')


def global_hy() -> HyNamespace:
    """The `hy` of the global runtime, which the conftest installs."""

    return get_global_runtime().hy
