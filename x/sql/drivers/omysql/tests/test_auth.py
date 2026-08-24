"""Test for auth methods supported by MySQL 8. These need the specially-configured users created by run-mysql."""
import pytest

from ... import omysql
from .dbs import CA_PEM


PASS_SHA256 = 'pass_sha256_01234567890123456789'
PASS_CACHING_SHA2 = 'pass_caching_sha2_01234567890123456789'


@pytest.fixture
def auth_db(databases):
    """The host/port of the primary test database, plus the server CA for the ssl variants."""

    db = databases[0]
    return {
        'host': db['host'],
        'port': db['port'],
        'ssl': {'ca': CA_PEM, 'check_hostname': False},
    }


def test_sha256_no_password(auth_db):
    con = omysql.connect(user='nopass_sha256', host=auth_db['host'], port=auth_db['port'], ssl=None)
    con.close()


def test_sha256_no_password_ssl(auth_db):
    con = omysql.connect(user='nopass_sha256', host=auth_db['host'], port=auth_db['port'], ssl=auth_db['ssl'])
    con.close()


def test_sha256_password(auth_db):
    con = omysql.connect(
        user='user_sha256', password=PASS_SHA256, host=auth_db['host'], port=auth_db['port'], ssl=None,
    )
    con.close()


def test_sha256_password_ssl(auth_db):
    con = omysql.connect(
        user='user_sha256', password=PASS_SHA256, host=auth_db['host'], port=auth_db['port'], ssl=auth_db['ssl'],
    )
    con.close()


def test_caching_sha2_no_password(auth_db):
    con = omysql.connect(user='nopass_caching_sha2', host=auth_db['host'], port=auth_db['port'], ssl=None)
    con.close()


def test_caching_sha2_no_password_ssl(auth_db):
    con = omysql.connect(user='nopass_caching_sha2', host=auth_db['host'], port=auth_db['port'], ssl=auth_db['ssl'])
    con.close()


def test_caching_sha2_password(auth_db):
    con = omysql.connect(
        user='user_caching_sha2',
        password=PASS_CACHING_SHA2,
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=None,
    )
    con.close()

    # Fast path of caching sha2
    con = omysql.connect(
        user='user_caching_sha2',
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
            user='user_caching_sha2',
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
        user='user_caching_sha2',
        password=PASS_CACHING_SHA2,
        host=auth_db['host'],
        port=auth_db['port'],
        ssl=auth_db['ssl'],
    )
    con.close()

    # Fast path of caching sha2
    con = omysql.connect(
        user='user_caching_sha2',
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
            user='user_caching_sha2',
            password=PASS_CACHING_SHA2,
            host=auth_db['host'],
            port=auth_db['port'],
            ssl=auth_db['ssl'],
        )
        con.query('FLUSH PRIVILEGES')
        con.close()
    finally:
        omysql.connections._DEFAULT_AUTH_PLUGIN = None  # noqa: SLF001
