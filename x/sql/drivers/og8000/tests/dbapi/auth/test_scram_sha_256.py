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

    # Toggled off so the connection under test is plain scram, not scram over TLS. RESET (rather than SET ssl = on)
    # restores whatever the server was configured with, and a leftover override from a killed run is cleared by the
    # session-level db_setup fixture.
    cursor.execute('ALTER SYSTEM SET ssl = off')
    cursor.execute('SELECT pg_reload_conf()')
    yield
    cursor.execute('ALTER SYSTEM RESET ssl')
    cursor.execute('SELECT pg_reload_conf()')
    cursor.execute(f'DROP DATABASE IF EXISTS {DB} WITH (FORCE)')


def test_scram_sha_256(setup, db_kwargs):
    db_kwargs['database'] = DB

    with connect(**db_kwargs):
        pass
