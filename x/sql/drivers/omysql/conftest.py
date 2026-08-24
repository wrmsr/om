import pytest

from .tests.dbs import DATABASES


@pytest.fixture
def databases():
    """
    Fresh copies of the connection parameter sets for the configured test databases. The canonical way for tests to
    obtain them: the first entry is the primary test database, the second a secondary one.
    """

    return [dict(params) for params in DATABASES]
