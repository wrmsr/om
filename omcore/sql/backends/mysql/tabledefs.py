import typing as ta

from ...dtypes import Boolean
from ...dtypes import Bytes
from ...dtypes import Datetime
from ...dtypes import Float
from ...dtypes import Integer
from ...dtypes import String
from ...dtypes import Uuid
from ...qualifiedname import QualifiedName
from ...syntax import QuoteStyles
from ...tabledefs.diffing import AlterColumn
from ...tabledefs.elements import Column
from ...tabledefs.elements import UpdatedAtTrigger
from ...tabledefs.lower import cluster_on_primary_key
from ...tabledefs.rendering import RenderColumn
from ...tabledefs.rendering import Renderer
from ...tabledefs.tabledefs import TableDef
from ...tabledefs.triggers import TriggerRenderer
from ...tabledefs.values import Now
from ...tabledefs.values import SimpleValue


##


# As the one statement a trigger can be without a compound body, which would need a delimiter of its own to get past a
# client. Mysql's greatest makes nothing of the whole if any of it is nothing, hence the coalesce.
CREATE_UPDATED_AT_TRIGGER_SRC = """\
create trigger {trigger_name}
before update on {table_name}
for each row
set new.{column_name} = if(
  new.{column_name} <=> old.{column_name},
  greatest(current_timestamp(6), coalesce(old.{column_name} + interval 1 microsecond, current_timestamp(6))),
  new.{column_name}
)\
"""


class MysqlUpdatedAtTriggerRenderer(TriggerRenderer[UpdatedAtTrigger]):
    @property
    def trigger_cls(self) -> type[UpdatedAtTrigger]:
        return UpdatedAtTrigger

    def create_statements(
            self,
            r: Renderer,
            tbl: TableDef,
            t: UpdatedAtTrigger,
            opts: Renderer.CreateOptions,
    ) -> list[str]:
        trigger_qn = tbl.name.sibling(t.trigger_name(tbl.name))

        stmts: list[str] = []
        if opts.if_not_exists:
            # Mysql has neither 'if not exists' nor 'or replace' for triggers.
            stmts.append(f'drop trigger if exists {r.qname(trigger_qn)}')
        stmts.append(CREATE_UPDATED_AT_TRIGGER_SRC.format(
            trigger_name=r.qname(trigger_qn),
            table_name=r.qname(tbl.name),
            column_name=r.quote_ident(t.column),
        ))
        return stmts

    def drop_statements(
            self,
            r: Renderer,
            table_name: QualifiedName,
            name: str,
    ) -> list[str]:
        return [f'drop trigger if exists {r.qname(table_name.sibling(name))}']


##


MYSQL_INTEGER_TYPES_BY_BITS: ta.Mapping[int, str] = {
    16: 'smallint',
    32: 'integer',
    64: 'bigint',
}

# Mysql cannot index a TEXT column without a key length, so an indexed string of unbounded length is given this one.
MYSQL_DEFAULT_INDEXED_STRING_LENGTH = 255


class MysqlTabledefRenderer(Renderer):
    ident_quote_style = QuoteStyles.BACKTICK
    max_ident_length = 64

    def builtin_trigger_renderers(self) -> ta.Sequence[TriggerRenderer]:
        return [MysqlUpdatedAtTriggerRenderer()]

    def column_type(self, c: Column, *, is_identity: bool, indexed: bool = False) -> str:
        if isinstance(c.type, String):
            if c.type.length is not None:
                return f'varchar({c.type.length})'
            elif indexed:
                return f'varchar({MYSQL_DEFAULT_INDEXED_STRING_LENGTH})'
            else:
                return 'text'
        elif isinstance(c.type, Uuid):
            return 'char(36)'
        elif isinstance(c.type, Integer):
            return MYSQL_INTEGER_TYPES_BY_BITS[self.integer_bits(c.type, is_identity=is_identity)]
        elif isinstance(c.type, Datetime):
            return 'datetime(6)'  # a plain datetime silently drops fractional seconds
        elif isinstance(c.type, Boolean):
            return 'tinyint(1)'
        elif isinstance(c.type, Float):
            return 'double'
        elif isinstance(c.type, Bytes):
            return 'blob'
        else:
            raise TypeError(c.type)

    def column_identity_sql(self, c: Column) -> str:
        return 'auto_increment'

    def render_default(self, v: SimpleValue) -> str:
        if isinstance(v, Now):
            return 'current_timestamp(6)'  # a default's precision must match the datetime(6) column's
        return super().render_default(v)

    def _render_column(self, rc: RenderColumn) -> str:
        # MySQL wants AUTO_INCREMENT *after* NOT NULL / DEFAULT, unlike postgres' identity clause - so the column-clause
        # ordering is genuinely dialect-specific. (A cleaner base would expose the ordering as a hook; for now mysql
        # overrides the whole thing.)
        parts = [f'{self.quote_ident(rc.name)} {rc.type}']
        if rc.not_null:
            parts.append('not null')
        if rc.default is not None:
            parts.append(f'default {rc.default}')
        if rc.identity:
            parts.append(rc.identity)
        parts.extend(rc.extra)
        return ' '.join(parts)

    def physical_table(self, tbl: TableDef) -> TableDef:
        # An innodb table is its primary key's index, and there is no other way to say what order it is in.
        return cluster_on_primary_key(tbl)

    def drop_index_statement(self, table_name: QualifiedName, name: str) -> str:
        # Mysql scopes index names to their table rather than their schema.
        return f'drop index {self.quote_ident(name)} on {self.qname(table_name)}'

    def alter_column_statements(self, op: AlterColumn) -> list[str]:
        rc = self._render_column(self._build_render_column(op.column, is_identity=False))
        return [f'alter table {self.qname(op.table)} modify column {rc}']
