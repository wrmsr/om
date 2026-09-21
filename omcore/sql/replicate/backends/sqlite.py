from .... import lang
from ...backends.sqlite.inspect import SqliteInspector
from ...backends.sqlite.tabledefs import SqliteTabledefRenderer
from ...backends.sqlite.values import SqliteDtypeCodec
from ...dtypes.codecs import DtypeCodec
from ...inspect.inspectors import Inspector
from ...qualifiedname import QualifiedName
from ...tabledefs.elements import Column
from ...tabledefs.elements import Trigger
from ...tabledefs.elements import UpdatedAtTrigger
from ...tabledefs.rendering import Renderer
from ...tabledefs.tabledefs import TableDef
from ...tabledefs.triggers import TriggerRenderer
from ..config import table_key_column
from ..names import log_table_name
from ..names import node_table_name
from ..names import shadow_name
from ..shadows import LOG_CHANGED_AT
from ..shadows import LOG_KEY
from ..shadows import LOG_TABLE
from ..shadows import LOG_VERSION
from ..shadows import NODE_ID
from ..shadows import SHADOW_CHANGED_AT
from ..shadows import SHADOW_DELETED
from ..shadows import SHADOW_KEY
from ..shadows import SHADOW_ORIGIN
from ..shadows import SHADOW_VERSION
from ..triggers import CaptureEvent
from ..triggers import CaptureTrigger
from .base import OnConflictReplicateBackend
from .base import sql_string_literal


##


# Sqlite scopes a trigger to its table's database: the trigger's own name may be qualified but the tables it touches
# must be bare. And a trigger fired by an upsert inherits the outer statement's conflict policy, which would turn an
# 'insert or ignore' into an abort, so the shadow row is created by a conditional select instead.
CAPTURE_TRIGGER_SRC = """\
create trigger {if_not_exists}{trigger_name}
after {event}{of_columns} on {table_name}
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
{log_statement}end\
"""


CAPTURE_LOG_SRC = """\

  insert into {log} ({log_columns})
  values ({table_literal}, {row}.{key}, (select {shadow_version} from {shadow} where {shadow_key} = {row}.{key}), current_timestamp);
"""  # noqa


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
        row = 'old' if t.event is CaptureEvent.DELETE else 'new'
        key = r.quote_ident(table_key_column(tbl).name)

        # Sqlite has no way for a trigger to alter a row on its way in, so its updated-at trigger follows an update
        # with one of its own - which, as an update like any other, would be captured too: two versions and two log
        # entries to the one change. So where a table has columns kept that way the update trigger is one of the rest
        # of them, which that second update sets none of. It is by what a statement sets, not by what changes, so an
        # update of every column - as applying a replicated row is - is still captured; one of nothing but such a
        # column is not, and rides along with whatever is next captured of its row.
        of_columns = ''
        if t.event is CaptureEvent.UPDATE and (kept := {
            ut.column
            for ut in tbl.elements.get_any(Trigger)
            if isinstance(ut, UpdatedAtTrigger)
        }):
            of_columns = ' of ' + ', '.join(r.quote_ident(c.name) for c in tbl.elements[Column] if c.name not in kept)

        log_statement = ''
        if t.log:
            log_statement = CAPTURE_LOG_SRC.format(
                log=r.quote_ident(log_table_name(tbl.name.parts[:-1]).last),
                log_columns=', '.join(
                    r.quote_ident(c)
                    for c in (
                        LOG_TABLE,
                        LOG_KEY,
                        LOG_VERSION,
                        LOG_CHANGED_AT,
                    )
                ),
                table_literal=sql_string_literal(tbl.name.last),
                row=row,
                key=key,
                shadow=r.quote_ident(shadow.last),
                shadow_version=r.quote_ident(SHADOW_VERSION),
                shadow_key=r.quote_ident(SHADOW_KEY),
            )

        return [
            CAPTURE_TRIGGER_SRC.format(
                if_not_exists='if not exists ' if opts.if_not_exists else '',
                trigger_name=r.qname(tbl.name.sibling(trigger_name)),
                event=t.event.value,
                of_columns=of_columns,
                table_name=r.quote_ident(tbl.name.last),
                shadow=r.quote_ident(shadow.last),
                log_statement=log_statement,
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
                row=row,
                key=key,
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
