# ruff: noqa: S608
import re

from .... import check
from ...api.querierfuncs import query_all
from ...api.queriers import AsyncQuerier
from ...dtypes import DATETIME
from ...dtypes import INTEGER
from ...dtypes import STRING
from ...dtypes import Dtype
from ...dtypes import String
from ...inspect.inspectors import Inspector
from ...inspect.lifting import lift_reflected_table
from ...inspect.reflected import ReflectedColumn
from ...inspect.reflected import ReflectedIndex
from ...inspect.reflected import ReflectedTable
from ...inspect.reflected import ReflectedTrigger
from ...qualifiedname import CanQualifiedName
from ...qualifiedname import as_qualified_name
from ...syntax import QuoteStyles
from ...tabledefs.tabledefs import TableDef


##


def _lit(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _quote(s: str) -> str:
    return QuoteStyles.DOUBLE.quote(s)


_BOUNDED_CHAR_TYPE_PAT = re.compile(r'^(?:var)?char(?:acter)?(?:\s+varying)?\s*\(\s*(\d+)\s*\)$')


class SqliteInspector(Inspector):
    """
    Pragma-based reflection. A qualified table name names its database ('main', 'temp', or an attached alias); a bare
    one is resolved the way sqlite resolves any bare name.
    """

    async def reflect_table(self, querier: AsyncQuerier, name: CanQualifiedName) -> ReflectedTable | None:
        name = as_qualified_name(name)
        if len(name) > 2:
            raise ValueError(name)
        db_prefix = f'{_quote(name[0])}.' if len(name) == 2 else ''
        table = _quote(name.last)

        info = await query_all(querier, f'pragma {db_prefix}table_info({table})')
        if not info:
            return None

        cols: list[ReflectedColumn] = []
        for row in info:
            d = row.to_dict()
            m = _BOUNDED_CHAR_TYPE_PAT.match(d['type'].strip().lower())
            cols.append(ReflectedColumn(
                d['name'],
                d['type'],
                nullable=not d['notnull'],
                primary_key=bool(d['pk']),
                length=int(m.group(1)) if m is not None else None,
            ))

        idxs: list[ReflectedIndex] = []
        for irow in await query_all(querier, f'pragma {db_prefix}index_list({table})'):
            idd = irow.to_dict()
            if idd.get('origin') != 'c':
                continue  # only explicit CREATE INDEXes are modeled; skip pk- and unique-constraint-backed indexes
            iname = idd['name']
            icols = [
                r.to_dict()['name']
                for r in await query_all(querier, f'pragma {db_prefix}index_info({_quote(iname)})')
            ]
            idxs.append(ReflectedIndex(iname, icols, unique=bool(idd['unique'])))

        trgs = [
            ReflectedTrigger(check.non_empty_str(r.to_dict()['name']))
            for r in await query_all(querier, (
                f'select name from {db_prefix}sqlite_master '
                f"where type = 'trigger' and tbl_name = {_lit(name.last)} "
                'order by name'
            ))
        ]

        return ReflectedTable(name, cols, indexes=idxs, triggers=trgs)

    def lift_table(self, reflected: ReflectedTable) -> TableDef:
        return lift_reflected_table(reflected, self.lift_dtype)

    def lift_dtype(self, rc: ReflectedColumn) -> Dtype:
        tl = rc.type.strip().lower()
        if 'int' in tl:
            return INTEGER  # every sqlite integer is 64-bit, so no declared width is a lie; leave it unspecified
        elif tl in ('datetime', 'timestamp'):
            return DATETIME
        elif rc.length is not None:
            return String(length=rc.length)
        else:
            # fail-open: text/string/varchar/blob/anything-else lands as String for now.
            return STRING
