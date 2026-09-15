import typing as ta

from .... import lang
from ...backends.postgres.inspect import PostgresInspector
from ...backends.postgres.tabledefs import PostgresTabledefRenderer
from ...backends.postgres.values import PostgresDtypeCodec
from ...dtypes.codecs import DtypeCodec
from ...inspect.inspectors import Inspector
from ...qualifiedname import QualifiedName
from ...tabledefs.rendering import Renderer
from ...tabledefs.tabledefs import TableDef
from ...tabledefs.triggers import TriggerRenderer
from ..config import table_key_column
from ..names import capture_function_name
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


CAPTURE_FUNCTION_SRC = """\
create or replace function {function_name}()
returns trigger
language plpgsql
as $$
begin
  insert into {shadow} ({shadow_columns})
  values ({row}.{key}, 0, (select {node_id} from {node_table}), false, current_timestamp)
  on conflict ({shadow_key}) do nothing;

  update {shadow}
  set {shadow_version} = {shadow_version} + 1,
      {shadow_origin} = (select {node_id} from {node_table}),
      {shadow_deleted} = {deleted},
      {shadow_changed_at} = current_timestamp
  where {shadow_key} = {row}.{key};
{log_statement}
  return null;
end;
$$\
"""


CAPTURE_LOG_SRC = """\

  insert into {log} ({log_columns})
  values ({table_literal}, {row}.{key}, (select {shadow_version} from {shadow} where {shadow_key} = {row}.{key}), current_timestamp);
"""  # noqa


CAPTURE_TRIGGER_SRC = """\
create {or_replace}trigger {trigger_name}
after {event} on {table_name}
for each row
execute function {function_name}()
"""


class PostgresCaptureTriggerRenderer(TriggerRenderer[CaptureTrigger]):
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
        function_qn = tbl.name.sibling(capture_function_name(trigger_name))
        shadow = shadow_name(tbl.name)
        node_table = node_table_name(tbl.name.parts[:-1])
        row = 'old' if t.event is CaptureEvent.DELETE else 'new'
        key = r.quote_ident(table_key_column(tbl).name)

        log_statement = ''
        if t.log:
            log_statement = CAPTURE_LOG_SRC.format(
                log=r.qname(log_table_name(tbl.name.parts[:-1])),
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
                shadow=r.qname(shadow),
                shadow_version=r.quote_ident(SHADOW_VERSION),
                shadow_key=r.quote_ident(SHADOW_KEY),
            )

        return [
            CAPTURE_FUNCTION_SRC.format(
                function_name=r.qname(function_qn),
                shadow=r.qname(shadow),
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
                node_table=r.qname(node_table),
                deleted='true' if t.event is CaptureEvent.DELETE else 'false',
            ),

            CAPTURE_TRIGGER_SRC.format(
                or_replace='or replace ' if opts.if_not_exists else '',
                trigger_name=r.quote_ident(trigger_name),
                event=t.event.value,
                table_name=r.qname(tbl.name),
                function_name=r.qname(function_qn),
            ),
        ]

    def drop_statements(
            self,
            r: Renderer,
            table_name: QualifiedName,
            name: str,
    ) -> list[str]:
        function_qn = table_name.sibling(capture_function_name(name))
        return [
            f'drop trigger if exists {r.quote_ident(name)} on {r.qname(table_name)}',
            f'drop function if exists {r.qname(function_qn)}()',
        ]


##


class PostgresReplicateBackend(OnConflictReplicateBackend, lang.Final):
    @property
    def tabledef_renderer(self) -> Renderer:
        return PostgresTabledefRenderer(trigger_renderers=[PostgresCaptureTriggerRenderer()])

    @property
    def inspector(self) -> Inspector:
        return PostgresInspector()

    @property
    def dtype_codec(self) -> DtypeCodec:
        return PostgresDtypeCodec()

    def now_sql(self) -> str:
        return 'current_timestamp'

    @property
    def dialect_name(self) -> ta.Literal['postgres']:
        return 'postgres'
