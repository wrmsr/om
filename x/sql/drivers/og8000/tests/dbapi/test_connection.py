import datetime
import socket

import pytest

from omcore import check

from ...dbapi import DatabaseError
from ...dbapi import InterfaceError
from ...dbapi import connect


def test_unix_socket_missing():
    conn_params = {
        'unix_sock': '/file-does-not-exist',
        'user': "doesn't-matter",
    }

    with pytest.raises(InterfaceError):
        with connect(**conn_params):  # type: ignore
            pass


def test_internet_socket_connection_refused():
    conn_params = {
        'port': 0,
        'user': "doesn't-matter",
    }

    with pytest.raises(
        InterfaceError,
        match=(
                r"Can't create a connection to host localhost and port 0 "
                r"\(timeout is None and source_address is None\)."
        ),
    ):
        with connect(**conn_params):  # type: ignore
            pass


def test_connection_plain_socket(db_kwargs):
    host = db_kwargs.get('host', 'localhost')
    port = db_kwargs.get('port', 5432)
    with socket.create_connection((host, port)) as sock:
        conn_params = {
            'sock': sock,
            'user': db_kwargs['user'],
            'password': db_kwargs['password'],
            'ssl_context': False,
        }

        with connect(**conn_params) as con:
            cur = con.cursor()

            cur.execute('SELECT 1')
            res = cur.fetchall()
            assert res[0][0] == 1


def test_database_missing(db_kwargs):
    db_kwargs['database'] = 'missing-db'
    with pytest.raises(DatabaseError):
        with connect(**db_kwargs):
            pass


def test_database_name_unicode(db_kwargs):
    db_kwargs['database'] = 'test_og8000_sn\uff6fw'

    # Should only raise an exception saying db doesn't exist
    with pytest.raises(DatabaseError, match='3D000'):
        with connect(**db_kwargs):
            pass


def test_database_name_bytes(db_kwargs):
    """Should only raise an exception saying db doesn't exist"""

    db_kwargs['database'] = bytes('test_og8000_sn\uff6fw', 'utf8')
    with pytest.raises(DatabaseError, match='3D000'):
        with connect(**db_kwargs):
            pass


def test_password_bytes(con, db_kwargs):
    # Create user
    username = 'test_og8000_boltzmann'
    password = 'cha\uff6fs'  # noqa
    cur = con.cursor()
    cur.execute('drop role if exists ' + username)
    cur.execute('create user ' + username + " with password '" + password + "';")
    con.commit()

    try:
        db_kwargs['user'] = username
        db_kwargs['password'] = password.encode('utf8')
        db_kwargs['database'] = 'test_og8000_md5'
        with pytest.raises(DatabaseError, match='3D000'):
            with connect(**db_kwargs):
                pass
    finally:
        cur.execute('drop role ' + username)
        con.commit()


def test_application_name(db_kwargs):
    app_name = 'my test application name'
    db_kwargs['application_name'] = app_name
    with connect(**db_kwargs) as db:
        cur = db.cursor()
        cur.execute(
            'select application_name from pg_stat_activity '
            ' where pid = pg_backend_pid()',
        )

        application_name = check.not_none(cur.fetchone())[0]
        assert application_name == app_name


def test_application_name_integer(db_kwargs):
    db_kwargs['application_name'] = 1
    with pytest.raises(
        InterfaceError,
        match=r"The parameter application_name can't be of type <class 'int'>.",
    ):
        with connect(**db_kwargs):
            pass


def test_application_name_bytearray(db_kwargs):
    db_kwargs['application_name'] = bytearray(b'Philby')
    with connect(**db_kwargs):
        pass


def test_notify(con):
    cursor = con.cursor()
    cursor.execute('select pg_backend_pid()')
    backend_pid = cursor.fetchall()[0][0]
    assert list(con.notifications) == []
    cursor.execute('LISTEN test')
    cursor.execute('NOTIFY test')
    con.commit()

    cursor.execute('VALUES (1, 2), (3, 4), (5, 6)')
    assert len(con.notifications) == 1
    notification = con.notifications[0]
    assert (notification.process_id, notification.channel, notification.payload) == (backend_pid, 'test', '')


def test_notify_with_payload(con):
    cursor = con.cursor()
    cursor.execute('select pg_backend_pid()')
    backend_pid = cursor.fetchall()[0][0]
    assert list(con.notifications) == []
    cursor.execute('LISTEN test')
    cursor.execute("NOTIFY test, 'Parnham'")
    con.commit()

    cursor.execute('VALUES (1, 2), (3, 4), (5, 6)')
    assert len(con.notifications) == 1
    notification = con.notifications[0]
    assert (notification.process_id, notification.channel, notification.payload) == (backend_pid, 'test', 'Parnham')


def test_broken_pipe_read(con, db_kwargs):
    db1 = connect(**db_kwargs)
    cur1 = db1.cursor()
    cur2 = con.cursor()
    cur1.execute('select pg_backend_pid()')
    pid1 = check.not_none(cur1.fetchone())[0]

    cur2.execute('select pg_terminate_backend(%s)', (pid1,))
    with pytest.raises(InterfaceError, match='network error'):
        cur1.execute('select 1')

    try:
        db1.close()
    except InterfaceError:
        pass


def test_broken_pipe_flush(con, db_kwargs):
    db1 = connect(**db_kwargs)
    cur1 = db1.cursor()
    cur2 = con.cursor()
    cur1.execute('select pg_backend_pid()')
    pid1 = check.not_none(cur1.fetchone())[0]

    cur2.execute('select pg_terminate_backend(%s)', (pid1,))
    try:
        cur1.execute('select 1')
    except InterfaceError:
        pass

    # Sometimes raises and sometime doesn't
    try:
        db1.close()
    except InterfaceError as e:
        assert str(e) == 'network error'  # noqa


def test_broken_pipe_unpack(con):
    cur = con.cursor()
    cur.execute('select pg_backend_pid()')
    pid1 = cur.fetchone()[0]

    with pytest.raises(InterfaceError, match='network error'):
        cur.execute('select pg_terminate_backend(%s)', (pid1,))


def test_py_value_fail(con):
    # Ensure that if an out adapter throws an exception, the original exception is raised (OG8000TestError), and the
    # connection is still usable after the error.

    class OG8000TestError(Exception):
        pass

    def raise_exception(val):
        raise OG8000TestError('oh noes!')

    con.register_out_adapter(datetime.time, raise_exception)

    c = con.cursor()
    with pytest.raises(OG8000TestError):
        c.execute('SELECT CAST(%s AS TIME) AS f1', (datetime.time(10, 30),))

    # ensure that the connection is still usable for a new query
    c.execute("VALUES ('hw3'::text)")
    assert c.fetchone()[0] == 'hw3'


def test_no_data_error_recovery(con):
    for _ in range(1, 4):
        with pytest.raises(DatabaseError) as e:  # noqa
            c = con.cursor()
            c.execute('DROP TABLE t1')
        assert e.value.args[0]['C'] == '42P01'
        con.rollback()


def test_closed_connection(db_kwargs):
    my_db = connect(**db_kwargs)
    cursor = my_db.cursor()
    my_db.close()
    with pytest.raises(my_db.InterfaceError, match='connection is closed'):
        cursor.execute("VALUES ('hw1'::text)")


@pytest.mark.parametrize(
    'commit',
    [
        'commit',
        'COMMIT;',
    ],
)
def test_failed_transaction_commit_sql(cursor, commit):
    cursor.execute('create temporary table tt (f1 int primary key)')
    cursor.execute('begin')
    try:
        cursor.execute('insert into tt(f1) values(null)')
    except DatabaseError:
        pass

    with pytest.raises(InterfaceError):
        cursor.execute(commit)


def test_failed_transaction_commit_method(con, cursor):
    cursor.execute('create temporary table tt (f1 int primary key)')
    cursor.execute('begin')
    try:
        cursor.execute('insert into tt(f1) values(null)')
    except DatabaseError:
        pass

    with pytest.raises(InterfaceError):
        con.commit()


@pytest.mark.parametrize(
    'rollback',
    [
        'rollback',
        'rollback;',
        'ROLLBACK ;',
    ],
)
def test_failed_transaction_rollback_sql(cursor, rollback):
    cursor.execute('create temporary table tt (f1 int primary key)')
    cursor.execute('begin')
    try:
        cursor.execute('insert into tt(f1) values(null)')
    except DatabaseError:
        pass

    cursor.execute(rollback)


def test_failed_transaction_rollback_method(cursor, con):
    cursor.execute('create temporary table tt (f1 int primary key)')
    cursor.execute('begin')
    try:
        cursor.execute('insert into tt(f1) values(null)')
    except DatabaseError:
        pass

    con.rollback()


@pytest.mark.parametrize(
    'sql',
    [
        'BEGIN',
        'select * from tt;',
    ],
)
def test_failed_transaction_sql(cursor, sql):
    cursor.execute('create temporary table tt (f1 int primary key)')
    cursor.execute('begin')
    try:
        cursor.execute('insert into tt(f1) values(null)')
    except DatabaseError:
        pass

    with pytest.raises(DatabaseError):
        cursor.execute(sql)
