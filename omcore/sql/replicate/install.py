import typing as ta
import uuid

from ... import dataclasses as dc
from ... import lang
from ..api import querierfuncs as qf
from ..api.asyncs import ImmediateSyncToAsyncRunner
from ..api.asyncs import SyncToAsyncConn
from ..api.queriers import Querier
from ..inspect.migrating import TableMigration
from ..inspect.migrating import migrate_table
from ..tabledefs.diffing import diff_table
from ..tabledefs.elements import Elements
from ..tabledefs.elements import OpaqueTrigger
from ..tabledefs.tabledefs import TableDef
from .config import ReplicationSchema
from .errors import ReplicationInstallError
from .nodes import Node
from .shadows import cursor_table_def
from .shadows import log_table_def
from .shadows import node_table_def
from .shadows import shadow_table_def
from .triggers import CAPTURE_TRIGGER_VERSION
from .triggers import CaptureTrigger
from .triggers import capture_triggers


##


@dc.dataclass(frozen=True, kw_only=True)
class InstallReport(lang.Final):
    node_id: uuid.UUID
    created_node: bool
    migrations: ta.Sequence[TableMigration]


def install_node(
        node: Node,
        schema: ReplicationSchema,
        *,
        no_manage_base_tables: bool = False,
        capture_trigger_version: int = CAPTURE_TRIGGER_VERSION,
) -> InstallReport:
    """
    Idempotently brings a node up to the schema: its identity row, its cursor table, its change log if it keeps one,
    and for every table the shadow table, the capture triggers, and a backfill of shadow rows for base rows that have
    none. Base tables are created and
    migrated too unless told otherwise, in which case they must already exist and only their triggers are managed.
    Everything goes through the tabledefs machinery, so a trigger body change (a version bump) is a drop and an add like
    any other migration.
    """

    r = node.backend.tabledef_renderer
    insp = node.backend.inspector
    migrations: list[TableMigration] = []

    with node.db.connect() as conn:
        aconn = SyncToAsyncConn(ImmediateSyncToAsyncRunner(), conn)

        def migrate(td: TableDef) -> None:
            migrations.append(lang.sync_await(migrate_table(aconn, td, inspector=insp, renderer=r)))

        migrate(node_table_def(node.node_table))
        created_node = False
        if (node_id := node.backend.read_node_id(conn, node.node_table)) is None:
            node_id = uuid.uuid7()
            node.backend.insert_node_id(conn, node.node_table, node_id)
            created_node = True
        node._set_node_id(node_id)  # noqa

        migrate(cursor_table_def(node.cursor_table))
        if node.log:
            migrate(log_table_def(node.log_table))

        for td in schema.tables:
            table = node.table_name(td)
            shadow = node.shadow_name(td)

            # The shadow must exist before a trigger can write to it.
            migrate(shadow_table_def(shadow))

            base = dc.replace(td, name=table)
            if not no_manage_base_tables:
                migrate(TableDef(table, Elements(
                    *base.elements,
                    *capture_triggers(capture_trigger_version, log=node.log),
                )))
            else:
                _migrate_triggers_only(conn, aconn, node, base, capture_trigger_version)

            node.backend.backfill_shadow(conn, td, table, shadow, node_id)

    return InstallReport(node_id=node_id, created_node=created_node, migrations=migrations)


def _migrate_triggers_only(
        conn: Querier,
        aconn: ta.Any,
        node: Node,
        base: TableDef,
        capture_trigger_version: int,
) -> None:
    """Adds or refreshes the capture triggers on a table that exists and is otherwise not ours to touch."""

    insp = node.backend.inspector
    r = node.backend.tabledef_renderer

    reflected = lang.sync_await(insp.reflect_table(aconn, base.name))
    if reflected is None:
        raise ReplicationInstallError(f'table {base.name.dotted!r} does not exist on {node!r}')
    existing = insp.lift_table(reflected)

    # The reflected table, minus the opaque reflections of our own triggers, plus the triggers as we want them: the diff
    # is then trigger ops only, and it drops any stale version of ours while leaving foreign triggers alone.
    kept = [
        e for e in existing.elements
        if not (isinstance(e, OpaqueTrigger) and CaptureTrigger.owns_trigger_name(base.name, e.name))
    ]
    current = TableDef(base.name, Elements(*kept, *capture_triggers(capture_trigger_version, log=node.log)))

    for op in diff_table(current, existing):
        for s in r.render_migration(op):
            qf.exec(conn, s)
