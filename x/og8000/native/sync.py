import collections
import typing as ta

from ..converters import make_params
from ..core.sync import SyncCoreConnection
from ..protocol.session import Context
from ..protocol.session import CopyStream
from .statements import plan_run
from .statements import to_statement


##


class Connection(SyncCoreConnection):
    def __init__(self, *args: ta.Any, **kwargs: ta.Any) -> None:
        super().__init__(*args, **kwargs)
        self._context: Context | None = None

    @property
    def columns(self) -> ta.Sequence[ta.Mapping[str, ta.Any]] | None:
        context = self._context
        if context is None:
            return None
        return context.columns

    @property
    def row_count(self) -> int | None:
        context = self._context
        if context is None:
            return None
        return context.row_count

    def run(
            self,
            sql: str,
            stream: CopyStream | None = None,
            types: ta.Mapping[str, int] | None = None,
            **params: ta.Any,
    ) -> list[list[ta.Any]] | None:
        if len(params) == 0 and stream is None:
            self._context = self.execute_simple(sql)
        else:
            statement, vals, oids = plan_run(sql, params, types)
            self._context = self.execute_unnamed(statement, vals, oids=oids, stream=stream)
        return self._context.rows

    def prepare(self, sql: str) -> PreparedStatement:
        return PreparedStatement(self, sql)


class PreparedStatement:
    def __init__(self, con: SyncCoreConnection, sql: str, types: ta.Mapping[str, int] | None = None) -> None:
        super().__init__()

        self.con = con
        self.statement, self.make_vals = to_statement(sql)
        oids = () if types is None else self.make_vals(collections.defaultdict(lambda: None, types))
        self.name, self.cols, self.input_funcs = con.prepare_statement(self.statement, oids)
        self._context: Context | None = None

    @property
    def columns(self) -> ta.Sequence[ta.Mapping[str, ta.Any]] | None:
        context = self._context
        if context is None:
            return None
        return context.columns

    def run(self, **params: ta.Any) -> list[list[ta.Any]] | None:
        self._context = self.con.execute_named(
            self.name,
            make_params(self.con.py_types, self.make_vals(params)),
            self.cols,
            self.input_funcs,
            self.statement,
        )
        return self._context.rows

    def close(self) -> None:
        self.con.close_prepared_statement(self.name)
