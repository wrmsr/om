import pytest

from ... import omysql
from .. import cursors
from ..constants import ER
from .utils import get_mysql_vendor


def test_re_insert_values_with_on_duplicate_key_alias():
    m = cursors.RE_INSERT_VALUES.match(
        'INSERT INTO t1 (a,b,c) VALUES (%s,%s,%s) AS new '
        'ON DUPLICATE KEY UPDATE c = new.a + new.b',
    )
    assert m is not None
    assert m.group(1) == 'INSERT INTO t1 (a,b,c) VALUES '
    assert m.group(2) == '(%s,%s,%s)'
    assert m.group(3) == ' AS new ON DUPLICATE KEY UPDATE c = new.a + new.b'

    m = cursors.RE_INSERT_VALUES.match(
        'INSERT INTO t1 (a,b,c) VALUES (%s,%s,%s) AS new(n1,n2,n3) '
        'ON DUPLICATE KEY UPDATE c = n1 + n2',
    )
    assert m is not None
    assert m.group(3) == ' AS new(n1,n2,n3) ON DUPLICATE KEY UPDATE c = n1 + n2'

    m = cursors.RE_INSERT_VALUES.match(
        'INSERT INTO t1 (a,b,c) VALUES (%s,%s,%s) '
        'ON DUPLICATE KEY UPDATE c=VALUES(a)+VALUES(b)',
    )
    assert m is not None
    assert m.group(3) == ' ON DUPLICATE KEY UPDATE c=VALUES(a)+VALUES(b)'


@pytest.fixture
def test_table_conn(connect, safe_create_table, databases):
    """A dedicated connection to a database holding a populated 5-row `test` table."""

    conn = connect()
    safe_create_table(
        conn,
        'test',
        'create table test (data varchar(10))',
    )
    cursor = conn.cursor()
    cursor.execute(
        "insert into test (data) values ('row1'), ('row2'), ('row3'), ('row4'), ('row5')",
    )
    conn.commit()
    cursor.close()

    test_connection = omysql.connect(**databases[0])
    yield test_connection
    test_connection.close()


def test_cursor_is_iterator(test_table_conn):
    """Test that the cursor is an iterator."""

    cursor = test_table_conn.cursor()
    cursor.execute('select * from test')
    assert cursor.__iter__() == cursor
    assert cursor.__next__() == ('row1',)


def test_cleanup_rows_unbuffered(test_table_conn):
    conn = test_table_conn
    cursor = conn.cursor(cursors.SSCursor)

    cursor.execute('select * from test as t1, test as t2')
    for counter, _row in enumerate(cursor):
        if counter > 10:
            break

    del cursor

    c2 = conn.cursor()

    c2.execute('select 1')
    assert c2.fetchone() == (1,)
    assert c2.fetchone() is None


def test_cleanup_rows_buffered(test_table_conn):
    conn = test_table_conn
    cursor = conn.cursor(cursors.Cursor)

    cursor.execute('select * from test as t1, test as t2')
    for counter, _row in enumerate(cursor):
        if counter > 10:
            break

    del cursor

    c2 = conn.cursor()
    c2.execute('select 1')

    assert c2.fetchone() == (1,)
    assert c2.fetchone() is None


def test_executemany(test_table_conn):
    conn = test_table_conn
    cursor = conn.cursor(cursors.Cursor)

    m = cursors.RE_INSERT_VALUES.match('INSERT INTO TEST (ID, NAME) VALUES (%s, %s)')
    assert m is not None, 'error parse %s'
    assert m.group(3) == '', 'group 3 not blank, bug in RE_INSERT_VALUES?'

    m = cursors.RE_INSERT_VALUES.match('INSERT INTO TEST (ID, NAME) VALUES (%(id)s, %(name)s)')
    assert m is not None, 'error parse %(name)s'
    assert m.group(3) == '', 'group 3 not blank, bug in RE_INSERT_VALUES?'

    m = cursors.RE_INSERT_VALUES.match('INSERT INTO TEST (ID, NAME) VALUES (%(id_name)s, %(name)s)')
    assert m is not None, 'error parse %(id_name)s'
    assert m.group(3) == '', 'group 3 not blank, bug in RE_INSERT_VALUES?'

    m = cursors.RE_INSERT_VALUES.match(
        'INSERT INTO TEST (ID, NAME) VALUES (%(id_name)s, %(name)s) ON duplicate update',
    )
    assert m is not None, 'error parse %(id_name)s'
    assert m.group(3) == ' ON duplicate update', 'group 3 not ON duplicate update, bug in RE_INSERT_VALUES?'

    # https://github.com/PyMySQL/PyMySQL/pull/597
    m = cursors.RE_INSERT_VALUES.match('INSERT INTO bloup(foo, bar)VALUES(%s, %s)')
    assert m is not None

    # cursor._executed must be "insert into test (data) values (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)"
    # list args
    data = range(10)
    cursor.executemany('insert into test (data) values (%s)', data)
    assert cursor._executed.endswith(b',(7),(8),(9)'), 'execute many with %s not in one query'  # noqa: SLF001

    # dict args
    data_dict = [{'data': i} for i in range(10)]
    cursor.executemany('insert into test (data) values (%(data)s)', data_dict)
    assert cursor._executed.endswith(b',(7),(8),(9)'), 'execute many with %(data)s not in one query'  # noqa: SLF001

    # %% in column set
    cursor.execute(
        """\
        CREATE TABLE percent_test (
            `A%` INTEGER,
            `B%` INTEGER)""",
    )
    try:
        q = 'INSERT INTO percent_test (`A%%`, `B%%`) VALUES (%s, %s)'
        assert cursors.RE_INSERT_VALUES.match(q) is not None
        cursor.executemany(q, [(3, 4), (5, 6)])
        assert cursor._executed.endswith(b'(3, 4),(5, 6)'), 'executemany with %% not in one query'  # noqa: SLF001
    finally:
        cursor.execute('DROP TABLE IF EXISTS percent_test')


def test_execution_time_limit(test_table_conn):
    # This test is similarly implemented in test_SSCursor.

    conn = test_table_conn
    db_type = get_mysql_vendor(conn)

    with conn.cursor(cursors.Cursor) as cur:
        # MySQL MAX_EXECUTION_TIME takes ms
        # MariaDB max_statement_time takes seconds as int/float, introduced in 10.1

        # this will sleep 0.01 seconds per row
        if db_type == 'mysql':
            sql = 'SELECT /*+ MAX_EXECUTION_TIME(2000) */ data, sleep(0.01) FROM test'
        else:
            sql = 'SET STATEMENT max_statement_time=2 FOR SELECT data, sleep(0.01) FROM test'

        cur.execute(sql)
        # unlike SSCursor, Cursor returns a tuple of tuples here
        assert cur.fetchall() == (
            ('row1', 0),
            ('row2', 0),
            ('row3', 0),
            ('row4', 0),
            ('row5', 0),
        )

        if db_type == 'mysql':
            sql = 'SELECT /*+ MAX_EXECUTION_TIME(2000) */ data, sleep(0.01) FROM test'
        else:
            sql = 'SET STATEMENT max_statement_time=2 FOR SELECT data, sleep(0.01) FROM test'
        cur.execute(sql)
        assert cur.fetchone() == ('row1', 0)

        # this discards the previous unfinished query
        cur.execute('SELECT 1')
        assert cur.fetchone() == (1,)

        if db_type == 'mysql':
            sql = 'SELECT /*+ MAX_EXECUTION_TIME(1) */ data, sleep(1) FROM test'
        else:
            sql = 'SET STATEMENT max_statement_time=0.001 FOR SELECT data, sleep(1) FROM test'
        with pytest.raises(omysql.errors.OperationalError) as cm:
            # in a buffered cursor this should reliably raise an OperationalError
            cur.execute(sql)

        if db_type == 'mysql':
            # this constant was only introduced in MySQL 5.7, not sure
            # what was returned before, may have been ER_QUERY_INTERRUPTED
            assert cm.value.args[0] == ER.QUERY_TIMEOUT
        else:
            assert cm.value.args[0] == ER.STATEMENT_TIMEOUT

        # connection should still be fine at this point
        cur.execute('SELECT 1')
        assert cur.fetchone() == (1,)


def test_warnings(connect):
    con = connect()
    cur = con.cursor()
    cur.execute('DROP TABLE IF EXISTS `no_exists_table`')
    assert cur.warning_count == 1

    cur.execute('SHOW WARNINGS')
    w = cur.fetchone()
    assert w[1] == ER.BAD_TABLE_ERROR
    assert 'no_exists_table' in w[2]

    cur.execute('SELECT 1')
    assert cur.warning_count == 0
