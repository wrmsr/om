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
"""The synchronous cursors: buffered (Cursor, DictCursor) and unbuffered/server-side (SSCursor, SSDictCursor)."""
import typing as ta

from omcore import check

from ..errors import NotSupportedError
from ..errors import ProgrammingError
from .formatting import RE_INSERT_VALUES
from .formatting import backquote_escape
from .formatting import escape_args
from .formatting import mogrify


##


class Cursor:
    """A buffered cursor: the full result of each query is read into memory."""

    #: The maximum size of a statement executemany will build before splitting it.
    max_stmt_length = 1024000

    def __init__(self, connection: ta.Any) -> None:
        super().__init__()

        self.connection = connection
        self.description: tuple[tuple[ta.Any, ...], ...] | None = None
        self.rownumber = 0
        self.rowcount = -1
        self.arraysize = 1
        self.warning_count = 0
        self.lastrowid: ta.Any = None
        self._executed: ta.Any = None
        self._result: ta.Any = None
        self._rows: ta.Sequence[ta.Any] | None = None

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        conn = self.connection
        if conn is None:
            return
        try:
            while self.nextset():
                pass
        finally:
            self.connection = None

    def _get_db(self) -> ta.Any:
        if self.connection is None:
            raise ProgrammingError('Cursor closed')
        return self.connection

    def _check_executed(self) -> None:
        if not self._executed:
            raise ProgrammingError('execute() first')

    def setinputsizes(self, *args: ta.Any) -> None:
        """Does nothing, required by the DB-API."""

    def setoutputsizes(self, *args: ta.Any) -> None:
        """Does nothing, required by the DB-API."""

    def setoutputsize(self, *args: ta.Any) -> None:
        """Does nothing, required by the DB-API."""

    #

    def mogrify(self, query: str, args: ta.Any = None) -> str:
        return mogrify(query, args, self._get_db())

    def execute(self, query: str, args: ta.Any = None) -> int:
        while self.nextset():
            pass
        query = self.mogrify(query, args)
        result = self._query(query)
        self._executed = query
        return result

    def executemany(self, query: str, args: ta.Sequence[ta.Any]) -> int | None:
        if not args:
            return None

        if (m := RE_INSERT_VALUES.match(query)) is not None:
            q_prefix = m.group(1) % ()
            q_values = m.group(2).rstrip()
            q_postfix = m.group(3) or ''
            return self._do_execute_many(q_prefix, q_values, q_postfix, args)

        self.rowcount = sum(self.execute(query, arg) for arg in args)
        return self.rowcount

    def _do_execute_many(self, prefix: str, values: str, postfix: str, args: ta.Sequence[ta.Any]) -> int:
        conn = self._get_db()
        encoding = conn.encoding
        it = iter(args)
        sql = bytearray(prefix.encode(encoding))
        sql += _encode(values % escape_args(next(it), conn), encoding)
        rows = 0
        for arg in it:
            v = _encode(values % escape_args(arg, conn), encoding)
            if len(sql) + len(v) + len(postfix) + 1 > self.max_stmt_length:
                rows += self.execute(bytes(sql) + postfix.encode(encoding))  # type: ignore[arg-type]
                sql = bytearray(prefix.encode(encoding))
            else:
                sql += b','
            sql += v
        rows += self.execute(bytes(sql) + postfix.encode(encoding))  # type: ignore[arg-type]
        self.rowcount = rows
        return rows

    def callproc(self, procname: str, args: ta.Sequence[ta.Any] = ()) -> ta.Sequence[ta.Any]:
        conn = self._get_db()
        escaped = backquote_escape(procname)
        if args:
            fmt = f'@`_{escaped}_%d`=%s'
            self._query('SET ' + ','.join(fmt % (i, conn.escape(a)) for i, a in enumerate(args)))
            self.nextset()
        placeholders = ','.join(f'@`_{escaped}_{i}`' for i in range(len(args)))
        q = f'CALL `{escaped}`({placeholders})'
        self._query(q)
        self._executed = q
        return args

    #

    def _conv_row(self, row: ta.Any) -> ta.Any:
        return row

    def fetchone(self) -> ta.Any:
        self._check_executed()
        if self._rows is None or self.rownumber >= len(self._rows):
            return None
        result = self._rows[self.rownumber]
        self.rownumber += 1
        return result

    def fetchmany(self, size: int | None = None) -> ta.Sequence[ta.Any]:
        self._check_executed()
        if self._rows is None:
            return ()
        end = self.rownumber + (size or self.arraysize)
        result = self._rows[self.rownumber:end]
        self.rownumber = min(end, len(self._rows))
        return result

    def fetchall(self) -> ta.Sequence[ta.Any]:
        self._check_executed()
        if self._rows is None:
            return []
        result = self._rows[self.rownumber:] if self.rownumber else self._rows
        self.rownumber = len(self._rows)
        return result

    def scroll(self, value: int, mode: str = 'relative') -> None:
        self._check_executed()
        if mode == 'relative':
            r = self.rownumber + value
        elif mode == 'absolute':
            r = value
        else:
            raise ProgrammingError(f'unknown scroll mode {mode}')
        if not (0 <= r < len(check.not_none(self._rows))):
            raise IndexError('out of range')
        self.rownumber = r

    def __iter__(self) -> ta.Self:
        return self

    def __next__(self) -> ta.Any:
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

    #

    def nextset(self) -> bool | None:
        return self._nextset(unbuffered=False)

    def _nextset(self, *, unbuffered: bool) -> bool | None:
        conn = self._get_db()
        if self._result is None or self._result is not conn.result:
            return None
        if not self._result.has_next:
            return None
        self._result = None
        self._clear_result()
        conn.next_result(unbuffered=unbuffered)
        self._do_get_result()
        return True

    def _query(self, q: str) -> int:
        conn = self._get_db()
        self._clear_result()
        conn.query(q)
        self._do_get_result()
        return self.rowcount

    def _clear_result(self) -> None:
        self.rownumber = 0
        self._result = None
        self.rowcount = 0
        self.warning_count = 0
        self.description = None
        self.lastrowid = None
        self._rows = None

    def _do_get_result(self) -> None:
        conn = self._get_db()
        self._result = result = conn.result
        self.rowcount = result.affected_rows
        self.warning_count = result.warning_count
        self.description = result.description
        self.lastrowid = result.insert_id
        self._rows = result.rows


def _encode(v: ta.Any, encoding: str) -> bytes:
    return v.encode(encoding, 'surrogateescape') if isinstance(v, str) else v


class DictCursorMixin(Cursor):
    """Turns each row into a dict keyed by column name (mixed in ahead of a concrete Cursor)."""

    dict_type: ta.ClassVar[type] = dict

    _fields: ta.Sequence[str]

    def _do_get_result(self) -> None:
        super()._do_get_result()
        fields: list[str] = []
        if self.description:
            for f in self._result.fields:
                name = f.name
                if name in fields:
                    name = f.table_name + '.' + name
                fields.append(name)
            self._fields = fields
        if fields and self._rows:
            self._rows = [self._conv_row(r) for r in self._rows]

    def _conv_row(self, row: ta.Any) -> ta.Any:
        if row is None:
            return None
        return self.dict_type(zip(self._fields, row, strict=False))


class DictCursor(DictCursorMixin):
    """A buffered cursor whose rows are dicts keyed by column name."""


class SSCursor(Cursor):
    """An unbuffered, server-side cursor: rows are fetched from the server one at a time."""

    def _query(self, q: str) -> int:
        conn = self._get_db()
        self._clear_result()
        conn.query(q, unbuffered=True)
        self._do_get_result()
        return self.rowcount

    def close(self) -> None:
        conn = self.connection
        if conn is None:
            return
        if self._result is not None and self._result is conn.result:
            conn.finish_unbuffered()
        try:
            while self.nextset():
                pass
        finally:
            self.connection = None

    def nextset(self) -> bool | None:
        return self._nextset(unbuffered=True)

    def read_next(self) -> ta.Any:
        return self._conv_row(self._get_db().fetch_unbuffered_row())

    def fetchone(self) -> ta.Any:
        self._check_executed()
        row = self.read_next()
        if row is None:
            self.warning_count = self._result.warning_count
            return None
        self.rownumber += 1
        return row

    def fetchall(self) -> ta.Sequence[ta.Any]:
        return list(self.fetchall_unbuffered())

    def fetchall_unbuffered(self) -> ta.Iterator[ta.Any]:
        return iter(self.fetchone, None)

    def fetchmany(self, size: int | None = None) -> ta.Sequence[ta.Any]:
        self._check_executed()
        rows = []
        for _ in range(self.arraysize if size is None else size):
            row = self.read_next()
            if row is None:
                self.warning_count = self._result.warning_count
                break
            rows.append(row)
            self.rownumber += 1
        return rows or ()

    def scroll(self, value: int, mode: str = 'relative') -> None:
        self._check_executed()
        if mode == 'relative':
            if value < 0:
                raise NotSupportedError('Backwards scrolling not supported by this cursor')
            steps = value
        elif mode == 'absolute':
            if value < self.rownumber:
                raise NotSupportedError('Backwards scrolling not supported by this cursor')
            steps = value - self.rownumber
        else:
            raise ProgrammingError(f'unknown scroll mode {mode}')
        for _ in range(steps):
            self.read_next()
        self.rownumber += steps


class SSDictCursor(DictCursorMixin, SSCursor):
    """An unbuffered cursor whose rows are dicts keyed by column name."""
