# Copyright (c) 2007-2009, Mathieu Fenniak
# Copyright (c) The Contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#   disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials provided with the distribution.
# * The name of the author may not be used to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Original Author: Mathieu Fenniak
import datetime
import itertools
import socket
import time
import typing as ta
import warnings

from omcore import check

from .converters import BIGINT
from .converters import BOOLEAN  # noqa: F401
from .converters import BOOLEAN_ARRAY  # noqa: F401
from .converters import BYTES
from .converters import CHAR
from .converters import CHAR_ARRAY  # noqa: F401
from .converters import DATE
from .converters import FLOAT
from .converters import FLOAT_ARRAY  # noqa: F401
from .converters import INET  # noqa: F401
from .converters import INT2VECTOR  # noqa: F401
from .converters import INTEGER
from .converters import INTEGER_ARRAY  # noqa: F401
from .converters import INTERVAL
from .converters import JSON  # noqa: F401
from .converters import JSONB  # noqa: F401
from .converters import MACADDR  # noqa: F401
from .converters import NAME
from .converters import NAME_ARRAY  # noqa: F401
from .converters import NULLTYPE  # noqa: F401
from .converters import NUMERIC
from .converters import NUMERIC_ARRAY  # noqa: F401
from .converters import OID
from .converters import PY_PG
from .converters import REAL
from .converters import SMALLINT
from .converters import TEXT
from .converters import TEXT_ARRAY  # noqa: F401
from .converters import TIME
from .converters import TIMESTAMP
from .converters import TIMESTAMPTZ
from .converters import UNKNOWN
from .converters import UUID_TYPE  # noqa: F401
from .converters import VARCHAR
from .converters import VARCHAR_ARRAY  # noqa: F401
from .converters import XID  # noqa: F401
from .core.sync import SyncCoreConnection
from .errors import DatabaseError
from .errors import Error
from .errors import InterfaceError
from .protocol.codes import TransactionStatus
from .protocol.session import Context
from .protocol.session import CopyStream
from .types import PGInterval  # noqa: F401
from .types import Range  # noqa: F401


if ta.TYPE_CHECKING:
    import ssl


ExceptionT = ta.TypeVar('ExceptionT', bound=Exception)

QueryArgs: ta.TypeAlias = ta.Sequence[ta.Any] | ta.Mapping[str, ta.Any]

Xid: ta.TypeAlias = tuple[int, str, str]


##


apilevel = '2.0'

threadsafety = 1

paramstyle = 'format'


##
# Type objects


class DbapiTypeObject:
    """
    A DB-API type object: compares equal to every type code (PostgreSQL type oid) of the kind of column it describes.
    Its first oid is the one used when it is given to `Cursor.setinputsizes`.
    """

    def __init__(self, name: str, *oids: int) -> None:
        super().__init__()

        check.not_empty(oids)
        self._name = name
        self._oids = tuple(oids)
        self._oid_set = frozenset(oids)

    @property
    def name(self) -> str:
        return self._name

    @property
    def oid(self) -> int:
        return self._oids[0]

    @property
    def oids(self) -> ta.Sequence[int]:
        return self._oids

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._name!r}, {", ".join(map(str, self._oids))})'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DbapiTypeObject):
            return self._oid_set == other._oid_set
        if isinstance(other, int):
            return other in self._oid_set
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._oid_set)


STRING = DbapiTypeObject('STRING', VARCHAR, TEXT, CHAR, NAME)
BINARY = DbapiTypeObject('BINARY', BYTES)
NUMBER = DbapiTypeObject('NUMBER', NUMERIC, INTEGER, BIGINT, SMALLINT, FLOAT, REAL)
DATETIME = DbapiTypeObject('DATETIME', TIMESTAMP, TIMESTAMPTZ, DATE, TIME, INTERVAL)
ROWID = DbapiTypeObject('ROWID', OID)


##
# Type constructors


Date = datetime.date
Time = datetime.time


def PgDate(year: int, month: int, day: int) -> Date:  # noqa: N802
    """
    Construct an object holding a date value.

    This function is part of the `DBAPI 2.0 specification <http://www.python.org/dev/peps/pep-0249/>`_.

    :rtype: :class:`datetime.date`
    """

    return Date(year, month, day)


def PgTime(hour: int, minute: int, second: int) -> Time:  # noqa: N802
    """
    Construct an object holding a time value.

    This function is part of the `DBAPI 2.0 specification <http://www.python.org/dev/peps/pep-0249/>`_.

    :rtype: :class:`datetime.time`
    """

    return Time(hour, minute, second)


def Timestamp(year: int, month: int, day: int, hour: int, minute: int, second: int) -> datetime.datetime:  # noqa: N802
    """
    Construct an object holding a timestamp value.

    This function is part of the `DBAPI 2.0 specification <http://www.python.org/dev/peps/pep-0249/>`_.

    :rtype: :class:`datetime.datetime`
    """

    return datetime.datetime(year, month, day, hour, minute, second)


def DateFromTicks(ticks: float) -> Date:  # noqa: N802
    """
    Construct an object holding a date value from the given ticks value
    (number of seconds since the epoch).

    This function is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.

    :rtype: :class:`datetime.date`
    """

    return Date(*time.localtime(ticks)[:3])


def TimeFromTicks(ticks: float) -> Time:  # noqa: N802
    """
    Construct an object holding a time value from the given ticks value
    (number of seconds since the epoch).

    This function is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.

    :rtype: :class:`datetime.time`
    """

    return Time(*time.localtime(ticks)[3:6])


def TimestampFromTicks(ticks: float) -> datetime.datetime:  # noqa: N802
    """
    Construct an object holding a timestamp value from the given ticks value
    (number of seconds since the epoch).

    This function is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.

    :rtype: :class:`datetime.datetime`
    """

    return Timestamp(*time.localtime(ticks)[:6])


def Binary(value: bytes) -> bytes:  # noqa: N802
    """
    Construct an object holding binary data.

    This function is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.
    """

    return value


def connect(
    user: str | bytes,
    host: str | None = 'localhost',
    database: str | bytes | None = None,
    port: int = 5432,
    password: str | bytes | None = None,
    source_address: tuple[str, int] | None = None,
    unix_sock: str | None = None,
    ssl_context: ssl.SSLContext | bool | None = None,
    timeout: float | None = None,
    tcp_keepalive: bool = True,
    application_name: str | bytes | None = None,
    replication: str | bytes | None = None,
    startup_params: ta.Mapping[str, str | bytes] | None = None,
    sock: socket.socket | None = None,
) -> Connection:
    return Connection(
        user,
        host=host,
        database=database,
        port=port,
        password=password,
        source_address=source_address,
        unix_sock=unix_sock,
        ssl_context=ssl_context,
        timeout=timeout,
        tcp_keepalive=tcp_keepalive,
        application_name=application_name,
        replication=replication,
        startup_params=startup_params,
        sock=sock,
    )


def convert_paramstyle(style: str, query: str, args: QueryArgs) -> tuple[str, QueryArgs]:
    # I don't see any way to avoid scanning the query string char by char,
    # so we might as well take that careful approach and create a
    # state-based scanner. We'll use int variables for the state.
    OUTSIDE = 0  # outside quoted string
    INSIDE_SQ = 1  # inside single-quote string '...'
    INSIDE_QI = 2  # inside quoted identifier   "..."
    INSIDE_ES = 3  # inside escaped single-quote string, E'...'
    INSIDE_PN = 4  # inside parameter name eg. :name
    INSIDE_CO = 5  # inside inline comment eg. --
    INSIDE_DQ = 6  # inside escaped dollar-quote string, $$...$$

    in_quote_escape = False
    in_param_escape = False
    placeholders: list[str] = []
    output_query: list[str] = []
    param_idx = map(lambda x: '$' + str(x), itertools.count(1))
    state = OUTSIDE
    prev_c: str | None = None

    for i, c in enumerate(query):
        next_c = query[i + 1] if i + 1 < len(query) else None

        if state == OUTSIDE:
            if c == "'":
                output_query.append(c)
                if prev_c == 'E':
                    state = INSIDE_ES
                else:
                    state = INSIDE_SQ

            elif c == '"':
                output_query.append(c)
                state = INSIDE_QI

            elif c == '-':
                output_query.append(c)
                if prev_c == '-':
                    state = INSIDE_CO

            elif c == '$':
                output_query.append(c)
                if prev_c == '$':
                    state = INSIDE_DQ

            elif style == 'qmark' and c == '?':
                output_query.append(next(param_idx))

            elif (
                style == 'numeric' and
                c == ':' and
                next_c and
                next_c not in ':=' and
                prev_c != ':'
            ):
                # Treat : as beginning of parameter name if and only if it's the only : around
                # Needed to properly process type conversions i.e. sum(x)::float
                output_query.append('$')

            elif (
                    style == 'named' and
                    c == ':' and
                    next_c and
                    next_c not in ':=' and
                    prev_c != ':'
            ):
                # Same logic for : as in numeric parameters
                state = INSIDE_PN
                placeholders.append('')

            elif style == 'pyformat' and c == '%' and next_c == '(':
                state = INSIDE_PN
                placeholders.append('')

            elif style in ('format', 'pyformat') and c == '%':
                style = 'format'
                if in_param_escape:
                    in_param_escape = False
                    output_query.append(c)
                else:
                    if next_c == '%':
                        in_param_escape = True
                    elif next_c == 's':
                        state = INSIDE_PN
                        output_query.append(next(param_idx))
                    else:
                        raise InterfaceError(
                            'Only %s and %% are supported in the query.',
                        )

            else:
                output_query.append(c)

        elif state == INSIDE_SQ:
            if c == "'":
                if in_quote_escape:
                    in_quote_escape = False
                else:
                    if next_c == "'":
                        in_quote_escape = True
                    else:
                        state = OUTSIDE
            output_query.append(c)

        elif state == INSIDE_QI:
            if c == '"':
                state = OUTSIDE
            output_query.append(c)

        elif state == INSIDE_ES:
            if c == "'" and prev_c != '\\':
                # check for escaped single-quote
                state = OUTSIDE
            output_query.append(c)

        elif state == INSIDE_DQ:
            if c == '$' and prev_c == '$':
                state = OUTSIDE
            output_query.append(c)

        elif state == INSIDE_PN:
            if style == 'named':
                placeholders[-1] += c
                if next_c is None or (not next_c.isalnum() and next_c != '_'):
                    state = OUTSIDE
                    try:
                        pidx = placeholders.index(placeholders[-1], 0, -1)
                        output_query.append('$' + str(pidx + 1))
                        del placeholders[-1]
                    except ValueError:
                        output_query.append('$' + str(len(placeholders)))

            elif style == 'pyformat':
                if prev_c == ')' and c == 's':
                    state = OUTSIDE
                    try:
                        pidx = placeholders.index(placeholders[-1], 0, -1)
                        output_query.append('$' + str(pidx + 1))
                        del placeholders[-1]
                    except ValueError:
                        output_query.append('$' + str(len(placeholders)))
                elif c in '()':
                    pass
                else:
                    placeholders[-1] += c

            elif style == 'format':
                state = OUTSIDE

        elif state == INSIDE_CO:
            output_query.append(c)
            if c == '\n':
                state = OUTSIDE

        prev_c = c

    if style in ('numeric', 'qmark', 'format'):
        vals = args
    else:
        vals = tuple(args[p] for p in placeholders)  # type: ignore[call-overload]

    return ''.join(output_query), vals


class Cursor:
    def __init__(self, connection: Connection) -> None:
        self._c = connection
        self.arraysize = 1

        self._context: Context | None = None
        self._row_iter: ta.Iterator[list[ta.Any]] | None = None

        self._input_oids: ta.Sequence[int] = ()

    @property
    def connection(self) -> Connection:
        warnings.warn('DB-API extension cursor.connection used', stacklevel=3)
        return self._c

    @property
    def rowcount(self) -> int:
        context = self._context
        if context is None:
            return -1

        return context.row_count

    @property
    def description(self) -> list[tuple[str, int, None, None, None, None, None]] | None:
        context = self._context
        if context is None:
            return None

        row_desc = context.columns
        if row_desc is None:
            return None
        if len(row_desc) == 0:
            return None
        columns: list[tuple[str, int, None, None, None, None, None]] = []
        for col in row_desc:
            columns.append((col['name'], col['type_oid'], None, None, None, None, None))
        return columns

    # Executes a database operation. Parameters may be provided as a sequence or mapping and will be bound to variables
    # in the operation.
    def execute(self, operation: str, args: QueryArgs = (), stream: CopyStream | None = None) -> None:
        """
        Executes a database operation. Parameters may be provided as a sequence, or as a mapping, depending upon the
        value of :data:`pg8000.paramstyle`.

        This method is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.

        :param operation:
            The SQL statement to execute.

        :param args:
            If :data:`paramstyle` is ``qmark``, ``numeric``, or ``format``, this argument should be an array of
            parameters to bind into the statement. If :data:`paramstyle` is ``named``, the argument should be a dict
            mapping of parameters. If the :data:`paramstyle` is ``pyformat``, the argument value may be either an array
            or a mapping.

        :param stream:
             This is a pg8000 extension for use with the PostgreSQL
            `COPY <http://www.postgresql.org/docs/current/static/sql-copy.html>`_ command. For a COPY FROM the parameter
            must be a readable file-like object, and for COPY TO it must be writable.
        """

        try:
            if not self._c._in_transaction and not self._c.autocommit:
                self._c.execute_simple('begin transaction')

            if len(args) == 0 and stream is None:
                self._context = self._c.execute_simple(operation)
            else:
                statement, vals = convert_paramstyle(paramstyle, operation, args)
                self._context = self._c.execute_unnamed(
                    statement, vals=vals, oids=self._input_oids, stream=stream,
                )

            if self._context.rows is None:
                self._row_iter = None
            else:
                self._row_iter = iter(self._context.rows)
            self._input_oids = ()
        except AttributeError:
            if self._c is None:
                raise InterfaceError('Cursor closed') from None
            raise

        self.input_types: list[ta.Any] = []

    def executemany(self, operation: str, param_sets: ta.Iterable[QueryArgs]) -> None:
        """
        Prepare a database operation, and then execute it against all
        parameter sequences or mappings provided.

        This method is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.

        :param operation:
            The SQL statement to execute
        :param parameter_sets:
            A sequence of parameters to execute the statement with. The values
            in the sequence should be sequences or mappings of parameters, the
            same as the args argument of the :meth:`execute` method.
        """

        rowcounts: list[int] = []
        input_oids = self._input_oids
        for parameters in param_sets:
            self._input_oids = input_oids
            self.execute(operation, parameters)
            rowcounts.append(self._context.row_count)  # type: ignore[union-attr]

        if len(rowcounts) == 0:
            self._context = Context(None)
        elif -1 in rowcounts:
            self._context.row_count = -1  # type: ignore[union-attr]
        else:
            self._context.row_count = sum(rowcounts)  # type: ignore[union-attr]

    def callproc(self, procname: str, parameters: ta.Sequence[ta.Any] | None = None) -> None:
        args = [] if parameters is None else parameters
        operation = f'CALL {procname}(' + ', '.join(['%s' for _ in args]) + ')'

        try:
            statement, vals = convert_paramstyle('format', operation, args)

            self._context = self._c.execute_unnamed(statement, vals=vals)

            if self._context.rows is None:
                self._row_iter = None
            else:
                self._row_iter = iter(self._context.rows)

        except AttributeError:
            if self._c is None:
                raise InterfaceError('Cursor closed') from None
            raise

    def fetchone(self) -> list[ta.Any] | None:
        """
        Fetch the next row of a query result set.

        This method is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.

        :returns:
            A row as a sequence of field values, or ``None`` if no more rows
            are available.
        """

        try:
            return next(self)
        except StopIteration:
            return None
        except TypeError:
            raise ProgrammingError('attempting to use unexecuted cursor')

    def __iter__(self) -> ta.Self:
        """
        A cursor object is iterable to retrieve the rows from a query.

        This is a DBAPI 2.0 extension.
        """

        return self

    def __next__(self) -> list[ta.Any]:
        try:
            return next(self._row_iter)  # type: ignore[arg-type]
        except AttributeError:
            if self._context is None:
                raise ProgrammingError("A query hasn't been issued.")
            else:
                raise
        except StopIteration as e:
            if self._context is None:
                raise ProgrammingError("A query hasn't been issued.")
            elif len(self._context.columns) == 0:  # type: ignore[arg-type]
                raise ProgrammingError('no result set')
            else:
                raise e

    def fetchmany(self, num: int | None = None) -> tuple[list[ta.Any], ...]:
        """
        Fetches the next set of rows of a query result.

        This method is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.

        :param size:

            The number of rows to fetch when called. If not provided, the
            :attr:`arraysize` attribute value is used instead.

        :returns:

            A sequence, each entry of which is a sequence of field values
            making up a row. If no more rows are available, an empty sequence
            will be returned.
        """

        try:
            return tuple(itertools.islice(self, self.arraysize if num is None else num))
        except TypeError:
            raise ProgrammingError('attempting to use unexecuted cursor')

    def fetchall(self) -> tuple[list[ta.Any], ...]:
        """
        Fetches all remaining rows of a query result.

        This method is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.

        :returns:

            A sequence, each entry of which is a sequence of field values
            making up a row.
        """

        try:
            return tuple(self)
        except TypeError:
            raise ProgrammingError('attempting to use unexecuted cursor')

    def close(self) -> None:
        """
        Closes the cursor.

        This method is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.
        """

        # The AttributeError from using a None connection is relied upon to detect a closed cursor.
        self._c = None  # type: ignore[assignment]

    def setinputsizes(self, sizes: ta.Sequence[int | DbapiTypeObject | type | None]) -> None:
        """
        This method is part of the `DBAPI 2.0 specification <http://www.python.org/dev/peps/pep-0249/>`_.

        Each size may be a PostgreSQL type oid, a DB-API type object, or a Python type with a default oid, and fixes the
        type of the corresponding parameter of the next `execute` call.
        """

        oids: list[int] = []
        for size in sizes:
            if isinstance(size, DbapiTypeObject):
                oid = size.oid
            elif isinstance(size, int):
                oid = size
            elif size is None:
                oid = UNKNOWN
            else:
                try:
                    oid = PY_PG[size]
                except KeyError:
                    oid = UNKNOWN
            oids.append(oid)

        self._input_oids = oids

    def setoutputsize(self, size: int, column: int | None = None) -> None:
        """
        This method is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_, however, it is not
        implemented by pg8000.
        """

        pass


class Connection(SyncCoreConnection):
    def __init__(self, *args: ta.Any, **kwargs: ta.Any) -> None:
        super().__init__(*args, **kwargs)
        self.autocommit = False
        self._xid: Xid | None = None

    # DBAPI Extension: supply exceptions as attributes on the connection
    Warning = property(lambda self: self._get_error(Warning))
    Error = property(lambda self: self._get_error(Error))
    InterfaceError = property(lambda self: self._get_error(InterfaceError))
    DatabaseError = property(lambda self: self._get_error(DatabaseError))
    DataError = property(lambda self: self._get_error(DataError))
    OperationalError = property(lambda self: self._get_error(OperationalError))
    IntegrityError = property(lambda self: self._get_error(IntegrityError))
    InternalError = property(lambda self: self._get_error(InternalError))
    ProgrammingError = property(lambda self: self._get_error(ProgrammingError))
    NotSupportedError = property(lambda self: self._get_error(NotSupportedError))

    def _get_error(self, error: type[ExceptionT]) -> type[ExceptionT]:
        warnings.warn(f'DB-API extension connection.{error.__name__} used', stacklevel=3)
        return error

    @property
    def _in_transaction(self) -> bool:
        return self.transaction_status in (TransactionStatus.IN_TRANSACTION, TransactionStatus.IN_FAILED_TRANSACTION)

    def cursor(self) -> Cursor:
        """
        Creates a :class:`Cursor` object bound to this
        connection.

        This function is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.
        """

        return Cursor(self)

    def commit(self) -> None:
        """
        Commits the current database transaction.

        This function is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.
        """

        self.execute_unnamed('commit')

    def rollback(self) -> None:
        """
        Rolls back the current database transaction.

        This function is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.
        """

        if not self._in_transaction:
            return
        self.execute_unnamed('rollback')

    def xid(self, format_id: int, global_transaction_id: str, branch_qualifier: str) -> Xid:
        """
        Create a Transaction IDs (only global_transaction_id is used in pg)
        format_id and branch_qualifier are not used in postgres
        global_transaction_id may be any string identifier supported by
        postgres returns a tuple
        (format_id, global_transaction_id, branch_qualifier)
        """

        return (format_id, global_transaction_id, branch_qualifier)

    def tpc_begin(self, xid: Xid) -> None:
        """
        Begins a TPC transaction with the given transaction ID xid.

        This method should be called outside of a transaction (i.e. nothing may
        have executed since the last .commit() or .rollback()).

        Furthermore, it is an error to call .commit() or .rollback() within the
        TPC transaction. A ProgrammingError is raised, if the application calls
        .commit() or .rollback() during an active TPC transaction.

        This function is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.
        """

        self._xid = xid
        if self.autocommit:
            self.execute_unnamed('begin transaction')

    def tpc_prepare(self) -> None:
        """
        Performs the first phase of a transaction started with .tpc_begin().
        A ProgrammingError is be raised if this method is called outside of a
        TPC transaction.

        After calling .tpc_prepare(), no statements can be executed until
        .tpc_commit() or .tpc_rollback() have been called.

        This function is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.
        """

        self.execute_unnamed("PREPARE TRANSACTION '%s';" % (self._xid[1],))  # type: ignore[index]

    def tpc_commit(self, xid: Xid | None = None) -> None:
        """
        When called with no arguments, .tpc_commit() commits a TPC
        transaction previously prepared with .tpc_prepare().

        If .tpc_commit() is called prior to .tpc_prepare(), a single phase
        commit is performed. A transaction manager may choose to do this if
        only a single resource is participating in the global transaction.

        When called with a transaction ID xid, the database commits the given
        transaction. If an invalid transaction ID is provided, a
        ProgrammingError will be raised. This form should be called outside of
        a transaction, and is intended for use in recovery.

        On return, the TPC transaction is ended.

        This function is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.
        """

        if xid is None:
            xid = self._xid

        if xid is None:
            raise ProgrammingError('Cannot tpc_commit() without a TPC transaction!')

        try:
            previous_autocommit_mode = self.autocommit
            self.autocommit = True
            if xid in self.tpc_recover():
                self.execute_unnamed("COMMIT PREPARED '%s';" % (xid[1],))
            else:
                # a single-phase commit
                self.commit()
        finally:
            self.autocommit = previous_autocommit_mode
        self._xid = None

    def tpc_rollback(self, xid: Xid | None = None) -> None:
        """
        When called with no arguments, .tpc_rollback() rolls back a TPC
        transaction. It may be called before or after .tpc_prepare().

        When called with a transaction ID xid, it rolls back the given
        transaction. If an invalid transaction ID is provided, a
        ProgrammingError is raised. This form should be called outside of a
        transaction, and is intended for use in recovery.

        On return, the TPC transaction is ended.

        This function is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.
        """

        if xid is None:
            xid = self._xid

        if xid is None:
            raise ProgrammingError(
                'Cannot tpc_rollback() without a TPC prepared transaction!',
            )

        try:
            previous_autocommit_mode = self.autocommit
            self.autocommit = True
            if xid in self.tpc_recover():
                # a two-phase rollback
                self.execute_unnamed("ROLLBACK PREPARED '%s';" % (xid[1],))
            else:
                # a single-phase rollback
                self.rollback()
        finally:
            self.autocommit = previous_autocommit_mode
        self._xid = None

    def tpc_recover(self) -> list[Xid]:
        """
        Returns a list of pending transaction IDs suitable for use with
        .tpc_commit(xid) or .tpc_rollback(xid).

        This function is part of the `DBAPI 2.0 specification
        <http://www.python.org/dev/peps/pep-0249/>`_.
        """

        try:
            previous_autocommit_mode = self.autocommit
            self.autocommit = True
            curs = self.cursor()
            curs.execute('select gid FROM pg_prepared_xacts')
            return [self.xid(0, row[0], '') for row in curs.fetchall()]
        finally:
            self.autocommit = previous_autocommit_mode


class Warning(Exception):  # noqa: A001,N818
    """
    Generic exception raised for important database warnings like data
    truncations. This exception is not currently used by pg8000.

    This exception is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.
    """

    pass


class DataError(DatabaseError):
    """
    Generic exception raised for errors that are due to problems with the
    processed data. This exception is not currently raised by pg8000.

    This exception is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.
    """

    pass


class OperationalError(DatabaseError):
    """
    Generic exception raised for errors that are related to the database's
    operation and not necessarily under the control of the programmer. This
    exception is currently never raised by pg8000.

    This exception is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.
    """

    pass


class IntegrityError(DatabaseError):
    """
    Generic exception raised when the relational integrity of the database is
    affected. This exception is not currently raised by pg8000.

    This exception is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.
    """

    pass


class InternalError(DatabaseError):
    """
    Generic exception raised when the database encounters an internal error.
    This is currently only raised when unexpected state occurs in the pg8000
    interface itself, and is typically the result of a interface bug.

    This exception is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.
    """

    pass


class ProgrammingError(DatabaseError):
    """
    Generic exception raised for programming errors. For example, this
    exception is raised if more parameter fields are in a query string than
    there are available parameters.

    This exception is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.
    """

    pass


class NotSupportedError(DatabaseError):
    """
    Generic exception raised in case a method or database API was used which
    is not supported by the database.

    This exception is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.
    """

    pass


class ArrayContentNotSupportedError(NotSupportedError):
    """
    Raised when attempting to transmit an array where the base type is not
    supported for binary data transfer by the interface.
    """

    pass
