import threading
import time
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...logs import all as logs
from .config import ReplicationSchema
from .links import Link
from .links import LinkSyncReport
from .links import sync_link_once
from .maintenance import DEFAULT_LOG_KEEP_S
from .maintenance import DEFAULT_TOMBSTONE_KEEP_S
from .maintenance import MaintenanceReport
from .maintenance import maintain_node
from .nodes import Node


log = logs.get_module_logger(globals())


##


@dc.dataclass(frozen=True, kw_only=True)
class WorkerReport(lang.Final):
    synced: ta.Sequence[LinkSyncReport] = ()
    failed: ta.Sequence[str] = ()  # link names whose step raised; they back off, the rest carry on
    waiting: ta.Sequence[str] = ()  # link names still in backoff
    maintained: ta.Sequence[MaintenanceReport] = ()


class Worker(lang.Final):
    """
    Drives a set of links in the background: each pass steps every link that is not backing off, a failing link doubles
    its wait up to a cap and never blocks the others, and nothing is ever skipped within a link. Every node the links
    touch is pruned on the maintenance interval. The clock and the sleeper are injectable, so tests step it by hand.
    """

    def __init__(
            self,
            links: ta.Sequence[Link],
            *,
            interval_s: float = 1.,
            max_backoff_s: float = 60.,
            clock: ta.Callable[[], float] = time.monotonic,
            sleeper: ta.Callable[[float], None] = time.sleep,
            maintenance_interval_s: float | None = 60. * 60.,
            log_keep_s: float = DEFAULT_LOG_KEEP_S,
            tombstone_keep_s: float = DEFAULT_TOMBSTONE_KEEP_S,
    ) -> None:
        super().__init__()

        check.arg(interval_s > 0)
        check.arg(max_backoff_s >= interval_s)
        check.arg(maintenance_interval_s is None or maintenance_interval_s > 0)

        self._links = list(links)
        self._interval_s = interval_s
        self._max_backoff_s = max_backoff_s
        self._clock = clock
        self._sleeper = sleeper
        self._maintenance_interval_s = maintenance_interval_s
        self._log_keep_s = log_keep_s
        self._tombstone_keep_s = tombstone_keep_s

        self._failures: dict[str, int] = {}
        self._next_attempt: dict[str, float] = {}
        self._next_maintenance: float | None = None
        self._stop = threading.Event()

        # Every node any link touches, with the schema of a link that touches it.
        self._nodes: dict[str, tuple[Node, ReplicationSchema]] = {}
        for link in self._links:
            for node in (link.source, link.target):
                self._nodes.setdefault(node.name, (node, link.schema))

    @property
    def links(self) -> ta.Sequence[Link]:
        return self._links

    def failures(self, link: str) -> int:
        return self._failures.get(link, 0)

    def run_once(self) -> WorkerReport:
        now = self._clock()
        synced: list[LinkSyncReport] = []
        failed: list[str] = []
        waiting: list[str] = []

        for link in self._links:
            if self._next_attempt.get(link.name, 0.) > now:
                waiting.append(link.name)
                continue

            try:
                synced.append(sync_link_once(link))
            except Exception:  # noqa
                n = self._failures.get(link.name, 0) + 1
                self._failures[link.name] = n
                delay = min(self._interval_s * (2 ** n), self._max_backoff_s)
                self._next_attempt[link.name] = now + delay
                log.exception('Link %r failed (attempt %d); backing off %.1fs', link.name, n, delay)
                failed.append(link.name)
            else:
                self._failures.pop(link.name, None)
                self._next_attempt.pop(link.name, None)

        maintained = self._maybe_maintain(now)

        return WorkerReport(synced=synced, failed=failed, waiting=waiting, maintained=maintained)

    def _maybe_maintain(self, now: float) -> list[MaintenanceReport]:
        # Pruning is due on entry and then every interval; a node that fails to prune just waits for the next one.
        if (mi := self._maintenance_interval_s) is None:
            return []
        if self._next_maintenance is not None and self._next_maintenance > now:
            return []
        self._next_maintenance = now + mi

        out: list[MaintenanceReport] = []
        for node, schema in self._nodes.values():
            try:
                out.append(maintain_node(
                    node,
                    schema,
                    log_keep_s=self._log_keep_s,
                    tombstone_keep_s=self._tombstone_keep_s,
                ))
            except Exception:  # noqa
                log.exception('Maintenance of %r failed', node)
        return out

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        while not self._stop.is_set():
            self.run_once()
            self._sleeper(self._interval_s)
