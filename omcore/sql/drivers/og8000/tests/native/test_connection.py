import datetime
import socket

import pytest

from ...... import check
from ...errors import DatabaseError
from ...native import Connection
from ...native import InterfaceError


def test_unix_socket_missing():
    conn_params = {
        'unix_sock': '/file-does-not-exist',
        'user': "doesn't-matter",
    }

    with pytest.raises(InterfaceError):
        Connection(**conn_params)


def test_internet_socket_connection_refused():
    conn_params = {
        'port': 0,
        'user': "doesn't-matter",
    }

    with pytest.raises(
        InterfaceError,
        match=r"Can't create a connection to host localhost and port 0 \(timeout is None and source_address is None\).",
    ):
        Connection(**conn_params)


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

        with Connection(**conn_params) as con:
            res = con.run('SELECT 1')
            assert check.not_none(res)[0][0] == 1


def test_database_missing(db_kwargs):
    db_kwargs['database'] = 'missing-db'
    with pytest.raises(DatabaseError):
        Connection(**db_kwargs)


def test_notify(con):
    backend_pid = con.run('select pg_backend_pid()')[0][0]
    assert list(con.notifications) == []
    con.run('LISTEN test')
    con.run('NOTIFY test')

    con.run('VALUES (1, 2), (3, 4), (5, 6)')
    assert len(con.notifications) == 1
    notification = con.notifications[0]
    assert (notification.process_id, notification.channel, notification.payload) == (backend_pid, 'test', '')


def test_notify_with_payload(con):
    backend_pid = con.run('select pg_backend_pid()')[0][0]
    assert list(con.notifications) == []
    con.run('LISTEN test')
    con.run("NOTIFY test, 'Parnham'")

    con.run('VALUES (1, 2), (3, 4), (5, 6)')
    assert len(con.notifications) == 1
    notification = con.notifications[0]
    assert (notification.process_id, notification.channel, notification.payload) == (backend_pid, 'test', 'Parnham')


# This requires a line in pg_hba.conf that requires md5 for the database test_og8000_md5


def test_md5(db_kwargs):
    db_kwargs['database'] = 'test_og8000_md5'

    # Should only raise an exception saying db doesn't exist
    with pytest.raises(DatabaseError, match='3D000'):
        Connection(**db_kwargs)


# This requires a line in pg_hba.conf that requires 'password' for the database test_og8000_password


def test_password(db_kwargs):
    db_kwargs['database'] = 'test_og8000_password'

    # Should only raise an exception saying db doesn't exist
    with pytest.raises(DatabaseError, match='3D000'):
        Connection(**db_kwargs)


def test_unicode_database_name(db_kwargs):
    db_kwargs['database'] = 'test_og8000_sn\uff6fw'

    # Should only raise an exception saying db doesn't exist
    with pytest.raises(DatabaseError, match='3D000'):
        Connection(**db_kwargs)


def test_bytes_database_name(db_kwargs):
    """Should only raise an exception saying db doesn't exist"""

    db_kwargs['database'] = bytes('test_og8000_sn\uff6fw', 'utf8')
    with pytest.raises(DatabaseError, match='3D000'):
        Connection(**db_kwargs)


def test_bytes_password(con, db_kwargs):
    # Create user
    username = 'test_og8000_boltzmann'
    password = 'cha\uff6fs'  # noqa
    con.run('drop role if exists ' + username)
    con.run('create user ' + username + " with password '" + password + "';")

    try:
        db_kwargs['user'] = username
        db_kwargs['password'] = password.encode('utf8')
        db_kwargs['database'] = 'test_og8000_md5'
        with pytest.raises(DatabaseError, match='3D000'):
            Connection(**db_kwargs)
    finally:
        con.run('drop role ' + username)


def test_broken_pipe_read(con, db_kwargs):
    db1 = Connection(**db_kwargs)
    res = db1.run('select pg_backend_pid()')
    pid1 = check.not_none(res)[0][0]

    con.run('select pg_terminate_backend(:v)', v=pid1)
    with pytest.raises(InterfaceError, match='network error'):
        db1.run('select 1')

    try:
        db1.close()
    except InterfaceError:
        pass


def test_broken_pipe_unpack(con):
    res = con.run('select pg_backend_pid()')
    pid1 = res[0][0]

    with pytest.raises(InterfaceError, match='network error'):
        con.run('select pg_terminate_backend(:v)', v=pid1)


def test_broken_pipe_flush(con, db_kwargs):
    db1 = Connection(**db_kwargs)
    res = db1.run('select pg_backend_pid()')
    pid1 = check.not_none(res)[0][0]

    con.run('select pg_terminate_backend(:v)', v=pid1)
    try:
        db1.run('select 1')
    except InterfaceError:
        pass

    # Sometimes raises and sometime doesn't
    try:
        db1.close()
    except InterfaceError as e:
        assert str(e) == 'network error'  # noqa


def test_application_name(db_kwargs):
    app_name = 'my test application name'
    db_kwargs['application_name'] = app_name
    with Connection(**db_kwargs) as db:
        res = db.run(
            'select application_name from pg_stat_activity '
            ' where pid = pg_backend_pid()',
        )

        application_name = check.not_none(res)[0][0]
        assert application_name == app_name


def test_application_name_integer(db_kwargs):
    db_kwargs['application_name'] = 1
    with pytest.raises(
        InterfaceError,
        match=r"The parameter application_name can't be of type <class 'int'>.",
    ):
        Connection(**db_kwargs)


def test_application_name_bytearray(db_kwargs):
    db_kwargs['application_name'] = bytearray(b'Philby')
    with Connection(**db_kwargs):
        pass


class Og8000TestError(Exception):
    pass


def raise_exception(val):
    raise Og8000TestError('oh noes!')


def test_py_value_fail(con):
    # Ensure that if an out adapter throws an exception, the original exception is raised (Og8000TestError), and the
    # connection is still usable after the error.
    con.register_out_adapter(datetime.time, raise_exception)

    with pytest.raises(Og8000TestError):
        con.run('SELECT CAST(:v AS TIME)', v=datetime.time(10, 30))

    # ensure that the connection is still usable for a new query
    res = con.run("VALUES ('hw3'::text)")
    assert res[0][0] == 'hw3'


def test_no_data_error_recovery(con):
    for _ in range(1, 4):
        with pytest.raises(DatabaseError) as e:
            con.run('DROP TABLE test_og8000_no_such_table')
        assert e.value.args[0]['C'] == '42P01'
        con.run('ROLLBACK')


def test_closed_connection(con):
    con.close()
    with pytest.raises(InterfaceError, match='connection is closed'):
        con.run("VALUES ('hw1'::text)")


@pytest.mark.parametrize(
    'commit',
    [
        'commit',
        'COMMIT;',
    ],
)
def test_failed_transaction_commit(con, commit):
    con.run('create temporary table tt (f1 int primary key)')
    con.run('begin')
    try:
        con.run('insert into tt(f1) values(null)')
    except DatabaseError:
        pass

    with pytest.raises(InterfaceError):
        con.run(commit)


@pytest.mark.parametrize(
    'rollback',
    [
        'rollback',
        'rollback;',
        'ROLLBACK ;',
    ],
)
def test_failed_transaction_rollback(con, rollback):
    con.run('create temporary table tt (f1 int primary key)')
    con.run('begin')
    try:
        con.run('insert into tt(f1) values(null)')
    except DatabaseError:
        pass

    con.run(rollback)


@pytest.mark.parametrize(
    'rollback',
    [
        'rollback to sp',
        'rollback to sp;',
        'ROLLBACK TO sp ;',
    ],
)
def test_failed_transaction_rollback_to_savepoint(con, rollback):
    con.run('create temporary table tt (f1 int primary key)')
    con.run('begin')
    con.run('SAVEPOINT sp;')

    try:
        con.run('insert into tt(f1) values(null)')
    except DatabaseError:
        pass

    con.run(rollback)


@pytest.mark.parametrize(
    'sql',
    [
        'BEGIN',
        'select * from tt;',
    ],
)
def test_failed_transaction_sql(con, sql):
    con.run('create temporary table tt (f1 int primary key)')
    con.run('begin')
    try:
        con.run('insert into tt(f1) values(null)')
    except DatabaseError:
        pass

    with pytest.raises(DatabaseError):
        con.run(sql)


def test_parameter_statuses(con):
    role_name = 'test_og8000_Æthelred'
    try:
        con.run(f'create role {role_name}')
    except DatabaseError:
        pass
    try:
        con.run(f"set session authorization '{role_name}'")
        assert role_name == con.parameter_statuses['session_authorization']
    finally:
        con.run('reset session authorization')
        con.run(f'drop role if exists {role_name}')
