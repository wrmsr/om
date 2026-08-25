import typing as ta
import types
import urllib.parse
import pytest

from omcore import check
from omcore.sql.tests.harness import HarnessDbs
from omcore import sql

from . import native


class Database(ta.TypedDict):
    host: str
    port: int
    user: str
    password: str


@pytest.fixture(scope='session')
def _database(harness) -> Database:
    spec = harness[HarnessDbs].specs()['postgres']
    url = check.isinstance(spec.loc, sql.UrlDbLoc)
    pu = urllib.parse.urlparse(check.isinstance(url.url, str))
    return types.MappingProxyType({  # noqa
        'host': pu.hostname,
        'port': pu.port,
        'user': pu.username,
        'password': pu.password,
    })


@pytest.fixture(scope='session')
def db_setup(_database):
    with native.Connection(**_database) as con:
        con.run('CREATE EXTENSION IF NOT EXISTS hstore')

        # Clear any ssl override left in postgresql.auto.conf by a previous run killed inside the scram auth tests,
        # which toggle ssl off for their duration.
        con.run('ALTER SYSTEM RESET ssl')
        con.run('SELECT pg_reload_conf()')


@pytest.fixture(scope='session')
def pg_server_ssl(_database, db_setup):
    """Whether the server accepts SSL connections."""

    with native.Connection(**_database) as con:
        return con.is_ssl


@pytest.fixture
def db_kwargs(_database, db_setup):
    """A fresh copy of the connection parameters for the test database. The canonical way for tests to obtain them."""

    return dict(_database)
