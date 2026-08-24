import datetime
import os
import socket
import time
import types

import pytest

from ... import omysql
from ..constants import CLIENT
from .utils import mysql_server_is


OSUSER = os.environ.get('USER')


class TempUser:
    def __init__(self, c, user, db, auth=None, authdata=None, password=None):
        self._c = c
        self._user = user
        self._db = db
        create = 'CREATE USER ' + user
        if password is not None:
            create += f" IDENTIFIED BY '{password}'"
        elif auth is not None:
            create += f' IDENTIFIED WITH {auth}'
            if authdata is not None:
                create += f" AS '{authdata}'"
        try:
            c.execute(create)
            self._created = True
        except omysql.err.InternalError:
            # already exists - TODO need to check the same plugin applies
            self._created = False
        try:
            c.execute(f'GRANT SELECT ON {db}.* TO {user}')
            self._grant = True
        except omysql.err.InternalError:
            self._grant = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._grant:
            self._c.execute(f'REVOKE SELECT ON {self._db}.* FROM {self._user}')
        if self._created:
            self._c.execute(f'DROP USER {self._user}')


##
# Authentication


def _without_user(db):
    d = dict(db)
    del d['user']
    return d


def _auth_info(db):
    """Inspects the server's active authentication plugins."""

    info = types.SimpleNamespace(
        socket_found=False,
        socket_plugin_name=None,
        two_questions_found=False,
        three_attempts_found=False,
        pam_found=False,
        pam_plugin_name=None,
        mysql_old_password_found=False,
        sha256_password_found=False,
        ed25519_found=False,
    )

    con = omysql.connect(**db)
    cur = con.cursor()
    cur.execute('SHOW PLUGINS')
    for r in cur:
        if (r[1], r[2]) != ('ACTIVE', 'AUTHENTICATION'):
            continue
        if r[3] == 'auth_socket.so' or r[0] == 'unix_socket':
            info.socket_plugin_name = r[0]
            info.socket_found = True
        elif r[3] == 'dialog_examples.so':
            if r[0] == 'two_questions':
                info.two_questions_found = True
            elif r[0] == 'three_attempts':
                info.three_attempts_found = True
        elif r[0] == 'pam':
            info.pam_found = True
            pam_plugin_name = r[3].split('.')[0]
            if pam_plugin_name == 'auth_pam':
                pam_plugin_name = 'pam'
            info.pam_plugin_name = pam_plugin_name

            # MySQL: authentication_pam
            # https://dev.mysql.com/doc/refman/5.5/en/pam-authentication-plugin.html

            # MariaDB: pam
            # https://mariadb.com/kb/en/mariadb/pam-authentication-plugin/

            # Names differ but functionality is close
        elif r[0] == 'mysql_old_password':
            info.mysql_old_password_found = True
        elif r[0] == 'sha256_password':
            info.sha256_password_found = True
        elif r[0] == 'ed25519':
            info.ed25519_found = True
    con.close()

    return info


def _require_socket_auth(db):
    # socket auth requires the current user and for the connection to be a socket
    # rest do grants @localhost due to incomplete logic - TODO change to @% then
    if not (db.get('unix_socket') is not None and db.get('host') in ('localhost', '127.0.0.1')):
        pytest.skip('connection to unix_socket required')


def _require_pam_env():
    if os.environ.get('PASSWORD') is None:
        pytest.skip('PASSWORD env var required')
    if os.environ.get('PAMSERVICE') is None:
        pytest.skip('PAMSERVICE env var required')


class Dialog:
    fail = False
    m = {}

    def __init__(self, con):
        self.fail = Dialog.fail

    def prompt(self, echo, prompt):
        if self.fail:
            self.fail = False
            return b'bad guess at a password'
        return self.m.get(prompt)


class DialogHandler:
    def __init__(self, con):
        self.con = con

    def authenticate(self, pkt):
        while True:
            flag = pkt.read_uint8()
            # echo = (flag & 0x06) == 0x02
            last = (flag & 0x01) == 0x01
            prompt = pkt.read_all()

            if prompt == b'Password, please:':
                self.con.write_packet(b'stillnotverysecret\0')
            else:
                self.con.write_packet(b'no idea what to do with this prompt\0')
            pkt = self.con._read_packet()  # noqa: SLF001
            pkt.check_error()
            if pkt.is_ok_packet() or last:
                break
        return pkt


class DefectiveHandler:
    def __init__(self, con):
        self.con = con


def _run_socket_auth(connect, db, plugin_name):
    with TempUser(
        connect().cursor(),
        OSUSER + '@localhost',
        db['database'],
        plugin_name,
    ):
        omysql.connect(user=OSUSER, **_without_user(db))


def test_socket_auth_install_plugin(connect, databases):
    db = databases[0]
    _require_socket_auth(db)
    if _auth_info(db).socket_found:
        pytest.skip('socket plugin already installed')

    # needs plugin. lets install it.
    installed_name = None
    cur = connect().cursor()
    try:
        try:
            cur.execute("install plugin auth_socket soname 'auth_socket.so'")
            installed_name = 'auth_socket'
        except omysql.err.InternalError:
            try:
                cur.execute("install soname 'auth_socket'")
                installed_name = 'unix_socket'
            except omysql.err.InternalError:
                pytest.skip("we couldn't install the socket plugin")
        _run_socket_auth(connect, db, installed_name)
    finally:
        if installed_name is not None:
            cur.execute(f'uninstall plugin {installed_name}')


def test_socket_auth(connect, databases):
    db = databases[0]
    _require_socket_auth(db)
    info = _auth_info(db)
    if not info.socket_found:
        pytest.skip('no socket plugin')
    _run_socket_auth(connect, db, info.socket_plugin_name)


def _run_dialog_auth_two_questions(connect, db):
    Dialog.fail = False
    Dialog.m = {
        b'Password, please:': b'notverysecret',
        b'Are you sure ?': b'yes, of course',
    }
    with TempUser(
        connect().cursor(),
        'test_omysql_user@localhost',
        db['database'],
        'two_questions',
        'notverysecret',
    ):
        with pytest.raises(omysql.err.OperationalError):
            omysql.connect(user='test_omysql_user', **_without_user(db))
        omysql.connect(
            user='test_omysql_user',
            auth_plugin_map={b'dialog': Dialog},
            **_without_user(db),
        )


def test_dialog_auth_two_questions_install_plugin(connect, databases):
    db = databases[0]
    _require_socket_auth(db)
    if _auth_info(db).two_questions_found:
        pytest.skip('two_questions plugin already installed')

    # needs plugin. lets install it.
    installed = False
    cur = connect().cursor()
    try:
        try:
            cur.execute("install plugin two_questions soname 'dialog_examples.so'")
            installed = True
        except omysql.err.InternalError:
            pytest.skip("we couldn't install the two_questions plugin")
        _run_dialog_auth_two_questions(connect, db)
    finally:
        if installed:
            cur.execute('uninstall plugin two_questions')


def test_dialog_auth_two_questions(connect, databases):
    db = databases[0]
    _require_socket_auth(db)
    if not _auth_info(db).two_questions_found:
        pytest.skip('no two questions auth plugin')
    _run_dialog_auth_two_questions(connect, db)


def _run_dialog_auth_three_attempts(connect, db):
    Dialog.m = {b'Password, please:': b'stillnotverysecret'}
    Dialog.fail = True  # fail just once. We've got three attempts after all
    with TempUser(
        connect().cursor(),
        'test_omysql_user@localhost',
        db['database'],
        'three_attempts',
        'stillnotverysecret',
    ):
        omysql.connect(user='test_omysql_user', auth_plugin_map={b'dialog': Dialog}, **_without_user(db))
        omysql.connect(user='test_omysql_user', auth_plugin_map={b'dialog': DialogHandler}, **_without_user(db))
        with pytest.raises(omysql.err.OperationalError):
            omysql.connect(user='test_omysql_user', auth_plugin_map={b'dialog': object}, **_without_user(db))

        with pytest.raises(omysql.err.OperationalError):
            omysql.connect(user='test_omysql_user', auth_plugin_map={b'dialog': DefectiveHandler}, **_without_user(db))
        with pytest.raises(omysql.err.OperationalError):
            omysql.connect(user='test_omysql_user', auth_plugin_map={b'notdialogplugin': Dialog}, **_without_user(db))
        Dialog.m = {b'Password, please:': b'I do not know'}
        with pytest.raises(omysql.err.OperationalError):
            omysql.connect(user='test_omysql_user', auth_plugin_map={b'dialog': Dialog}, **_without_user(db))
        Dialog.m = {b'Password, please:': None}
        with pytest.raises(omysql.err.OperationalError):
            omysql.connect(user='test_omysql_user', auth_plugin_map={b'dialog': Dialog}, **_without_user(db))


def test_dialog_auth_three_attempts_install_plugin(connect, databases):
    db = databases[0]
    _require_socket_auth(db)
    if _auth_info(db).three_attempts_found:
        pytest.skip('three_attempts plugin already installed')

    # needs plugin. lets install it.
    installed = False
    cur = connect().cursor()
    try:
        try:
            cur.execute("install plugin three_attempts soname 'dialog_examples.so'")
            installed = True
        except omysql.err.InternalError:
            pytest.skip("we couldn't install the three_attempts plugin")
        _run_dialog_auth_three_attempts(connect, db)
    finally:
        if installed:
            cur.execute('uninstall plugin three_attempts')


def test_dialog_auth_three_attempts(connect, databases):
    db = databases[0]
    _require_socket_auth(db)
    if not _auth_info(db).three_attempts_found:
        pytest.skip('no three attempts plugin')
    _run_dialog_auth_three_attempts(connect, db)


def _run_pam_auth(connect, db):
    pam_db = _without_user(db)
    pam_db['password'] = os.environ.get('PASSWORD')
    cur = connect().cursor()
    try:
        cur.execute('show grants for ' + OSUSER + '@localhost')
        grants = cur.fetchone()[0]
        cur.execute('drop user ' + OSUSER + '@localhost')
    except omysql.OperationalError as e:
        # assuming the user doesn't exist which is ok too
        assert e.args[0] == 1045
        grants = None
    with TempUser(
        cur,
        OSUSER + '@localhost',
        db['database'],
        'pam',
        os.environ.get('PAMSERVICE'),
    ):
        try:
            omysql.connect(user=OSUSER, **pam_db)
            pam_db['password'] = 'very bad guess at password'
            with pytest.raises(omysql.err.OperationalError):
                omysql.connect(
                    user=OSUSER,
                    auth_plugin_map={b'mysql_cleartext_password': DefectiveHandler},
                    **_without_user(db),
                )
        except omysql.OperationalError as e:
            assert e.args[0] == 1045
            # we had 'bad guess at password' work with pam. Well at least we get
            # a permission denied here
            with pytest.raises(omysql.err.OperationalError):
                omysql.connect(
                    user=OSUSER,
                    auth_plugin_map={b'mysql_cleartext_password': DefectiveHandler},
                    **_without_user(db),
                )
    if grants:
        # recreate the user
        cur.execute(grants)


def test_pam_auth_install_plugin(connect, databases):
    db = databases[0]
    _require_socket_auth(db)
    if _auth_info(db).pam_found:
        pytest.skip('pam plugin already installed')
    _require_pam_env()

    # needs plugin. lets install it.
    installed = False
    cur = connect().cursor()
    try:
        try:
            cur.execute("install plugin pam soname 'auth_pam.so'")
            installed = True
        except omysql.err.InternalError:
            pytest.skip("we couldn't install the auth_pam plugin")
        _run_pam_auth(connect, db)
    finally:
        if installed:
            cur.execute('uninstall plugin pam')


def test_pam_auth(connect, databases):
    db = databases[0]
    _require_socket_auth(db)
    if not _auth_info(db).pam_found:
        pytest.skip('no pam plugin')
    _require_pam_env()
    _run_pam_auth(connect, db)


def test_auth_sha256(connect, databases):
    db = databases[0]
    _require_socket_auth(db)
    if not _auth_info(db).sha256_password_found:
        pytest.skip('no sha256 password authentication plugin found')

    conn = connect()
    c = conn.cursor()
    with TempUser(
        c,
        'test_omysql_user@localhost',
        db['database'],
        'sha256_password',
    ):
        c.execute("SET PASSWORD FOR 'test_omysql_user'@'localhost' ='Sh@256Pa33'")
        c.execute('FLUSH PRIVILEGES')
        sha_db = _without_user(db)
        sha_db['password'] = 'Sh@256Pa33'
        # Although SHA256 is supported, need the configuration of public key of
        # the mysql server. Currently will get error by this test.
        with pytest.raises(omysql.err.OperationalError):
            omysql.connect(user='test_omysql_user', **sha_db)


def test_auth_ed25519(connect, databases):
    db = databases[0]
    if not _auth_info(db).ed25519_found:
        pytest.skip('no ed25519 authention plugin')

    ed_db = _without_user(db)
    # The explicit per-user passwords below must win over the configured ones (under either spelling).
    ed_db.pop('password', None)
    ed_db.pop('passwd', None)
    conn = connect()
    c = conn.cursor()
    c.execute("select ed25519_password(''), ed25519_password('ed25519_password')")
    for r in c:
        empty_pass = r[0].decode('ascii')
        non_empty_pass = r[1].decode('ascii')

    with TempUser(
        c,
        'test_omysql_user',
        db['database'],
        'ed25519',
        empty_pass,
    ):
        omysql.connect(user='test_omysql_user', password='', **ed_db)

    with TempUser(
        c,
        'test_omysql_user',
        db['database'],
        'ed25519',
        non_empty_pass,
    ):
        omysql.connect(user='test_omysql_user', password='ed25519_password', **ed_db)


##
# Connection


def test_utf8mb4(connect):
    """This test requires MySQL >= 5.5."""

    connect(charset='utf8mb4')


def test_set_character_set(connect):
    con = connect()
    cur = con.cursor()

    con.set_character_set('latin1')
    cur.execute('SELECT @@character_set_connection')
    assert cur.fetchone() == ('latin1',)
    assert con.encoding == 'cp1252'

    con.set_character_set('utf8mb4', 'utf8mb4_general_ci')
    cur.execute('SELECT @@character_set_connection, @@collation_connection')
    assert cur.fetchone() == ('utf8mb4', 'utf8mb4_general_ci')
    assert con.encoding == 'utf8'


def test_largedata(connect):
    """Large query and response (>=16MB)."""

    cur = connect().cursor()
    cur.execute('SELECT @@max_allowed_packet')
    if cur.fetchone()[0] < 16 * 1024 * 1024 + 10:
        pytest.skip('Set max_allowed_packet to bigger than 17MB')
    t = 'a' * (16 * 1024 * 1024)
    cur.execute("SELECT '" + t + "'")
    assert cur.fetchone()[0] == t


def test_autocommit(connect):
    con = connect()
    assert not con.get_autocommit()

    cur = con.cursor()
    cur.execute('SET AUTOCOMMIT=1')
    assert con.get_autocommit()

    con.autocommit(False)
    assert not con.get_autocommit()
    cur.execute('SELECT @@AUTOCOMMIT')
    assert cur.fetchone()[0] == 0


def test_select_db(connect, databases):
    con = connect()
    current_db = databases[0]['database']
    other_db = databases[1]['database']

    cur = con.cursor()
    cur.execute('SELECT database()')
    assert cur.fetchone()[0] == current_db

    con.select_db(other_db)
    cur.execute('SELECT database()')
    assert cur.fetchone()[0] == other_db


def test_connection_gone_away(connect):
    """
    http://dev.mysql.com/doc/refman/5.0/en/gone-away.html
    http://dev.mysql.com/doc/refman/5.0/en/error-messages-client.html#error_cr_server_gone_error
    """

    con = connect()
    cur = con.cursor()
    cur.execute('SET wait_timeout=1')
    time.sleep(2)
    with pytest.raises(omysql.OperationalError) as cm:
        cur.execute('SELECT 1+1')
    # error occurs while reading, not writing because of socket buffer.
    # assert cm.value.args[0] == 2006
    assert cm.value.args[0] in (2006, 2013)


def test_init_command(connect):
    conn = connect(
        init_command='SELECT "bar"; SELECT "baz"',
        client_flag=CLIENT.MULTI_STATEMENTS,
    )
    c = conn.cursor()
    c.execute('select "foobar";')
    assert c.fetchone() == ('foobar',)
    conn.close()
    with pytest.raises(omysql.err.Error):
        conn.ping(reconnect=False)


def test_read_default_group(connect):
    conn = connect(
        read_default_group='client',
    )
    assert conn.open


def test_set_charset(connect):
    c = connect()
    with pytest.warns(DeprecationWarning):
        c.set_charset('utf8mb4')
    # TODO validate setting here


def test_defer_connect(databases):
    d = databases[0]
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(d['unix_socket'])
    except KeyError:
        sock.close()
        sock = socket.create_connection((d.get('host', 'localhost'), d.get('port', 3306)))
    for k in ['unix_socket', 'host', 'port']:
        try:
            del d[k]
        except KeyError:
            pass

    c = omysql.connect(defer_connect=True, **d)
    assert not c.open
    c.connect(sock)
    c.close()
    sock.close()


##
# Escaping


class Foo:
    """A custom type, escaped by escape_foo."""

    value = 'bar'


def escape_foo(x, d):
    return x.value


def test_escape_string(connect):
    con = connect()
    cur = con.cursor()

    assert con.escape("foo'bar") == "'foo\\'bar'"
    # added NO_AUTO_CREATE_USER as not including it in 5.7 generates warnings
    # mysql-8.0 removes the option however
    if mysql_server_is(con, (8, 0, 0)):
        cur.execute("SET sql_mode='NO_BACKSLASH_ESCAPES'")
    else:
        cur.execute("SET sql_mode='NO_BACKSLASH_ESCAPES,NO_AUTO_CREATE_USER'")
    assert con.escape("foo'bar") == "'foo''bar'"


def test_escape_builtin_encoders(connect):
    con = connect()

    val = datetime.datetime(2012, 3, 4, 5, 6)
    assert con.escape(val, con.encoders) == "'2012-03-04 05:06:00'"


def test_escape_custom_object(connect):
    con = connect()

    mapping = {Foo: escape_foo}
    assert con.escape(Foo(), mapping) == 'bar'


def test_escape_fallback_encoder(connect):
    con = connect()

    class Custom(str):
        pass

    mapping = {str: omysql.converters.escape_string}
    assert con.escape(Custom('foobar'), mapping) == "'foobar'"


def test_escape_no_default(connect):
    con = connect()

    with pytest.raises(TypeError):
        con.escape(42, {})


def test_escape_dict_raise_typeerror(connect):
    """con.escape(dict) should raise TypeError."""

    con = connect()

    with pytest.raises(TypeError):
        con.escape({'foo': Foo()})


def test_escape_list_item(connect):
    con = connect()

    mapping = con.encoders.copy()
    mapping[Foo] = escape_foo
    assert con.escape([Foo()], mapping) == '(bar)'


def test_previous_cursor_not_closed(connect):
    con = connect(
        init_command='SELECT "bar"; SELECT "baz"',
        client_flag=CLIENT.MULTI_STATEMENTS,
    )
    cur1 = con.cursor()
    cur1.execute('SELECT 1; SELECT 2')
    cur2 = con.cursor()
    cur2.execute('SELECT 3')
    assert cur2.fetchone()[0] == 3


def test_commit_during_multi_result(connect):
    con = connect(client_flag=CLIENT.MULTI_STATEMENTS)
    cur = con.cursor()
    cur.execute('SELECT 1; SELECT 2')
    con.commit()
    cur.execute('SELECT 3')
    assert cur.fetchone()[0] == 3
