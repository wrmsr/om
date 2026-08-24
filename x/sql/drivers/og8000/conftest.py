import pytest

from . import native
from .tests.dbs import DB_KWARGS


@pytest.fixture(scope='session')
def db_setup():
    with native.Connection(**DB_KWARGS) as con:
        con.run('CREATE EXTENSION IF NOT EXISTS hstore')


@pytest.fixture
def db_kwargs(db_setup):
    """A fresh copy of the connection parameters for the test database. The canonical way for tests to obtain them."""

    return dict(DB_KWARGS)
