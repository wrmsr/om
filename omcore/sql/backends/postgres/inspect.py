# ruff: noqa: S608
from .... import check
from ...api.querierfuncs import query_all
from ...api.queriers import AsyncQuerier
from ...dtypes import DATETIME
from ...dtypes import JSON
from ...dtypes import STRING
from ...dtypes import UUID
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


class PostgresInspector(Inspector):
    """
    Barebones reflection. Fail-open: it models columns, the primary key, explicitly-created (non-primary) indexes, and
    the names of non-internal triggers; anything more exotic is deliberately ignored rather than fatal. Names are
    interpolated as escaped string literals rather than bound as parameters, since placeholders are driver-specific;
    they come from code, not user input, and this is reflection-only. A bare table name is resolved against the
    session's current schema, exactly where unqualified ddl would have created it.
    """

    def _schema_expr(self, name: QualifiedName) -> str:
        if len(name) == 1:
            return 'current_schema()'
        elif len(name) == 2:
            return _lit(name[0])
        else:
            raise ValueError(name)

    async def reflect_table(self, querier: AsyncQuerier, name: CanQualifiedName) -> ReflectedTable | None:
        name = QualifiedName.of(name)
        schema = self._schema_expr(name)
        table = _lit(name.last)

        cols_rows = await query_all(querier, (
            'select column_name, data_type, is_nullable, character_maximum_length '
            'from information_schema.columns '
            f'where table_schema = {schema} and table_name = {table} '
            'order by ordinal_position'
        ))
        if not cols_rows:
            return None

        pk_cols = [
            r.to_dict()['column_name']
            for r in await query_all(querier, (
                'select kcu.column_name '
                'from information_schema.table_constraints tc '
                'join information_schema.key_column_usage kcu '
                'on kcu.constraint_schema = tc.constraint_schema and kcu.constraint_name = tc.constraint_name '
                f'where tc.table_schema = {schema} and tc.table_name = {table} '
                "and tc.constraint_type = 'PRIMARY KEY' "
                'order by kcu.ordinal_position'
            ))
        ]

        cols: list[ReflectedColumn] = []
        for r in cols_rows:
            d = r.to_dict()
            cols.append(ReflectedColumn(
                d['column_name'],
                d['data_type'],
                nullable=d['is_nullable'] == 'YES',
                length=d['character_maximum_length'],
            ))

        idx_cols: dict[str, list[str]] = {}
        idx_unique: dict[str, bool] = {}
        for r in await query_all(querier, (
            'select i.relname as index_name, ix.indisunique as is_unique, a.attname as column_name '
            'from pg_class t '
            'join pg_namespace n on n.oid = t.relnamespace '
            'join pg_index ix on ix.indrelid = t.oid '
            'join pg_class i on i.oid = ix.indexrelid '
            'join lateral unnest(ix.indkey) with ordinality as k(attnum, ord) on true '
            'join pg_attribute a on a.attrelid = t.oid and a.attnum = k.attnum '
            f"where n.nspname = {schema} and t.relname = {table} and t.relkind = 'r' and not ix.indisprimary "
            'order by i.relname, k.ord'
        )):
            d = r.to_dict()
            iname = d['index_name']
            idx_cols.setdefault(iname, []).append(d['column_name'])
            idx_unique[iname] = bool(d['is_unique'])

        idxs = [ReflectedIndex(nm, cs, unique=idx_unique[nm]) for nm, cs in idx_cols.items()]

        trgs = [
            ReflectedTrigger(check.non_empty_str(r.to_dict()['trigger_name']))
            for r in await query_all(querier, (
                'select t.tgname as trigger_name '
                'from pg_trigger t '
                'join pg_class c on c.oid = t.tgrelid '
                'join pg_namespace n on n.oid = c.relnamespace '
                f'where n.nspname = {schema} and c.relname = {table} and not t.tgisinternal '
                'order by t.tgname'
            ))
        ]

        return ReflectedTable(name, cols, primary_key=pk_cols, indexes=idxs, triggers=trgs)

    def lift_table(self, reflected: ReflectedTable) -> TableDef:
        return lift_reflected_table(reflected, self.lift_dtype)

    def lift_dtype(self, rc: ReflectedColumn) -> Dtype:
        tl = rc.type.strip().lower()
        if tl in ('smallint', 'int2'):
            return Integer(bits=16)
        elif tl in ('integer', 'int', 'int4'):
            return Integer(bits=32)
        elif tl in ('bigint', 'int8'):
            return Integer(bits=64)
        elif 'timestamp' in tl or tl == 'date':
            return DATETIME
        elif tl == 'uuid':
            return UUID
        elif tl in ('jsonb', 'json'):
            return JSON
        elif tl in ('character varying', 'character') and rc.length is not None:
            return String(length=rc.length)
        else:
            # fail-open: text/varchar/char/etc land as String for now.
            return STRING
