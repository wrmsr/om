# ruff: noqa: S608
import typing as ta

from .... import lang
from ...backends.mysql.inspect import MysqlInspector
from ...backends.mysql.tabledefs import MysqlTabledefRenderer
from ...backends.mysql.values import MysqlDtypeCodec
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
from .base import ReplicateBackend


##


CAPTURE_TRIGGER_SRC = """\
create trigger {trigger_name}
after {event} on {table_name}
for each row
begin
  insert ignore into {shadow} ({shadow_columns})
  values ({row}.{key}, 0, (select {node_id} from {node_table}), 0, current_timestamp);

  update {shadow}
  set {shadow_version} = {shadow_version} + 1,
      {shadow_origin} = (select {node_id} from {node_table}),
      {shadow_deleted} = {deleted},
      {shadow_changed_at} = current_timestamp
  where {shadow_key} = {row}.{key};
end\
"""


class MysqlCaptureTriggerRenderer(TriggerRenderer[CaptureTrigger]):
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
        trigger_qn = tbl.name.sibling(t.trigger_name(tbl.name))
        shadow = shadow_name(tbl.name)
        node_table = node_table_name(tbl.name.parts[:-1])

        stmts: list[str] = []
        if opts.if_not_exists:
            # Mysql has neither 'if not exists' nor 'or replace' for triggers.
            stmts.append(f'drop trigger if exists {r.qname(trigger_qn)}')

        stmts.append(CAPTURE_TRIGGER_SRC.format(
            trigger_name=r.qname(trigger_qn),
            event=t.event.value,
            table_name=r.qname(tbl.name),
            shadow=r.qname(shadow),
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
            node_table=r.qname(node_table),
            deleted='1' if t.event is CaptureEvent.DELETE else '0',
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


class MysqlReplicateBackend(ReplicateBackend, lang.Final):
    @property
    def tabledef_renderer(self) -> Renderer:
        return MysqlTabledefRenderer(trigger_renderers=[MysqlCaptureTriggerRenderer()])

    @property
    def inspector(self) -> Inspector:
        return MysqlInspector()

    @property
    def dtype_codec(self) -> DtypeCodec:
        return MysqlDtypeCodec()

    def upsert_sql(
            self,
            table: str,
            columns: ta.Sequence[str],
            key: str,
            placeholders: ta.Sequence[str],
    ) -> str:
        # The row-alias form (8.0.19+) rather than the deprecated values() function; mysql demands at least one
        # assignment, so a key-only table re-assigns its key.
        sets = [f'{c} = new.{c}' for c in columns if c != key] or [f'{key} = {key}']
        return (
            f'insert into {table} ({", ".join(columns)}) values ({", ".join(placeholders)}) as new '
            f'on duplicate key update {", ".join(sets)}'
        )
