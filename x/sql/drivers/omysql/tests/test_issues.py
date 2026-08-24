import datetime
import textwrap
import time
import warnings

import pytest

from ... import omysql


##
# Old issues


def test_issue_3(connect):
    """Undefined methods datetime_or_None, date_or_None."""

    conn = connect()
    c = conn.cursor()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        c.execute('drop table if exists issue3')
    c.execute('create table issue3 (d date, t time, dt datetime, ts timestamp)')
    try:
        c.execute(
            'insert into issue3 (d, t, dt, ts) values (%s,%s,%s,%s)',
            (None, None, None, None),
        )
        c.execute('select d from issue3')
        assert c.fetchone()[0] is None
        c.execute('select t from issue3')
        assert c.fetchone()[0] is None
        c.execute('select dt from issue3')
        assert c.fetchone()[0] is None
        c.execute('select ts from issue3')
        assert type(c.fetchone()[0]) in (type(None), datetime.datetime), (
            'expected Python type None or datetime from SQL timestamp'
        )
    finally:
        c.execute('drop table issue3')


def test_issue_4(connect):
    """Can't retrieve TIMESTAMP fields."""

    conn = connect()
    c = conn.cursor()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        c.execute('drop table if exists issue4')
    c.execute('create table issue4 (ts timestamp)')
    try:
        c.execute('insert into issue4 (ts) values (now())')
        c.execute('select ts from issue4')
        assert isinstance(c.fetchone()[0], datetime.datetime)
    finally:
        c.execute('drop table issue4')


def test_issue_5(connect):
    """Query on information_schema.tables fails."""

    con = connect()
    cur = con.cursor()
    cur.execute('select * from information_schema.tables')


def test_issue_6(databases):
    """Exception: TypeError: ord() expected a character, but string of length 0 found."""

    # ToDo: this test requires access to db 'mysql'.
    kwargs = databases[0]
    kwargs['database'] = 'mysql'
    conn = omysql.connect(**kwargs)
    c = conn.cursor()
    c.execute('select * from user')
    conn.close()


def test_issue_8(connect):
    """Primary Key and Index error when selecting data."""

    conn = connect()
    c = conn.cursor()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        c.execute('drop table if exists test')
    c.execute(
        """CREATE TABLE `test` (`station` int NOT NULL DEFAULT '0', `dh`
datetime NOT NULL DEFAULT '2015-01-01 00:00:00', `echeance` int NOT NULL
DEFAULT '0', `me` double DEFAULT NULL, `mo` double DEFAULT NULL, PRIMARY
KEY (`station`,`dh`,`echeance`)) ENGINE=MyISAM DEFAULT CHARSET=latin1;""",
    )
    try:
        assert c.execute('SELECT * FROM test') == 0
        c.execute('ALTER TABLE `test` ADD INDEX `idx_station` (`station`)')
        assert c.execute('SELECT * FROM test') == 0
    finally:
        c.execute('drop table test')


def test_issue_13(connect):
    """Can't handle large result fields."""

    conn = connect()
    cur = conn.cursor()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        cur.execute('drop table if exists issue13')
    try:
        cur.execute('create table issue13 (t text)')
        # ticket says 18k
        size = 18 * 1024
        cur.execute('insert into issue13 (t) values (%s)', ('x' * size,))
        cur.execute('select t from issue13')
        # use a bare comparison so that obscenely huge error messages don't print
        r = cur.fetchone()[0]
        assert 'x' * size == r
    finally:
        cur.execute('drop table issue13')


def test_issue_15(connect):
    """Query should be expanded before perform character encoding."""

    conn = connect()
    c = conn.cursor()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        c.execute('drop table if exists issue15')
    c.execute('create table issue15 (t varchar(32))')
    try:
        c.execute('insert into issue15 (t) values (%s)', ('\xe4\xf6\xfc',))
        c.execute('select t from issue15')
        assert c.fetchone()[0] == '\xe4\xf6\xfc'
    finally:
        c.execute('drop table issue15')


def test_issue_16(connect):
    """Patch for string and tuple escaping."""

    conn = connect()
    c = conn.cursor()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        c.execute('drop table if exists issue16')
    c.execute('create table issue16 (name varchar(32) primary key, email varchar(32))')
    try:
        c.execute("insert into issue16 (name, email) values ('pete', 'floydophone')")
        c.execute('select email from issue16 where name=%s', ('pete',))
        assert c.fetchone()[0] == 'floydophone'
    finally:
        c.execute('drop table issue16')


@pytest.mark.skip('test_issue_17() requires a custom, legacy MySQL configuration and will not be run.')
def test_issue_17(connect, databases):
    """Could not connect mysql use password."""

    conn = connect()
    host = databases[0]['host']
    db = databases[0]['database']
    c = conn.cursor()

    # grant access to a table to a user with a password
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            c.execute('drop table if exists issue17')
        c.execute('create table issue17 (x varchar(32) primary key)')
        c.execute("insert into issue17 (x) values ('hello, world!')")
        c.execute(f"grant all privileges on {db}.issue17 to 'issue17user'@'%%' identified by '1234'")
        conn.commit()

        conn2 = omysql.connect(host=host, user='issue17user', passwd='1234', db=db)
        c2 = conn2.cursor()
        c2.execute('select x from issue17')
        assert c2.fetchone()[0] == 'hello, world!'
    finally:
        c.execute('drop table issue17')


##
# New issues


def test_issue_34():
    with pytest.raises(omysql.OperationalError) as cm:
        omysql.connect(host='localhost', port=1237, user='root')
    assert cm.value.args[0] == 2003


def test_issue_33(safe_create_table, databases):
    conn = omysql.connect(charset='utf8', **databases[0])
    safe_create_table(conn, 'hei\xdfe', 'create table hei\xdfe (name varchar(32))')
    c = conn.cursor()
    c.execute("insert into hei\xdfe (name) values ('Pi\xdfata')")
    c.execute('select name from hei\xdfe')
    assert c.fetchone()[0] == 'Pi\xdfata'


@pytest.mark.skip('This test requires manual intervention')
def test_issue_35(connect):
    conn = connect()
    c = conn.cursor()
    print('sudo killall -9 mysqld within the next 10 seconds')
    with pytest.raises(omysql.OperationalError) as cm:
        c.execute('select sleep(10)')
    assert cm.value.args[0] == 2013


def test_issue_36(connections):
    # connection 0 is super user, connection 1 isn't
    conn = connections[1]
    c = conn.cursor()
    c.execute('show processlist')
    kill_id = None
    for row in c.fetchall():
        id_ = row[0]
        info = row[7]
        if info == 'show processlist':
            kill_id = id_
            break
    assert kill_id == conn.thread_id()
    # now nuke the connection
    connections[0].kill(kill_id)
    # make sure this connection has broken
    with pytest.raises(omysql.Error):
        c.execute('show tables')
    c.close()
    conn.close()

    # check the process list from the other connection
    # Wait since CI sometimes fails this test otherwise.
    time.sleep(0.1)

    c = connections[0].cursor()
    c.execute('show processlist')
    ids = [row[0] for row in c.fetchall()]
    assert kill_id not in ids


def test_issue_37(connect):
    conn = connect()
    c = conn.cursor()
    assert c.execute('SELECT @foo') == 1
    assert c.fetchone() == (None,)
    assert c.execute("SET @foo = 'bar'") == 0
    c.execute("set @foo = 'bar'")


def test_issue_38(connect):
    conn = connect()
    c = conn.cursor()
    datum = 'a' * 1024 * 1023  # reduced size for most default mysql installs

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            c.execute('drop table if exists issue38')
        c.execute('create table issue38 (id integer, data mediumblob)')
        c.execute('insert into issue38 values (1, %s)', (datum,))
    finally:
        c.execute('drop table issue38')


def disabled_test_issue_54(connect):
    conn = connect()
    c = conn.cursor()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        c.execute('drop table if exists issue54')
    big_sql = 'select * from issue54 where '
    big_sql += ' and '.join(f'{i}={i}' for i in range(100000))

    try:
        c.execute('create table issue54 (id integer primary key)')
        c.execute('insert into issue54 (id) values (7)')
        c.execute(big_sql)
        assert c.fetchone()[0] == 7
    finally:
        c.execute('drop table issue54')


##
# GitHub issues


def test_issue_66(connect):
    """'Connection' object has no attribute 'insert_id'."""

    conn = connect()
    c = conn.cursor()
    assert conn.insert_id() == 0
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            c.execute('drop table if exists issue66')
        c.execute('create table issue66 (id integer primary key auto_increment, x integer)')
        c.execute('insert into issue66 (x) values (1)')
        c.execute('insert into issue66 (x) values (1)')
        assert conn.insert_id() == 2
    finally:
        c.execute('drop table issue66')


def test_issue_79(connect):
    """Duplicate field overwrites the previous one in the result of DictCursor."""

    conn = connect()
    c = conn.cursor(omysql.cursors.DictCursor)

    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        c.execute('drop table if exists a')
        c.execute('drop table if exists b')
    c.execute("""CREATE TABLE a (id int, value int)""")
    c.execute("""CREATE TABLE b (id int, value int)""")

    a = (1, 11)
    b = (1, 22)
    try:
        c.execute('insert into a values (%s, %s)', a)
        c.execute('insert into b values (%s, %s)', b)

        c.execute('SELECT * FROM a inner join b on a.id = b.id')
        r = c.fetchall()[0]
        assert r['id'] == 1
        assert r['value'] == 11
        assert r['b.value'] == 22
    finally:
        c.execute('drop table a')
        c.execute('drop table b')


def test_issue_95(connect):
    """Leftover trailing OK packet for "CALL my_sp" queries."""

    conn = connect()
    cur = conn.cursor()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        cur.execute('DROP PROCEDURE IF EXISTS `foo`')
    cur.execute(
        """CREATE PROCEDURE `foo` ()
    BEGIN
        SELECT 1;
    END""",
    )
    try:
        cur.execute("""CALL foo()""")
        cur.execute("""SELECT 1""")
        assert cur.fetchone()[0] == 1
    finally:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            cur.execute('DROP PROCEDURE IF EXISTS `foo`')


def test_issue_114(databases):
    """autocommit is not set after reconnecting with ping()."""

    conn = omysql.connect(charset='utf8', **databases[0])
    conn.autocommit(False)
    c = conn.cursor()
    c.execute("""select @@autocommit;""")
    assert not c.fetchone()[0]
    conn.close()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        conn.ping(reconnect=True)
    c.execute("""select @@autocommit;""")
    assert not c.fetchone()[0]
    conn.close()

    # Ensure autocommit() is still working
    conn = omysql.connect(charset='utf8', **databases[0])
    c = conn.cursor()
    c.execute("""select @@autocommit;""")
    assert not c.fetchone()[0]
    conn.close()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        conn.ping(reconnect=True)
    conn.autocommit(True)
    c.execute("""select @@autocommit;""")
    assert c.fetchone()[0]
    conn.close()


def test_issue_175(connect):
    """The number of fields returned by server is read in wrong way."""

    conn = connect()
    cur = conn.cursor()
    for length in (200, 300):
        columns = ', '.join(f'c{i} integer' for i in range(length))
        sql = f'create table test_field_count ({columns})'
        try:
            cur.execute(sql)
            cur.execute('select * from test_field_count')
            assert len(cur.description) == length
        finally:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore')
                cur.execute('drop table if exists test_field_count')


def test_issue_321(safe_create_table, databases):
    """Test iterable as query argument."""

    conn = omysql.connect(charset='utf8', **databases[0])
    safe_create_table(
        conn,
        'issue321',
        'create table issue321 (value_1 varchar(1), value_2 varchar(1))',
    )

    sql_insert = 'insert into issue321 (value_1, value_2) values (%s, %s)'
    sql_dict_insert = 'insert into issue321 (value_1, value_2) values (%(value_1)s, %(value_2)s)'
    sql_select = 'select * from issue321 where value_1 in %s and value_2=%s'
    data = [
        [('a',), '\u0430'],
        [['b'], '\u0430'],
        {'value_1': [['c']], 'value_2': '\u0430'},
    ]
    cur = conn.cursor()
    assert cur.execute(sql_insert, data[0]) == 1
    assert cur.execute(sql_insert, data[1]) == 1
    assert cur.execute(sql_dict_insert, data[2]) == 1
    assert cur.execute(sql_select, [('a', 'b', 'c'), '\u0430']) == 3
    assert cur.fetchone() == ('a', '\u0430')
    assert cur.fetchone() == ('b', '\u0430')
    assert cur.fetchone() == ('c', '\u0430')


def test_issue_364(safe_create_table, databases):
    """Test mixed unicode/binary arguments in executemany."""

    conn = omysql.connect(charset='utf8mb4', **databases[0])
    safe_create_table(
        conn,
        'issue364',
        'create table issue364 (value_1 binary(3), value_2 varchar(3)) '
        'engine=InnoDB default charset=utf8mb4',
    )

    sql = 'insert into issue364 (value_1, value_2) values (_binary %s, %s)'
    usql = 'insert into issue364 (value_1, value_2) values (_binary %s, %s)'
    values = [omysql.Binary(b'\x00\xff\x00'), '\xe4\xf6\xfc']

    # test single insert and select
    cur = conn.cursor()
    cur.execute(sql, args=values)
    cur.execute('select * from issue364')
    assert cur.fetchone() == tuple(values)

    # test single insert unicode query
    cur.execute(usql, args=values)

    # test multi insert and select
    cur.executemany(sql, args=(values, values, values))
    cur.execute('select * from issue364')
    for row in cur.fetchall():
        assert row == tuple(values)

    # test multi insert with unicode query
    cur.executemany(usql, args=(values, values, values))


def test_issue_363(safe_create_table, databases):
    """Test binary / geometry types."""

    conn = omysql.connect(charset='utf8', **databases[0])
    safe_create_table(
        conn,
        'issue363',
        'CREATE TABLE issue363 ( '
        'id INTEGER PRIMARY KEY, geom LINESTRING NOT NULL /*!80003 SRID 0 */, '
        'SPATIAL KEY geom (geom)) '
        'ENGINE=MyISAM',
    )

    cur = conn.cursor()
    query = (
        "INSERT INTO issue363 (id, geom) VALUES"
        "(1998, ST_GeomFromText('LINESTRING(1.1 1.1,2.2 2.2)'))"
    )
    cur.execute(query)

    # select WKT
    query = 'SELECT ST_AsText(geom) FROM issue363'
    cur.execute(query)
    row = cur.fetchone()
    assert row == ('LINESTRING(1.1 1.1,2.2 2.2)',)

    # select WKB
    query = 'SELECT ST_AsBinary(geom) FROM issue363'
    cur.execute(query)
    row = cur.fetchone()
    assert row == (
        b'\x01\x02\x00\x00\x00\x02\x00\x00\x00'
        b'\x9a\x99\x99\x99\x99\x99\xf1?'
        b'\x9a\x99\x99\x99\x99\x99\xf1?'
        b'\x9a\x99\x99\x99\x99\x99\x01@'
        b'\x9a\x99\x99\x99\x99\x99\x01@',
    )

    # select internal binary
    cur.execute('SELECT geom FROM issue363')
    row = cur.fetchone()
    # don't assert the exact internal binary value, as it could vary across implementations
    assert isinstance(row[0], bytes)


def test_issue_1206(databases):
    conn = omysql.connect(charset='utf8', **databases[0])

    cur = conn.cursor()
    cur.execute('DROP PROCEDURE IF EXISTS `foo.bar`')
    try:
        cur.execute(
            textwrap.dedent("""\
            create procedure `foo.bar` (arg1 int)
            begin
                select arg1*2;
            end
        """),
        )

        cur.callproc('foo.bar', args=(123,))
        assert cur.fetchone()[0] == 246
    finally:
        cur.execute('DROP PROCEDURE IF EXISTS `foo.bar`')
        conn.close()
