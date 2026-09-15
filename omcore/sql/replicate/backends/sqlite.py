from .... import lang
from ...backends.sqlite.inspect import SqliteInspector
from ...backends.sqlite.tabledefs import SqliteTabledefRenderer
from ...backends.sqlite.values import SqliteDtypeCodec
from ...dtypes.codecs import DtypeCodec
from ...inspect.inspectors import Inspector
from ...qualifiedname import QualifiedName
from ...tabledefs.rendering import Renderer
from ...tabledefs.tabledefs import TableDef
from ...tabledefs.triggers import TriggerRenderer
from ..config import table_key_column
from ..names import node_table_name
from ..names import shadow_name
from ..shadows import NODE_ID
from ..shadows import SHADOW_CHANGED_AT
from ..shadows import SHADOW_DELETED
from ..shadows import SHADOW_KEY
from ..shadows import SHADOW_ORIGIN
from ..shadows import SHADOW_VERSION
from ..triggers import CaptureEvent
from ..triggers import CaptureTrigger
from .base import OnConflictReplicateBackend


##


# Sqlite scopes a trigger to its table's database: the trigger's own name may be qualified but the tables it touches
# must be bare. And a trigger fired by an upsert inherits the outer statement's conflict policy, which would turn an
# 'insert or ignore' into an abort, so the shadow row is created by a conditional select instead.
CAPTURE_TRIGGER_SRC = """\
create trigger {if_not_exists}{trigger_name}
after {event} on {table_name}
for each row
begin
  insert into {shadow} ({shadow_columns})
  select {row}.{key}, 0, (select {node_id} from {node_table}), 0, current_timestamp
  where not exists (select 1 from {shadow} where {shadow_key} = {row}.{key});

  update {shadow}
  set {shadow_version} = {shadow_version} + 1,
      {shadow_origin} = (select {node_id} from {node_table}),
      {shadow_deleted} = {deleted},
      {shadow_changed_at} = current_timestamp
  where {shadow_key} = {row}.{key};
end\
"""


class SqliteCaptureTriggerRenderer(TriggerRenderer[CaptureTrigger]):
    @property
    def trigger_cls(self) -> type[CaptureTrigger]:
        return CaptureTrigger

    def create_statements(
            self,
            r: Renderer,
            tbl: TableDef,
            t: CaptureTrigger,
            opts: Renderer.CreateOptions,
    ) -> list[str]:
        trigger_name = t.trigger_name(tbl.name)
        shadow = shadow_name(tbl.name)
        node_table = node_table_name(tbl.name.parts[:-1])

        return [
            CAPTURE_TRIGGER_SRC.format(
                if_not_exists='if not exists ' if opts.if_not_exists else '',
                trigger_name=r.qname(tbl.name.sibling(trigger_name)),
                event=t.event.value,
                table_name=r.quote_ident(tbl.name.last),
                shadow=r.quote_ident(shadow.last),
                shadow_columns=', '.join(
                    r.quote_ident(c)
                    for c in (
                        SHADOW_KEY,
                        SHADOW_VERSION,
                        SHADOW_ORIGIN,
                        SHADOW_DELETED,
                        SHADOW_CHANGED_AT,
                    )
                ),
                shadow_key=r.quote_ident(SHADOW_KEY),
                shadow_version=r.quote_ident(SHADOW_VERSION),
                shadow_origin=r.quote_ident(SHADOW_ORIGIN),
                shadow_deleted=r.quote_ident(SHADOW_DELETED),
                shadow_changed_at=r.quote_ident(SHADOW_CHANGED_AT),
                row='old' if t.event is CaptureEvent.DELETE else 'new',
                key=r.quote_ident(table_key_column(tbl).name),
                node_id=r.quote_ident(NODE_ID),
                node_table=r.quote_ident(node_table.last),
                deleted='1' if t.event is CaptureEvent.DELETE else '0',
            ),
        ]

    def drop_statements(
            self,
            r: Renderer,
            table_name: QualifiedName,
            name: str,
    ) -> list[str]:
        return [f'drop trigger if exists {r.qname(table_name.sibling(name))}']


##


class SqliteReplicateBackend(OnConflictReplicateBackend, lang.Final):
    @property
    def tabledef_renderer(self) -> Renderer:
        return SqliteTabledefRenderer(trigger_renderers=[SqliteCaptureTriggerRenderer()])

    @property
    def inspector(self) -> Inspector:
        return SqliteInspector()

    @property
    def dtype_codec(self) -> DtypeCodec:
        return SqliteDtypeCodec()
