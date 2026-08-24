import datetime
import warnings

import pytest

from .. import cursors


BOB = {'name': 'bob', 'age': 21, 'DOB': datetime.datetime(1990, 2, 6, 23, 4, 56)}
JIM = {'name': 'jim', 'age': 56, 'DOB': datetime.datetime(1955, 5, 9, 13, 12, 45)}
FRED = {'name': 'fred', 'age': 100, 'DOB': datetime.datetime(1911, 9, 12, 1, 1, 1)}

CURSOR_TYPES = [cursors.DictCursor, cursors.SSDictCursor]


def _ensure_cursor_expired(cursor):
    if isinstance(cursor, cursors.SSCursor):
        list(cursor.fetchall_unbuffered())


@pytest.fixture
def dictcursor_conn(connect):
    """A connection to a database holding a populated `dictcursor` table."""

    conn = connect()
    c = conn.cursor()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        c.execute('drop table if exists dictcursor')
        c.execute('CREATE TABLE dictcursor (name char(20), age int , DOB datetime)')
    data = [
        ('bob', 21, '1990-02-06 23:04:56'),
        ('jim', 56, '1955-05-09 13:12:45'),
        ('fred', 100, '1911-09-12 01:01:01'),
    ]
    c.executemany('insert into dictcursor values (%s,%s,%s)', data)

    yield conn

    c = conn.cursor()
    c.execute('drop table dictcursor')


@pytest.mark.parametrize('cursor_type', CURSOR_TYPES)
def test_DictCursor(dictcursor_conn, cursor_type):
    bob, jim, fred = BOB.copy(), JIM.copy(), FRED.copy()
    # all assertions compare to the structure as would come out from MySQLdb
    conn = dictcursor_conn
    c = conn.cursor(cursor_type)

    # try an update which should return no rows
    c.execute("update dictcursor set age=20 where name='bob'")
    bob['age'] = 20
    # pull back the single row dict for bob and check
    c.execute("SELECT * from dictcursor where name='bob'")
    r = c.fetchone()
    assert r == bob, 'fetchone via DictCursor failed'
    _ensure_cursor_expired(c)

    # same again, but via fetchall
    c.execute("SELECT * from dictcursor where name='bob'")
    r = c.fetchall()
    assert r == [bob], 'fetch a 1 row result via fetchall failed via DictCursor'
    # same test again but iterate over the cursor
    c.execute("SELECT * from dictcursor where name='bob'")
    for r in c:
        assert r == bob, 'fetch a 1 row result via iteration failed via DictCursor'
    # get all 3 rows via fetchall
    c.execute('SELECT * from dictcursor')
    r = c.fetchall()
    assert r == [bob, jim, fred], 'fetchall failed via DictCursor'
    # same test again but do a list comprehension
    c.execute('SELECT * from dictcursor')
    r = list(c)
    assert r == [bob, jim, fred], 'DictCursor should be iterable'
    # get all 2 rows via fetchmany
    c.execute('SELECT * from dictcursor')
    r = c.fetchmany(2)
    assert r == [bob, jim], 'fetchmany failed via DictCursor'
    _ensure_cursor_expired(c)


@pytest.mark.parametrize('cursor_type', CURSOR_TYPES)
def test_custom_dict(dictcursor_conn, cursor_type):
    class MyDict(dict):
        pass

    class MyDictCursor(cursor_type):
        dict_type = MyDict

    keys = ['name', 'age', 'DOB']
    bob = MyDict([(k, BOB[k]) for k in keys])
    jim = MyDict([(k, JIM[k]) for k in keys])
    fred = MyDict([(k, FRED[k]) for k in keys])

    cur = dictcursor_conn.cursor(MyDictCursor)
    cur.execute("SELECT * FROM dictcursor WHERE name='bob'")
    r = cur.fetchone()
    assert r == bob, 'fetchone() returns MyDictCursor'
    _ensure_cursor_expired(cur)

    cur.execute('SELECT * FROM dictcursor')
    r = cur.fetchall()
    assert r == [bob, jim, fred], 'fetchall failed via MyDictCursor'

    cur.execute('SELECT * FROM dictcursor')
    r = list(cur)
    assert r == [bob, jim, fred], 'list failed via MyDictCursor'

    cur.execute('SELECT * FROM dictcursor')
    r = cur.fetchmany(2)
    assert r == [bob, jim], 'fetchmany failed via MyDictCursor'
    _ensure_cursor_expired(cur)
