import pytest

from ... import dbapi
from ..utils import parse_server_version


@pytest.fixture
def con(request, db_kwargs):
    conn = dbapi.connect(**db_kwargs)

    def fin():
        try:
            conn.rollback()
        except dbapi.InterfaceError:
            pass

        try:
            conn.close()
        except dbapi.InterfaceError:
            pass

    request.addfinalizer(fin)
    return conn


@pytest.fixture
def cursor(request, con):
    cursor = con.cursor()

    def fin():
        cursor.close()

    request.addfinalizer(fin)
    return cursor


@pytest.fixture
def pg_version(cursor):
    cursor.execute("select current_setting('server_version')")
    retval = cursor.fetchall()
    version = retval[0][0]
    major = parse_server_version(version)
    return major
