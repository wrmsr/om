import pytest

from ....errors import DatabaseError
from ....native import Connection
from ....native import InterfaceError


# This requires a line in pg_hba.conf that requires scram-sha-256 for the database test_og8000_scram_sha_256

DB = 'test_og8000_scram_sha_256'


@pytest.fixture
def setup(con):
    try:
        con.run(f'CREATE DATABASE {DB}')
    except DatabaseError:
        pass

    # Toggled off so the connection under test is plain scram, not scram over TLS. RESET (rather than SET ssl = on)
    # restores whatever the server was configured with, and a leftover override from a killed run is cleared by the
    # session-level db_setup fixture.
    con.run('ALTER SYSTEM SET ssl = off')
    con.run('SELECT pg_reload_conf()')
    yield
    con.run('ALTER SYSTEM RESET ssl')
    con.run('SELECT pg_reload_conf()')
    con.run(f'DROP DATABASE IF EXISTS {DB} WITH (FORCE)')


def test_scram_sha_256(setup, db_kwargs):
    db_kwargs['database'] = DB

    with Connection(**db_kwargs):
        pass


def test_scram_sha_256_ssl_False(setup, db_kwargs):
    db_kwargs['database'] = DB
    db_kwargs['ssl_context'] = False

    with Connection(**db_kwargs):
        pass


def test_scram_sha_256_ssl_True(setup, db_kwargs):
    db_kwargs['database'] = DB
    db_kwargs['ssl_context'] = True

    with pytest.raises(InterfaceError, match='Server refuses SSL'):
        with Connection(**db_kwargs):
            pass
