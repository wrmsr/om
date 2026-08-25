import pytest

from ... import native
from ..utils import parse_server_version


@pytest.fixture
def con(request, db_kwargs):
    conn = native.Connection(**db_kwargs)

    yield conn

    try:
        conn.run('rollback')
    except native.InterfaceError:
        pass

    try:
        conn.close()
    except native.InterfaceError:
        pass


@pytest.fixture
def pg_version(con):
    retval = con.run("select current_setting('server_version')")
    version = retval[0][0]
    major = parse_server_version(version)
    return major
