import pytest

from ..connections import Connection
from ..errors import Error
from ..errors import OperationalError
from ..errors import raise_mysql_exception


def test_error_init_sqlstate():
    error = Error(1234, 'boom', sqlstate='42000')
    assert error.args == (1234, 'boom')
    assert error.sqlstate == '42000'

    error = Error(1234, 'boom')
    assert error.args == (1234, 'boom')
    assert error.sqlstate is None


def test_raise_mysql_exception():
    data = b'\xff\x15\x04#28000Access denied'
    with pytest.raises(OperationalError) as cm:
        raise_mysql_exception(data)
    assert cm.type == OperationalError
    assert cm.value.args == (1045, 'Access denied')
    assert cm.value.sqlstate == '28000'

    data = b'\xff\x10\x04Too many connections'
    with pytest.raises(OperationalError) as cm:
        raise_mysql_exception(data)
    assert cm.type == OperationalError
    assert cm.value.args == (1040, 'Too many connections')
    assert cm.value.sqlstate is None


def test_set_charset_deprecated():
    calls = []

    class RecordingConnection(Connection):
        def __init__(self):
            # Deliberately does not call super().__init__, so no connection is made.
            pass

        def set_character_set(self, charset, collation=None):
            calls.append((charset, collation))

    con = RecordingConnection()
    with pytest.warns(
        DeprecationWarning,
        match="'set_charset' is deprecated, use 'set_character_set' instead",
    ):
        con.set_charset('utf8mb4')
    assert calls == [('utf8mb4', None)]
