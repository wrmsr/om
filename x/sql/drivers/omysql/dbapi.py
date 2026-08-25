from . import connections
from .constants import FIELD_TYPE
from .cursors import DictCursor  # noqa
from .errors import DatabaseError  # noqa
from .errors import DataError  # noqa
from .errors import Error  # noqa
from .errors import IntegrityError  # noqa
from .errors import InterfaceError  # noqa
from .errors import InternalError  # noqa
from .errors import MySQLError  # noqa
from .errors import NotSupportedError  # noqa
from .errors import OperationalError  # noqa
from .errors import ProgrammingError  # noqa
from .errors import Warning  # noqa
from .times import Date  # noqa
from .times import DateFromTicks  # noqa
from .times import Time  # noqa
from .times import TimeFromTicks  # noqa
from .times import Timestamp  # noqa
from .times import TimestampFromTicks  # noqa


##


threadsafety = 1
apilevel = '2.0'
paramstyle = 'pyformat'


##


class DBAPISet(frozenset):
    def __ne__(self, other):
        if isinstance(other, set):
            return frozenset.__ne__(self, other)
        else:
            return other not in self

    def __eq__(self, other):
        if isinstance(other, frozenset):
            return frozenset.__eq__(self, other)
        else:
            return other in self

    def __hash__(self):
        return frozenset.__hash__(self)


STRING = DBAPISet([
    FIELD_TYPE.ENUM,
    FIELD_TYPE.STRING,
    FIELD_TYPE.VAR_STRING,
])

BINARY = DBAPISet([
    FIELD_TYPE.BLOB,
    FIELD_TYPE.LONG_BLOB,
    FIELD_TYPE.MEDIUM_BLOB,
    FIELD_TYPE.TINY_BLOB,
])

NUMBER = DBAPISet([
    FIELD_TYPE.DECIMAL,
    FIELD_TYPE.NEWDECIMAL,
    FIELD_TYPE.DOUBLE,
    FIELD_TYPE.FLOAT,
    FIELD_TYPE.INT24,
    FIELD_TYPE.LONG,
    FIELD_TYPE.LONGLONG,
    FIELD_TYPE.TINY,
    FIELD_TYPE.YEAR,
])

DATE = DBAPISet([
    FIELD_TYPE.DATE,
    FIELD_TYPE.NEWDATE,
])

TIME = DBAPISet([FIELD_TYPE.TIME])

TIMESTAMP = DBAPISet([
    FIELD_TYPE.TIMESTAMP,
    FIELD_TYPE.DATETIME,
])

DATETIME = TIMESTAMP

ROWID = DBAPISet()


def Binary(x):  # noqa
    """Return x as a binary type."""

    return bytes(x)


Connect = connect = Connection = connections.Connection

NULL = 'NULL'
