import datetime
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from .nodes import Node


##


DEFAULT_LOG_KEEP_S: ta.Final[float] = 7 * 24 * 60 * 60.
DEFAULT_TOMBSTONE_KEEP_S: ta.Final[float] = 30 * 24 * 60 * 60.


@dc.dataclass(frozen=True, kw_only=True)
class MaintenanceReport(lang.Final):
    node: str
    log_pruned_before: datetime.datetime | None


async def prune_log(node: Node, *, keep_s: float, now: datetime.datetime | None = None) -> datetime.datetime:
    """
    Drops log entries older than the retention, short of the newest one. The log is a hint list, so a dropped entry
    costs nothing but the freshness a tail would have given a link that was away longer than the retention; the sweep
    covers it.
    """

    check.arg(keep_s >= 0)
    before = (now if now is not None else datetime.datetime.now(datetime.UTC)) - datetime.timedelta(seconds=keep_s)
    async with node.db.connect() as conn:
        await node.backend.prune_log(conn, node.log_table, before=before)
    return before


async def maintain_node(
        node: Node,
        *,
        log_keep_s: float = DEFAULT_LOG_KEEP_S,
        now: datetime.datetime | None = None,
) -> MaintenanceReport:
    """
    What a node needs done to it every so often which no link's sweep gets done along its way - which the pruning of
    tombstones is, and so is not here.
    """

    return MaintenanceReport(
        node=node.name,
        log_pruned_before=await prune_log(
            node,
            keep_s=log_keep_s,
            now=now,
        ) if node.log else None,
    )
