import collections
import typing as ta

from ..converters import make_params
from ..core.asyncio import AsyncioCoreConnection
from ..protocol.session import Context
from ..protocol.session import CopyStream
from .statements import plan_run
from .statements import to_statement


##


class AsyncioConnection(AsyncioCoreConnection):
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

    async def run(
            self,
            sql: str,
            stream: CopyStream | None = None,
            types: ta.Mapping[str, int] | None = None,
            **params: ta.Any,
    ) -> list[list[ta.Any]] | None:
        if len(params) == 0 and stream is None:
            self._context = await self.execute_simple(sql)
        else:
            statement, vals, oids = plan_run(sql, params, types)
            self._context = await self.execute_unnamed(statement, vals, oids=oids, stream=stream)
        return self._context.rows

    async def prepare(self, sql: str, types: ta.Mapping[str, int] | None = None) -> AsyncPreparedStatement:
        statement, make_vals = to_statement(sql)
        oids = () if types is None else make_vals(collections.defaultdict(lambda: None, types))
        info = await self.prepare_statement(statement, oids)
        return AsyncPreparedStatement(self, statement, make_vals, info.name, info.columns, info.input_funcs)


class AsyncPreparedStatement:
    """Created via `AsyncConnection.prepare`, as preparing requires awaiting."""

    def __init__(
            self,
            con: AsyncioCoreConnection,
            statement: str,
            make_vals: ta.Callable[[ta.Mapping[str, ta.Any]], tuple[ta.Any, ...]],
            name: str,
            cols: ta.Sequence[ta.Mapping[str, ta.Any]] | None,
            input_funcs: ta.Sequence[ta.Any],
    ) -> None:
        super().__init__()

        self.con = con
        self.statement = statement
        self.make_vals = make_vals
        self.name = name
        self.cols = cols
        self.input_funcs = input_funcs
        self._context: Context | None = None

    @property
    def columns(self) -> ta.Sequence[ta.Mapping[str, ta.Any]] | None:
        context = self._context
        if context is None:
            return None
        return context.columns

    async def run(self, **params: ta.Any) -> list[list[ta.Any]] | None:
        self._context = await self.con.execute_named(
            self.name,
            make_params(self.con.py_types, self.make_vals(params)),
            self.cols,
            self.input_funcs,
            self.statement,
        )
        return self._context.rows

    async def close(self) -> None:
        await self.con.close_prepared_statement(self.name)
