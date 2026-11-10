import os.path

import pytest

from ... import hy  # noqa: F401  # Register the Hy import hooks.


##


def pytest_collect_file(file_path, parent):
    if (
        file_path.suffix == '.hy' and
        'native_tests' in os.path.relpath(file_path, os.path.dirname(__file__)).split(os.path.sep) and
        file_path.name != '__init__.hy'
    ):
        return pytest.Module.from_parent(parent, path=file_path)
    return None
