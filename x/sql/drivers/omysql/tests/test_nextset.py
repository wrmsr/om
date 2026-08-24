import pytest

from ... import omysql
from ..constants import CLIENT


def test_nextset(connect):
    con = connect(
        init_command='SELECT "bar"; SELECT "baz"',
        client_flag=CLIENT.MULTI_STATEMENTS,
    )
    cur = con.cursor()
    cur.execute('SELECT 1; SELECT 2;')
    assert list(cur) == [(1,)]

    r = cur.nextset()
    assert r

    assert list(cur) == [(2,)]
    assert cur.nextset() is None


def test_skip_nextset(connect):
    cur = connect(client_flag=CLIENT.MULTI_STATEMENTS).cursor()
    cur.execute('SELECT 1; SELECT 2;')
    assert list(cur) == [(1,)]

    cur.execute('SELECT 42')
    assert list(cur) == [(42,)]


def test_nextset_error(connect):
    con = connect(client_flag=CLIENT.MULTI_STATEMENTS)
    cur = con.cursor()

    for i in range(3):
        cur.execute('SELECT %s; xyzzy;', (i,))
        assert list(cur) == [(i,)]
        with pytest.raises(omysql.ProgrammingError):
            cur.nextset()
        assert cur.fetchall() == []


def test_ok_and_next(connect):
    cur = connect(client_flag=CLIENT.MULTI_STATEMENTS).cursor()
    cur.execute('SELECT 1; commit; SELECT 2;')
    assert list(cur) == [(1,)]
    assert cur.nextset()
    assert cur.nextset()
    assert list(cur) == [(2,)]
    assert not bool(cur.nextset())


@pytest.mark.xfail
def test_multi_cursor(connect):
    con = connect(client_flag=CLIENT.MULTI_STATEMENTS)
    cur1 = con.cursor()
    cur2 = con.cursor()

    cur1.execute('SELECT 1; SELECT 2;')
    cur2.execute('SELECT 42')

    assert list(cur1) == [(1,)]
    assert list(cur2) == [(42,)]

    r = cur1.nextset()
    assert r

    assert list(cur1) == [(2,)]
    assert cur1.nextset() is None


def test_multi_statement_warnings(connect):
    con = connect(
        init_command='SELECT "bar"; SELECT "baz"',
        client_flag=CLIENT.MULTI_STATEMENTS,
    )
    cursor = con.cursor()

    # Must not raise (this once raised a TypeError from warning handling).
    cursor.execute('DROP TABLE IF EXISTS a; DROP TABLE IF EXISTS b;')


# TODO: How about SSCursor and nextset?
# It's very hard to implement correctly...
