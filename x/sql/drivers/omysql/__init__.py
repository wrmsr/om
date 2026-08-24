# Copyright (c) 2010-2016 PyMySQL contributors
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
import sys

from . import connections
from .constants import FIELD_TYPE
from .errors import DatabaseError
from .errors import DataError
from .errors import Error
from .errors import IntegrityError
from .errors import InterfaceError
from .errors import InternalError
from .errors import MySQLError
from .errors import NotSupportedError
from .errors import OperationalError
from .errors import ProgrammingError
from .errors import Warning
from .times import Date
from .times import DateFromTicks
from .times import Time
from .times import TimeFromTicks
from .times import Timestamp
from .times import TimestampFromTicks


# PyMySQL version.
# Used by setuptools and connection_attrs
VERSION = (1, 2, 0, 'final')
VERSION_STRING = '1.2.0'

### for mysqlclient compatibility
### Django checks mysqlclient version.
version_info = (2, 2, 8, 'final', 1)
__version__ = '2.2.8'


def get_client_info():  # for MySQLdb compatibility
    return __version__


def install_as_MySQLdb():
    """
    After this function is called, any application that imports MySQLdb will unwittingly actually use pymysql.
    """

    sys.modules['MySQLdb'] = sys.modules['omysql']


# end of mysqlclient compatibility code

threadsafety = 1
apilevel = '2.0'
paramstyle = 'pyformat'


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


def Binary(x):
    """Return x as a binary type."""

    return bytes(x)


def thread_safe():
    return True  # match MySQLdb.thread_safe()


Connect = connect = Connection = connections.Connection
NULL = 'NULL'
