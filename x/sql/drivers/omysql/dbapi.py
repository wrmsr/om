# ruff: noqa: DTZ001
# Copyright (c) 2010, 2013 PyMySQL contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import datetime
import time

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


##


Date = datetime.date
Time = datetime.time
TimeDelta = datetime.timedelta
Timestamp = datetime.datetime


def DateFromTicks(ticks):  # noqa
    return datetime.date(*time.localtime(ticks)[:3])


def TimeFromTicks(ticks):  # noqa
    return datetime.time(*time.localtime(ticks)[3:6])


def TimestampFromTicks(ticks):  # noqa
    return datetime.datetime(*time.localtime(ticks)[:6])
