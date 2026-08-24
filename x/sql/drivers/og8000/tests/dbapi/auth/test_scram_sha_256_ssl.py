from ssl import CERT_NONE
from ssl import create_default_context

import pytest

from ....dbapi import DatabaseError
from ....dbapi import connect


# This requires a line in pg_hba.conf that requires scram-sha-256 for the database test_og8000_scram_sha_256

DB = 'test_og8000_scram_sha_256'


@pytest.fixture
def setup(con, cursor):
    con.autocommit = True
    try:
        cursor.execute(f'CREATE DATABASE {DB}')
    except DatabaseError:
        con.rollback()
    yield
    cursor.execute(f'DROP DATABASE IF EXISTS {DB} WITH (FORCE)')


def test_scram_sha_256(setup, db_kwargs):
    db_kwargs['database'] = DB

    con = connect(**db_kwargs)
    con.close()


def test_scram_sha_256_ssl_context(setup, db_kwargs, pg_server_ssl):
    if not pg_server_ssl:
        pytest.skip('server does not accept SSL')

    ssl_context = create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = CERT_NONE

    db_kwargs['database'] = DB
    db_kwargs['ssl_context'] = ssl_context

    con = connect(**db_kwargs)
    con.close()
