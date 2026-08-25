"""Test for auth methods supported by MySQL 8."""
import pytest

from ... import omysql


PASS_SHA256 = 'pass_sha256_01234567890123456789'  # noqa: S105
PASS_CACHING_SHA2 = 'pass_caching_sha2_01234567890123456789'  # noqa: S105


@pytest.fixture(scope='module', autouse=True)
def auth_users(mysql_server_params):
    """
    Creates the specially-authenticated users these tests connect as, dropping them again afterwards. Idempotent, so
    leftovers from a previous run killed at any point are absorbed.
    """

    users = [
        ('test_omysql_nopass_sha256', 'sha256_password', None),
        ('test_omysql_user_sha256', 'sha256_password', PASS_SHA256),
        ('test_omysql_nopass_caching_sha2', 'caching_sha2_password', None),
        ('test_omysql_user_caching_sha2', 'caching_sha2_password', PASS_CACHING_SHA2),
    ]

    con = omysql.connect(**mysql_server_params)
    try:
        cur = con.cursor()
        for name, plugin, password in users:
            stmt = f"create user if not exists '{name}'@'%' identified with {plugin}"
            if password is not None:
                stmt += f" by '{password}'"
            cur.execute(stmt)
            # The FLUSH PRIVILEGES calls below run as these users.
            cur.execute(f"grant reload on *.* to '{name}'@'%'")

        yield

        for name, _, _ in users:
            cur.execute(f"drop user if exists '{name}'@'%'")
    finally:
        con.close()


@pytest.fixture
def auth_db(databases, ca_pem):
    """The host/port of the primary test database, plus the server CA for the ssl variants."""

    db = databases[0]
    return {
        'host': db['host'],
        'port': db['port'],
        'ssl': {'ca': ca_pem, 'check_hostname': False},
    }


def test_sha256_no_password(auth_db):
    con = omysql.connect(
        user='test_omysql_nopass_sha256',
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=None,
    )
    con.close()


def test_sha256_no_password_ssl(auth_db):
    con = omysql.connect(
        user='test_omysql_nopass_sha256',
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=auth_db['ssl'],
    )
    con.close()


def test_sha256_password(auth_db):
    con = omysql.connect(
        user='test_omysql_user_sha256',
        password=PASS_SHA256,
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=None,
    )
    con.close()


def test_sha256_password_ssl(auth_db):
    con = omysql.connect(
        user='test_omysql_user_sha256',
        password=PASS_SHA256,
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=auth_db['ssl'],
    )
    con.close()


def test_caching_sha2_no_password(auth_db):
    con = omysql.connect(
        user='test_omysql_nopass_caching_sha2',
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=None,
    )
    con.close()


def test_caching_sha2_no_password_ssl(auth_db):
    con = omysql.connect(
        user='test_omysql_nopass_caching_sha2',
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=auth_db['ssl'],
    )
    con.close()


def test_caching_sha2_password(auth_db):
    con = omysql.connect(
        user='test_omysql_user_caching_sha2',
        password=PASS_CACHING_SHA2,
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=None,
    )
    con.close()

    # Fast path of caching sha2
    con = omysql.connect(
        user='test_omysql_user_caching_sha2',
        password=PASS_CACHING_SHA2,
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=None,
    )
    con.query('FLUSH PRIVILEGES')
    con.close()

    # Fast path after auth_switch_request
    omysql.connections._DEFAULT_AUTH_PLUGIN = 'mysql_native_password'  # noqa: SLF001
    try:
        con = omysql.connect(
            user='test_omysql_user_caching_sha2',
            password=PASS_CACHING_SHA2,
            host=auth_db['host'],
            port=auth_db['port'],
            ssl=auth_db['ssl'],
        )
        con.query('FLUSH PRIVILEGES')
        con.close()
    finally:
        omysql.connections._DEFAULT_AUTH_PLUGIN = None  # noqa: SLF001


def test_caching_sha2_password_ssl(auth_db):
    con = omysql.connect(
        user='test_omysql_user_caching_sha2',
        password=PASS_CACHING_SHA2,
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=auth_db['ssl'],
    )
    con.close()

    # Fast path of caching sha2
    con = omysql.connect(
        user='test_omysql_user_caching_sha2',
        password=PASS_CACHING_SHA2,
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=auth_db['ssl'],
    )
    con.query('FLUSH PRIVILEGES')
    con.close()

    # Fast path after auth_switch_request
    omysql.connections._DEFAULT_AUTH_PLUGIN = 'mysql_native_password'  # noqa: SLF001
    try:
        con = omysql.connect(
            user='test_omysql_user_caching_sha2',
            password=PASS_CACHING_SHA2,
            host=auth_db['host'],
            port=auth_db['port'],
            ssl=auth_db['ssl'],
        )
        con.query('FLUSH PRIVILEGES')
        con.close()
    finally:
        omysql.connections._DEFAULT_AUTH_PLUGIN = None  # noqa: SLF001
