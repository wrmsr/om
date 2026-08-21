# ruff: noqa: S608
"""
Describes a DB-API 2.0 driver to the compliance suite: how to get a connection, and the few dialect-specific bits the
suite needs. Everything else is derived from the module itself, as the spec intends.
"""
import contextlib
import types
import typing as ta

from ..... import check
from ..... import dataclasses as dc


##


@dc.dataclass(frozen=True, kw_only=True)
class DbapiComplianceBinding:
    module: types.ModuleType

    # Returns a fresh, open connection each call, connected to a database the suite may create and drop tables in.
    connect: ta.Callable[[], ta.Any]

    # Prepended to every table the suite creates.
    table_prefix: str = 'dbapi_compliance_'

    # Dialect type names for the columns the suite round-trips values through.
    varchar_type: str = 'varchar(100)'
    integer_type: str = 'integer'
    numeric_type: str = 'numeric(12, 3)'
    float_type: str = 'double precision'
    binary_type: str = 'bytea'
    date_type: str = 'date'
    time_type: str = 'time'
    timestamp_type: str = 'timestamp'

    # A one-argument SQL function usable as `select <lower_func>(<param>)`.
    lower_func: str = 'lower'

    # A stored procedure, taking no arguments, that `cursor.callproc` can invoke - or None to skip callproc tests.
    callproc_name: str | None = None

    #

    @property
    def paramstyle(self) -> str:
        return check.in_(self.module.paramstyle, ('qmark', 'numeric', 'named', 'format', 'pyformat'))

    def placeholder(self, idx: int, name: str) -> str:
        """The placeholder for the idx'th (zero-based) parameter, named `name` where the style needs a name."""

        ps = self.paramstyle
        if ps == 'qmark':
            return '?'
        elif ps == 'numeric':
            return f':{idx + 1}'
        elif ps == 'named':
            return f':{name}'
        elif ps == 'format':
            return '%s'
        elif ps == 'pyformat':
            return f'%({name})s'
        else:
            raise ValueError(ps)

    def placeholders(self, names: ta.Sequence[str]) -> list[str]:
        return [self.placeholder(i, n) for i, n in enumerate(names)]

    def params(self, names: ta.Sequence[str], values: ta.Sequence[ta.Any]) -> ta.Any:
        """The parameters object to pass to execute for the given names and values, shaped for the paramstyle."""

        check.equal(len(names), len(values))
        if self.paramstyle in ('named', 'pyformat'):
            return dict(zip(names, values, strict=True))
        return tuple(values)

    def escape_percent(self, sql: str) -> str:
        """Escapes literal percent signs in SQL which will be passed to execute together with parameters."""

        if self.paramstyle in ('format', 'pyformat'):
            return sql.replace('%', '%%')
        return sql

    #

    def table_name(self, name: str) -> str:
        return self.table_prefix + name

    @contextlib.contextmanager
    def closing(self, obj: ta.Any) -> ta.Iterator[ta.Any]:
        try:
            yield obj
        finally:
            try:
                obj.close()
            except self.module.Error:  # noqa: S110
                pass

    @contextlib.contextmanager
    def table(self, con: ta.Any, name: str, columns: str) -> ta.Iterator[str]:
        """Creates (replacing any leftover) and on exit drops a table, committing around both."""

        full_name = self.table_name(name)
        cur = con.cursor()
        cur.execute(f'drop table if exists {full_name}')
        cur.execute(f'create table {full_name} {columns}')
        con.commit()
        try:
            yield full_name
        finally:
            try:
                con.rollback()
                cur = con.cursor()
                cur.execute(f'drop table if exists {full_name}')
                con.commit()
            except self.module.Error:  # noqa: S110
                pass
