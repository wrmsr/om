import io
import typing as ta

from .... import check
from ...dtypes import Boolean
from ...dtypes import Bytes
from ...dtypes import Datetime
from ...dtypes import Float
from ...dtypes import Integer
from ...dtypes import String
from ...dtypes import Uuid
from ...qualifiedname import QualifiedName
from ...tabledefs.elements import Column
from ...tabledefs.elements import Index
from ...tabledefs.elements import PrimaryKey
from ...tabledefs.elements import UpdatedAtTrigger
from ...tabledefs.elements import index_name
from ...tabledefs.rendering import Renderer
from ...tabledefs.tabledefs import TableDef
from ...tabledefs.triggers import TriggerRenderer
from ...tabledefs.values import Now
from ...tabledefs.values import SimpleValue


##


# Sqlite's current_timestamp stops at the second. This is as fine as its builtins go - they keep time in milliseconds -
# in the same text form, so the two sort together, as they do with the microseconds a client may write.
SQLITE_NOW_SQL = "strftime('%Y-%m-%d %H:%M:%f', 'now')"


CREATE_UPDATED_AT_TRIGGER_SRC = """\
create trigger {if_not_exists}{trigger_name}
after update on {table_name}
for each row
when new.{column_name} = old.{column_name}
begin
  update {table_name}
  set {column_name} = {now}
  where {where};
end\
"""


class SqliteUpdatedAtTriggerRenderer(TriggerRenderer[UpdatedAtTrigger]):
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
        if (pk := tbl.elements.get(PrimaryKey)) is not None:
            pk_cols = check.not_empty(pk.columns)
        else:
            pk_cols = ['rowid']

        # Sqlite scopes a trigger to its table's database: the trigger's own name may be qualified but the table it is
        # on, and any table its body touches, must not be.
        return [CREATE_UPDATED_AT_TRIGGER_SRC.format(
            if_not_exists='if not exists ' if opts.if_not_exists else '',
            trigger_name=r.qname(tbl.name.sibling(t.trigger_name(tbl.name))),
            table_name=r.quote_ident(tbl.name.last),
            column_name=r.quote_ident(t.column),
            now=SQLITE_NOW_SQL,
            where=' and '.join(f'{r.quote_ident(c)} = new.{r.quote_ident(c)}' for c in pk_cols),
        )]

    def drop_statements(
            self,
            r: Renderer,
            table_name: QualifiedName,
            name: str,
    ) -> list[str]:
        return [f'drop trigger if exists {r.qname(table_name.sibling(name))}']


##


class SqliteTabledefRenderer(Renderer):
    def builtin_trigger_renderers(self) -> ta.Sequence[TriggerRenderer]:
        return [SqliteUpdatedAtTriggerRenderer()]

    def column_type(self, c: Column, *, is_identity: bool, indexed: bool = False) -> str:
        # Type names matter only for sqlite's affinity rules: anything containing 'char' or 'text' is TEXT, 'int' is
        # INTEGER, and an unrecognized name ('string', say) falls through to NUMERIC - which would silently turn a
        # numeric-looking string into a number.
        if isinstance(c.type, String):
            return f'varchar({c.type.length})' if c.type.length is not None else 'text'
        elif isinstance(c.type, Uuid):
            return 'text'
        elif isinstance(c.type, Integer):
            return 'integer'  # every sqlite integer is 64-bit; the declared width is immaterial
        elif isinstance(c.type, Datetime):
            return 'datetime'
        elif isinstance(c.type, Boolean):
            return 'boolean'
        elif isinstance(c.type, Float):
            return 'real'
        elif isinstance(c.type, Bytes):
            return 'blob'
        else:
            raise TypeError(c.type)

    def render_default(self, v: SimpleValue) -> str:
        if isinstance(v, Now):
            return f'({SQLITE_NOW_SQL})'  # a default which is an expression, not a keyword or a literal, goes in parens
        return super().render_default(v)

    def table_suffixes(self, tbl: TableDef, identity_column: str | None) -> list[str]:
        # A single integer-pk column is sqlite's implicit rowid; otherwise the table is WITHOUT ROWID.
        return [] if identity_column is not None else ['without rowid']

    def index_statement(self, table_name: QualifiedName, e: Index, opts: Renderer.CreateOptions) -> str:
        # As with triggers: the index name carries the qualification, the table it is on must be bare.
        idx_name = index_name(table_name, e)

        with e.options.consume():
            pass

        out = io.StringIO()
        out.write('create ')
        if e.unique:
            out.write('unique ')
        out.write('index ')
        if opts.if_not_exists:
            out.write('if not exists ')
        out.write(f'{self.qname(table_name.sibling(idx_name))} on {self.quote_ident(table_name.last)} ')
        out.write(f'({", ".join(self.quote_ident(c) for c in e.columns)})')
        if e.where is not None:
            out.write(f' where {self.render_predicate(e.where)}')
        out.write('\n')
        return out.getvalue()
