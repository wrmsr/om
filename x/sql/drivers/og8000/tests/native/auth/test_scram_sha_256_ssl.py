from ssl import CERT_NONE
from ssl import create_default_context

import pytest

from ....errors import DatabaseError
from ....native import Connection


# This requires a line in pg_hba.conf that requires scram-sha-256 for the database test_og8000_scram_sha_256

DB = 'test_og8000_scram_sha_256'


@pytest.fixture
def setup(con, pg_server_ssl):
    if not pg_server_ssl:
        pytest.skip('server does not accept SSL')

    try:
        con.run(f'CREATE DATABASE {DB}')
    except DatabaseError:
        pass
    yield
    con.run(f'DROP DATABASE IF EXISTS {DB} WITH (FORCE)')


def test_scram_sha_256_plus(setup, db_kwargs):
    db_kwargs['database'] = DB

    with Connection(**db_kwargs) as con:
        assert con.is_ssl


def test_scram_sha_256_plus_ssl_True(setup, db_kwargs):
    db_kwargs['ssl_context'] = True
    db_kwargs['database'] = DB

    with Connection(**db_kwargs) as con:
        assert con.is_ssl


def test_scram_sha_256_plus_ssl_custom(setup, db_kwargs):
    context = create_default_context()
    context.check_hostname = False
    context.verify_mode = CERT_NONE

    db_kwargs['ssl_context'] = context
    db_kwargs['database'] = DB

    with Connection(**db_kwargs) as con:
        assert con.is_ssl


def test_scram_sha_256_plus_ssl_False(setup, db_kwargs):
    db_kwargs['ssl_context'] = False
    db_kwargs['database'] = DB

    with Connection(**db_kwargs) as con:
        assert not con.is_ssl
