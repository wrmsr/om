import pytest

from . import native
from .tests.dbs import DB_KWARGS


@pytest.fixture(scope='session')
def db_setup():
    with native.Connection(**DB_KWARGS) as con:
        con.run('CREATE EXTENSION IF NOT EXISTS hstore')

        # Clear any ssl override left in postgresql.auto.conf by a previous run killed inside the scram auth tests,
        # which toggle ssl off for their duration.
        con.run('ALTER SYSTEM RESET ssl')
        con.run('SELECT pg_reload_conf()')


@pytest.fixture(scope='session')
def pg_server_ssl(db_setup):
    """Whether the server accepts SSL connections."""

    with native.Connection(**DB_KWARGS) as con:
        return con.is_ssl


@pytest.fixture
def db_kwargs(db_setup):
    """A fresh copy of the connection parameters for the test database. The canonical way for tests to obtain them."""

    return dict(DB_KWARGS)
