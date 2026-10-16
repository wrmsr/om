import contextlib
import typing as ta

from ...api import querierfuncs as qf
from ...api.dbapi import DbapiAdapter
from ...api.dbapi import DbapiConn
from ...params import ParamStyle
from .dialect import SqliteDialect


##


class SqliteDbapiAdapter(DbapiAdapter):
    @contextlib.contextmanager
    def transaction_context(self, conn: DbapiConn, *, readonly: bool) -> ta.Iterator[None]:
        if not readonly:
            yield
            return

        was_query_only = bool(qf.query_scalar(conn, 'pragma query_only'))
        if not was_query_only:
            qf.exec(conn, 'pragma query_only = 1')
        try:
            yield
        finally:
            if not was_query_only:
                qf.exec(conn, 'pragma query_only = 0')


def sqlite_adapter(
        *,
        param_style: ParamStyle = ParamStyle.QMARK,
        immediate: bool = False,
) -> SqliteDbapiAdapter:
    return SqliteDbapiAdapter(
        param_style=param_style,
        dialect=SqliteDialect(immediate=immediate),
    )
