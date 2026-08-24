import pytest

from .. import omysql
from .tests.dbs import DATABASES


@pytest.fixture(scope='session')
def mysql_server_params():
    """Connection parameters for the MySQL server itself, with no database selected. Root credentials, per the config."""

    return {k: v for k, v in DATABASES[0].items() if k != 'database'}


@pytest.fixture(scope='session')
def mysql_bootstrap(mysql_server_params):
    """
    Creates the configured test databases and enables local_infile, undoing both afterwards. Everything it does is
    idempotent, so leftovers from a previous run killed at any point are absorbed.
    """

    con = omysql.connect(**mysql_server_params)
    try:
        cur = con.cursor()

        cur.execute('select @@global.local_infile')
        prior_local_infile = bool(cur.fetchone()[0])
        cur.execute('set global local_infile = 1')

        for params in DATABASES:
            cur.execute(f'create database if not exists `{params["database"]}`')

        yield

        for params in DATABASES:
            cur.execute(f'drop database if exists `{params["database"]}`')

        cur.execute(f'set global local_infile = {1 if prior_local_infile else 0}')
    finally:
        con.close()


@pytest.fixture
def databases(mysql_bootstrap):
    """
    Fresh copies of the connection parameter sets for the configured test databases. The canonical way for tests to
    obtain them: the first entry is the primary test database, the second a secondary one.
    """

    return [dict(params) for params in DATABASES]
