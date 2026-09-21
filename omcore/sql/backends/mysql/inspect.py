# ruff: noqa: S608
from .... import check
from ...api.querierfuncs import query_all
from ...api.queriers import AsyncQuerier
from ...dtypes import DATETIME
from ...dtypes import INTEGER
from ...dtypes import STRING
from ...dtypes import Dtype
from ...dtypes import Integer
from ...dtypes import String
from ...inspect.inspectors import Inspector
from ...inspect.lifting import lift_reflected_table
from ...inspect.reflected import ReflectedColumn
from ...inspect.reflected import ReflectedIndex
from ...inspect.reflected import ReflectedTable
from ...inspect.reflected import ReflectedTrigger
from ...qualifiedname import CanQualifiedName
from ...qualifiedname import QualifiedName
from ...tabledefs.tabledefs import TableDef


##


def _lit(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


class MysqlInspector(Inspector):
    """
    Barebones information_schema reflection. Fail-open: it models columns, the primary key, explicitly-created
    (non-PRIMARY) indexes, and trigger names, ignoring the rest. A qualified table name names its database; a bare one
    is resolved against the connection's current database. Names are interpolated as escaped string literals - they
    are code-defined, and this is reflection-only.
    """

    def _schema_expr(self, name: QualifiedName) -> str:
        if len(name) == 1:
            return 'database()'
        elif len(name) == 2:
            return _lit(name[0])
        else:
            raise ValueError(name)

    async def reflect_table(self, querier: AsyncQuerier, name: CanQualifiedName) -> ReflectedTable | None:
        name = QualifiedName.of(name)
        schema = self._schema_expr(name)
        table = _lit(name.last)

        rows = await query_all(querier, (
            'select column_name as name, data_type as type, is_nullable as nullable, '
            'character_maximum_length as length '
            'from information_schema.columns '
            f'where table_schema = {schema} and table_name = {table} '
            'order by ordinal_position'
        ))
        if not rows:
            return None

        cols: list[ReflectedColumn] = []
        for r in rows:
            d = r.to_dict()
            cols.append(ReflectedColumn(
                d['name'],
                d['type'],
                nullable=d['nullable'] == 'YES',
                length=int(d['length']) if d['length'] is not None else None,
            ))

        # The primary key is an index like the rest here, under a name of its own.
        idx_cols: dict[str, list[str]] = {}
        idx_unique: dict[str, bool] = {}
        for r in await query_all(querier, (
            'select index_name as iname, column_name as cname, non_unique as nonuniq '
            'from information_schema.statistics '
            f'where table_schema = {schema} and table_name = {table} '
            'order by index_name, seq_in_index'
        )):
            d = r.to_dict()
            iname = d['iname']
            idx_cols.setdefault(iname, []).append(d['cname'])
            idx_unique[iname] = not bool(int(d['nonuniq']))

        pk_cols = idx_cols.pop('PRIMARY', [])
        idxs = [ReflectedIndex(nm, cs, unique=idx_unique[nm]) for nm, cs in idx_cols.items()]

        trgs = [
            ReflectedTrigger(check.non_empty_str(r.to_dict()['tname']))
            for r in await query_all(querier, (
                'select trigger_name as tname '
                'from information_schema.triggers '
                f'where trigger_schema = {schema} and event_object_table = {table} '
                'order by trigger_name'
            ))
        ]

        return ReflectedTable(name, cols, primary_key=pk_cols, indexes=idxs, triggers=trgs)

    def lift_table(self, reflected: ReflectedTable) -> TableDef:
        return lift_reflected_table(reflected, self.lift_dtype)

    def lift_dtype(self, rc: ReflectedColumn) -> Dtype:
        tl = rc.type.strip().lower()
        if tl == 'smallint':
            return Integer(bits=16)
        elif tl in ('int', 'integer', 'mediumint'):
            return Integer(bits=32)
        elif tl == 'bigint':
            return Integer(bits=64)
        elif 'int' in tl:
            return INTEGER  # tinyint is also how a Boolean lands; leave it unspecified rather than guess
        elif tl in ('datetime', 'timestamp', 'date'):
            return DATETIME
        elif tl in ('varchar', 'char') and rc.length is not None:
            return String(length=rc.length)
        else:
            # fail-open: text/varchar/char/etc land as String for now.
            return STRING
