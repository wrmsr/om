import warnings

import pytest

from ... import omysql
from .dbs import DATABASES


def _drop_table(connection, tablename):
    cursor = connection.cursor()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        cursor.execute(f'drop table if exists `{tablename}`')
    cursor.close()


@pytest.fixture
def connections():
    """Open connections to each of the configured test databases, all closed after the test."""

    conns = [omysql.connect(**params) for params in DATABASES]
    yield conns
    for conn in conns:
        if conn.open:
            conn.close()


@pytest.fixture
def connect():
    """A factory for connections to the first test database, all closed after the test."""

    conns = []

    def make(**params):
        p = dict(DATABASES[0])
        p.update(params)
        conn = omysql.connect(**p)
        conns.append(conn)
        return conn

    make.conns = conns
    yield make
    for conn in conns:
        if conn.open:
            conn.close()


@pytest.fixture
def safe_create_table(connect):
    """
    A factory that creates a table, first dropping any existing version of it, and drops it again after the test.

    Depending on the `connect` fixture orders this fixture's teardown before its connections are closed, so the drops
    run on the given, still-open connections.
    """

    created = []

    def create(connection, tablename, ddl):
        _drop_table(connection, tablename)
        cursor = connection.cursor()
        cursor.execute(ddl)
        cursor.close()
        created.append((connection, tablename))

    yield create

    # End any transactions still open on this test's factory connections, so the drops below don't block on the shared
    # metadata locks those transactions would hold.
    for conn in connect.conns:
        if conn.open:
            conn.rollback()

    for connection, tablename in reversed(created):
        if connection.open:
            _drop_table(connection, tablename)
        else:
            conn = omysql.connect(**DATABASES[0])
            try:
                _drop_table(conn, tablename)
            finally:
                conn.close()
