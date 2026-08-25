# ruff: noqa: DTZ001
import datetime
import json
import time

import pytest

from .utils import get_mysql_vendor
from .utils import mysql_server_is


##
# Conversion


def test_datatypes(connect):
    """Test every data type."""

    conn = connect()
    c = conn.cursor()
    c.execute(
        """
create table test_datatypes (
    b bit,
    i int,
    l bigint,
    f real,
    s varchar(32),
    u varchar(32),
    bb blob,
    d date,
    dt datetime,
    ts timestamp,
    td time,
    t time,
    st datetime)
""",
    )
    try:
        # insert values

        v = (
            True,
            -3,
            123456789012,
            5.7,
            "hello'\" world",
            'Espa\xc3\xb1ol',
            'binary\x00data'.encode(conn.encoding),
            datetime.date(1988, 2, 2),
            datetime.datetime(2014, 5, 15, 7, 45, 57),
            datetime.timedelta(5, 6),
            datetime.time(16, 32),
            time.localtime(),
        )
        c.execute(
            'insert into test_datatypes (b,i,l,f,s,u,bb,d,dt,td,t,st) values'
            ' (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            v,
        )
        c.execute('select b,i,l,f,s,u,bb,d,dt,td,t,st from test_datatypes')
        r = c.fetchone()
        assert r[0] == b'\x01'
        assert r[1:10] == v[1:10]
        assert r[10] == datetime.timedelta(0, 60 * (v[10].hour * 60 + v[10].minute))
        assert r[-1] == datetime.datetime(*v[-1][:6])

        c.execute('delete from test_datatypes')

        # check nulls
        c.execute(
            'insert into test_datatypes (b,i,l,f,s,u,bb,d,dt,td,t,st)'
            ' values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            [None] * 12,
        )
        c.execute('select b,i,l,f,s,u,bb,d,dt,td,t,st from test_datatypes')
        r = c.fetchone()
        assert r == tuple([None] * 12)

        c.execute('delete from test_datatypes')

        # check sequences type
        for seq_type in (tuple, list, set, frozenset):
            c.execute('insert into test_datatypes (i, l) values (2,4), (6,8), (10,12)')
            seq = seq_type([2, 6])
            c.execute('select l from test_datatypes where i in %s order by i', (seq,))
            r = c.fetchall()
            assert r == ((4,), (8,))
            c.execute('delete from test_datatypes')

    finally:
        c.execute('drop table test_datatypes')


def test_dict(connect):
    """Test dict escaping."""

    conn = connect()
    c = conn.cursor()
    c.execute('create table test_dict (a integer, b integer, c integer)')
    try:
        c.execute(
            'insert into test_dict (a,b,c) values (%(a)s, %(b)s, %(c)s)',
            {'a': 1, 'b': 2, 'c': 3},
        )
        c.execute('select a,b,c from test_dict')
        assert c.fetchone() == (1, 2, 3)
    finally:
        c.execute('drop table test_dict')


def test_string(connect):
    conn = connect()
    c = conn.cursor()
    c.execute('create table test_dict (a text)')
    test_value = 'I am a test string'
    try:
        c.execute('insert into test_dict (a) values (%s)', test_value)
        c.execute('select a from test_dict')
        assert c.fetchone() == (test_value,)
    finally:
        c.execute('drop table test_dict')


def test_integer(connect):
    conn = connect()
    c = conn.cursor()
    c.execute('create table test_dict (a integer)')
    test_value = 12345
    try:
        c.execute('insert into test_dict (a) values (%s)', test_value)
        c.execute('select a from test_dict')
        assert c.fetchone() == (test_value,)
    finally:
        c.execute('drop table test_dict')


def test_binary(connect, safe_create_table):
    """Test binary data."""

    data = bytes(bytearray(range(255)))
    conn = connect()
    safe_create_table(conn, 'test_binary', 'create table test_binary (b binary(255))')

    with conn.cursor() as c:
        c.execute('insert into test_binary (b) values (_binary %s)', (data,))
        c.execute('select b from test_binary')
        assert c.fetchone()[0] == data


def test_blob(connect, safe_create_table):
    """Test blob data."""

    data = bytes(bytearray(range(256)) * 4)
    conn = connect()
    safe_create_table(conn, 'test_blob', 'create table test_blob (b blob)')

    with conn.cursor() as c:
        c.execute('insert into test_blob (b) values (_binary %s)', (data,))
        c.execute('select b from test_blob')
        assert c.fetchone()[0] == data


def test_untyped(connect):
    """Test conversion of null, empty string."""

    conn = connect()
    c = conn.cursor()
    c.execute("select null,''")
    assert c.fetchone() == (None, '')
    c.execute("select '',null")
    assert c.fetchone() == ('', None)


def test_timedelta(connect):
    """Test timedelta conversion."""

    conn = connect()
    c = conn.cursor()
    c.execute(
        "select time('12:30'), time('23:12:59'), time('23:12:59.05100'),"
        " time('-12:30'), time('-23:12:59'), time('-23:12:59.05100'), time('-00:30')",
    )
    assert c.fetchone() == (
        datetime.timedelta(0, 45000),
        datetime.timedelta(0, 83579),
        datetime.timedelta(0, 83579, 51000),
        -datetime.timedelta(0, 45000),
        -datetime.timedelta(0, 83579),
        -datetime.timedelta(0, 83579, 51000),
        -datetime.timedelta(0, 1800),
    )


def test_datetime_microseconds(connect):
    """Test datetime conversion with microseconds."""

    conn = connect()
    c = conn.cursor()
    dt = datetime.datetime(2013, 11, 12, 9, 9, 9, 123450)
    c.execute('create table test_datetime (id int, ts datetime(6))')
    try:
        c.execute('insert into test_datetime values (%s, %s)', (1, dt))
        c.execute('select ts from test_datetime')
        assert c.fetchone() == (dt,)
    finally:
        c.execute('drop table test_datetime')


##
# Cursor


def test_fetch_no_result(connect):
    """Test a fetchone() with no rows."""

    conn = connect()
    c = conn.cursor()
    c.execute('create table test_nr (b varchar(32))')
    try:
        data = 'pymysql'
        c.execute('insert into test_nr (b) values (%s)', (data,))
        assert c.fetchone() is None
    finally:
        c.execute('drop table test_nr')


def test_aggregates(connect):
    """Test aggregate functions."""

    conn = connect()
    c = conn.cursor()
    try:
        c.execute('create table test_aggregates (i integer)')
        for i in range(10):
            c.execute('insert into test_aggregates (i) values (%s)', (i,))
        c.execute('select sum(i) from test_aggregates')
        (r,) = c.fetchone()
        assert r == sum(range(10))
    finally:
        c.execute('drop table test_aggregates')


def test_single_tuple(connect, safe_create_table):
    """Test a single tuple."""

    conn = connect()
    c = conn.cursor()
    safe_create_table(conn, 'mystuff', 'create table mystuff (id integer primary key)')
    c.execute('insert into mystuff (id) values (1)')
    c.execute('insert into mystuff (id) values (2)')
    c.execute('select id from mystuff where id in %s', ((1,),))
    assert list(c.fetchall()) == [(1,)]
    c.close()


def test_json(connect, safe_create_table):
    conn = connect(charset='utf8mb4')
    # MariaDB only has limited JSON support, stores data as longtext
    # https://mariadb.com/kb/en/json-data-type/
    if not mysql_server_is(conn, (5, 7, 0)):
        pytest.skip('JSON type is only supported on MySQL >= 5.7')

    safe_create_table(
        conn,
        'test_json',
        """\
create table test_json (
    id int not null,
    json JSON not null,
    primary key (id)
);""",
    )
    cur = conn.cursor()

    json_str = '{"hello": "こんにちは"}'
    cur.execute('INSERT INTO test_json (id, `json`) values (42, %s)', (json_str,))
    cur.execute('SELECT `json` from `test_json` WHERE `id`=42')
    res = cur.fetchone()[0]
    assert json.loads(res) == json.loads(json_str)

    if get_mysql_vendor(conn) == 'mysql':
        cur.execute('SELECT CAST(%s AS JSON) AS x', (json_str,))
        res = cur.fetchone()[0]
        assert json.loads(res) == json.loads(json_str)


##
# Bulk inserts


BULKINSERT_DDL = """\
CREATE TABLE bulkinsert
(
id int,
name char(20),
age int,
height int,
PRIMARY KEY (id)
)
"""


@pytest.fixture
def bulkinsert_conn(connect, safe_create_table):
    """A connection to a database holding an empty `bulkinsert` table."""

    conn = connect()
    safe_create_table(conn, 'bulkinsert', BULKINSERT_DDL)
    return conn


def _verify_records(connect, data):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, age, height from bulkinsert')
    result = cursor.fetchall()
    assert sorted(result) == sorted(data)


def test_bulk_insert(connect, bulkinsert_conn):
    cursor = bulkinsert_conn.cursor()

    data = [(0, 'bob', 21, 123), (1, 'jim', 56, 45), (2, 'fred', 100, 180)]
    cursor.executemany(
        'insert into bulkinsert (id, name, age, height) values (%s,%s,%s,%s)',
        data,
    )
    assert cursor._executed == bytearray(  # noqa: SLF001
        b"insert into bulkinsert (id, name, age, height) values "
        b"(0,'bob',21,123),(1,'jim',56,45),(2,'fred',100,180)",
    )
    cursor.execute('commit')
    _verify_records(connect, data)


def test_bulk_insert_multiline_statement(connect, bulkinsert_conn):
    cursor = bulkinsert_conn.cursor()
    data = [(0, 'bob', 21, 123), (1, 'jim', 56, 45), (2, 'fred', 100, 180)]
    cursor.executemany(
        """insert
into bulkinsert (id, name,
age, height)
values (%s,
%s , %s,
%s )
 """,
        data,
    )
    assert cursor._executed.strip() == bytearray(  # noqa: SLF001
        b"""insert
into bulkinsert (id, name,
age, height)
values (0,
'bob' , 21,
123 ),(1,
'jim' , 56,
45 ),(2,
'fred' , 100,
180 )""",
    )
    cursor.execute('commit')
    _verify_records(connect, data)


def test_bulk_insert_single_record(connect, bulkinsert_conn):
    cursor = bulkinsert_conn.cursor()
    data = [(0, 'bob', 21, 123)]
    cursor.executemany(
        'insert into bulkinsert (id, name, age, height) values (%s,%s,%s,%s)',
        data,
    )
    cursor.execute('commit')
    _verify_records(connect, data)


def test_bulk_insert_on_duplicate_update(connect, bulkinsert_conn):
    """executemany should work with "insert ... on duplicate key update" (issue 288)."""

    cursor = bulkinsert_conn.cursor()
    data = [(0, 'bob', 21, 123), (1, 'jim', 56, 45), (2, 'fred', 100, 180)]
    cursor.executemany(
        """insert
into bulkinsert (id, name,
age, height)
values (%s,
%s , %s,
%s ) on duplicate key update
age = values(age)
 """,
        data,
    )
    assert cursor._executed.strip() == bytearray(  # noqa: SLF001
        b"""insert
into bulkinsert (id, name,
age, height)
values (0,
'bob' , 21,
123 ),(1,
'jim' , 56,
45 ),(2,
'fred' , 100,
180 ) on duplicate key update
age = values(age)""",
    )
    cursor.execute('commit')
    _verify_records(connect, data)
