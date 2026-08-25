import os.path

import pytest

from .. import cursors
from ..constants import ER
from ..errors import OperationalError


def _data_file(name):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', name)


def test_no_file(connect):
    """Test load local infile when the file does not exist."""

    conn = connect()
    c = conn.cursor()
    c.execute('CREATE TABLE test_load_local (a INTEGER, b INTEGER)')
    try:
        with pytest.raises(OperationalError):
            c.execute(
                "LOAD DATA LOCAL INFILE 'no_data.txt' INTO TABLE "
                "test_load_local fields terminated by ','",
            )
    finally:
        c.execute('DROP TABLE test_load_local')
        c.close()


def test_load_file(connect):
    """Test load local infile with a valid file."""

    conn = connect()
    c = conn.cursor()
    c.execute('CREATE TABLE test_load_local (a INTEGER, b INTEGER)')
    filename = _data_file('load_local_data.txt')
    try:
        c.execute(
            f"LOAD DATA LOCAL INFILE '{filename}' INTO TABLE test_load_local"
            " FIELDS TERMINATED BY ','",
        )
        c.execute('SELECT COUNT(*) FROM test_load_local')
        assert c.fetchone()[0] == 22749
    finally:
        c.execute('DROP TABLE test_load_local')


def test_unbuffered_load_file(connect):
    """Test unbuffered load local infile with a valid file."""

    conn = connect()
    c = conn.cursor(cursors.SSCursor)
    c.execute('CREATE TABLE test_load_local (a INTEGER, b INTEGER)')
    filename = _data_file('load_local_data.txt')
    try:
        c.execute(
            f"LOAD DATA LOCAL INFILE '{filename}' INTO TABLE test_load_local"
            " FIELDS TERMINATED BY ','",
        )
        c.execute('SELECT COUNT(*) FROM test_load_local')
        assert c.fetchone()[0] == 22749
    finally:
        c.close()
        conn.close()
        conn.connect()
        c = conn.cursor()
        c.execute('DROP TABLE test_load_local')


def test_load_warnings(connect):
    """Test load local infile produces the appropriate warnings."""

    conn = connect()
    c = conn.cursor()
    c.execute('CREATE TABLE test_load_local (a INTEGER, b INTEGER)')
    filename = _data_file('load_local_warn_data.txt')
    try:
        c.execute(
            f"LOAD DATA LOCAL INFILE '{filename}' INTO TABLE "
            "test_load_local FIELDS TERMINATED BY ','",
        )
        assert c.warning_count == 1

        c.execute('SHOW WARNINGS')
        w = c.fetchone()

        assert w[1] == ER.TRUNCATED_WRONG_VALUE_FOR_FIELD
        assert 'incorrect integer value' in w[2].lower()
    finally:
        c.execute('DROP TABLE test_load_local')
        c.close()
