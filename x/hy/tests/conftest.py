import os.path

import pytest

from .. import globalruntime


##


def pytest_collect_file(file_path, parent):
    # Most of these tests - and in particular the native tests, which are Hy modules imported (and so collected) through
    # Python's import system - exercise the global runtime, and so require it be installed.
    globalruntime.install()

    if (
        file_path.suffix == '.hy' and
        'native_tests' in os.path.relpath(file_path, os.path.dirname(__file__)).split(os.path.sep) and
        file_path.name != '__init__.hy'
    ):
        return pytest.Module.from_parent(parent, path=file_path)
    return None
