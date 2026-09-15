import datetime
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from .config import ReplicationSchema
from .nodes import Node


##


DEFAULT_LOG_KEEP_S: ta.Final[float] = 7 * 24 * 60 * 60.
DEFAULT_TOMBSTONE_KEEP_S: ta.Final[float] = 30 * 24 * 60 * 60.


@dc.dataclass(frozen=True, kw_only=True)
class MaintenanceReport(lang.Final):
    node: str
    log_pruned_before: datetime.datetime | None
    tombstones_pruned_before: datetime.datetime | None


def prune_log(node: Node, *, keep_s: float, now: datetime.datetime | None = None) -> datetime.datetime:
    """
    Drops log entries older than the retention. The log is a hint list, so a dropped entry costs nothing but the
    freshness a tail would have given a link that was away longer than the retention; the sweep covers it.
    """

    check.arg(keep_s >= 0)
    before = (now if now is not None else datetime.datetime.now(datetime.UTC)) - datetime.timedelta(seconds=keep_s)
    with node.db.connect() as conn:
        node.backend.prune_log(conn, node.log_table, before=before)
    return before


def prune_tombstones(
        node: Node,
        schema: ReplicationSchema,
        *,
        keep_s: float,
        now: datetime.datetime | None = None,
) -> datetime.datetime:
    """
    Drops shadow tombstones older than the retention. A tombstone is what tells a reader to delete its copy, so a
    reader that was away longer than the retention keeps its stale row: keep this long, and know the limitation.
    """

    check.arg(keep_s >= 0)
    before = (now if now is not None else datetime.datetime.now(datetime.UTC)) - datetime.timedelta(seconds=keep_s)
    with node.db.connect() as conn:
        for td in schema.tables:
            node.backend.prune_tombstones(conn, node.shadow_name(td), before=before)
    return before


def maintain_node(
        node: Node,
        schema: ReplicationSchema,
        *,
        log_keep_s: float = DEFAULT_LOG_KEEP_S,
        tombstone_keep_s: float = DEFAULT_TOMBSTONE_KEEP_S,
        now: datetime.datetime | None = None,
) -> MaintenanceReport:
    return MaintenanceReport(
        node=node.name,
        log_pruned_before=prune_log(node, keep_s=log_keep_s, now=now) if node.log else None,
        tombstones_pruned_before=prune_tombstones(node, schema, keep_s=tombstone_keep_s, now=now),
    )
