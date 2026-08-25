import pytest

from ... import dbapi
from ..utils import parse_server_version


@pytest.fixture
def con(request, db_kwargs):
    conn = dbapi.connect(**db_kwargs)

    yield conn

    try:
        conn.rollback()
    except dbapi.InterfaceError:
        pass

    try:
        conn.close()
    except dbapi.InterfaceError:
        pass


@pytest.fixture
def cursor(request, con):
    cursor = con.cursor()

    yield cursor

    cursor.close()


@pytest.fixture
def pg_version(cursor):
    cursor.execute("select current_setting('server_version')")
    retval = cursor.fetchall()
    version = retval[0][0]
    major = parse_server_version(version)
    return major
