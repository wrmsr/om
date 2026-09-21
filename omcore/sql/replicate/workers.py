import datetime
import math
import threading
import time
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...logs import all as logs
from .links import Link
from .links import LinkSyncReport
from .links import TableSyncReport
from .links import TailReport
from .links import sync_link_tail
from .links import sync_table_once
from .maintenance import DEFAULT_LOG_KEEP_S
from .maintenance import DEFAULT_TOMBSTONE_KEEP_S
from .maintenance import MaintenanceReport
from .maintenance import maintain_node
from .nodes import Node


log = logs.get_module_logger(globals())


##


@dc.dataclass(frozen=True, kw_only=True)
class TailPacing(lang.Final):
    """
    How long to leave a log alone before looking at it again: a fixed fraction of how long it has already had nothing
    new in it, within bounds. A log just written to is looked at again shortly, as whatever wrote to it likely will
    again; one gone quiet is left for longer the longer it stays so - geometrically longer, but never adding more than
    that fraction to how stale a change waiting in it has already had the chance to get. Nothing is counted or kept but
    when the log was last seen busy.

    With the defaults: every half second for the first five of quiet, every second by ten seconds in, every five by
    fifty, and every ten - as seldom as it gets - from a hundred on.
    """

    min_interval_s: float = .5
    max_interval_s: float = 10.
    idle_ratio: float = .1

    def __post_init__(self) -> None:
        check.arg(0 < self.min_interval_s <= self.max_interval_s)
        check.arg(self.idle_ratio > 0)

    def interval_s(self, idle_s: float) -> float:
        return min(max(idle_s * self.idle_ratio, self.min_interval_s), self.max_interval_s)


##


@dc.dataclass(frozen=True, kw_only=True)
class WorkerReport(lang.Final):
    synced: ta.Sequence[LinkSyncReport] = ()  # what each link with something due did: a tail, a table's batch, or both
    failed: ta.Sequence[str] = ()  # link names whose step raised; they back off, the rest carry on
    waiting: ta.Sequence[str] = ()  # link names still in backoff
    maintained: ta.Sequence[MaintenanceReport] = ()


class _LinkSchedule:
    def __init__(self, link: Link, now: float, sweep_interval_s: float) -> None:
        super().__init__()

        self.link = link

        # A worker starts out taking its links' logs for busy: it is likely there because something is going on.
        self.last_busy = now
        self.next_tail = now if link.source.log else math.inf

        # The tables' first batches are spread over the interval, rather than landing together and staying that way.
        self.next_sweeps = [now + (i * sweep_interval_s / len(link.tables)) for i in range(len(link.tables))]

        self.num_failures = 0
        self.next_attempt: float | None = None

    def next_due(self) -> float:
        if self.next_attempt is not None:
            return self.next_attempt
        return min([self.next_tail, *self.next_sweeps])


class Worker(lang.Final):
    """
    Drives a set of links in the background, each at its own pace and at two of them: its log is tailed as often as it
    has lately been worth it (see `TailPacing`), and its tables are swept a batch at a time, a table at a time, at a
    steady and by default leisurely interval - each batch also pruning the tombstones of the stretch of keys it covers.
    A quiet link then costs a look at its source's log every so often, which for a local source is next to nothing, and
    now and then a small batch of shadows to compare. The sweep does hurry when it finds itself behind: a table whose
    batch had something to ship is due its next one at once.

    A failing link doubles its wait up to a cap and never blocks the others, and nothing is ever skipped within a link.
    The logs of the nodes the links touch are pruned on the maintenance interval. The clocks and the sleeper are
    injectable, so tests step it by hand.
    """

    def __init__(
            self,
            links: ta.Sequence[Link],
            *,
            tail_pacing: TailPacing = TailPacing(),
            sweep_interval_s: float = 60.,
            backoff_s: float = 1.,
            max_backoff_s: float = 60.,
            clock: ta.Callable[[], float] = time.monotonic,
            wall_clock: ta.Callable[[], datetime.datetime] = lambda: datetime.datetime.now(datetime.UTC),
            sleeper: ta.Callable[[float], ta.Any] | None = None,
            maintenance_interval_s: float | None = 60. * 60.,
            log_keep_s: float = DEFAULT_LOG_KEEP_S,
            tombstone_keep_s: float | None = DEFAULT_TOMBSTONE_KEEP_S,
    ) -> None:
        super().__init__()

        check.arg(sweep_interval_s > 0)
        check.arg(0 < backoff_s <= max_backoff_s)
        check.arg(maintenance_interval_s is None or maintenance_interval_s > 0)
        check.arg(tombstone_keep_s is None or tombstone_keep_s >= 0)

        self._links = list(links)
        self._tail_pacing = tail_pacing
        self._sweep_interval_s = sweep_interval_s
        self._backoff_s = backoff_s
        self._max_backoff_s = max_backoff_s
        self._clock = clock
        self._wall_clock = wall_clock
        self._maintenance_interval_s = maintenance_interval_s
        self._log_keep_s = log_keep_s
        self._tombstone_keep_s = tombstone_keep_s

        self._stop = threading.Event()

        # Waiting on the stop signal rather than the clock, a stop does not have to wait out a sleep.
        self._sleeper = sleeper if sleeper is not None else self._stop.wait

        now = self._clock()
        self._schedules = [_LinkSchedule(link, now, sweep_interval_s) for link in self._links]
        self._next_maintenance: float | None = now if maintenance_interval_s is not None else None

        # Every node any link touches.
        self._nodes: dict[str, Node] = {}
        for link in self._links:
            for node in (link.source, link.target):
                self._nodes.setdefault(node.name, node)

    @property
    def links(self) -> ta.Sequence[Link]:
        return self._links

    def failures(self, link: str) -> int:
        return check.single(s for s in self._schedules if s.link.name == link).num_failures

    #

    def _step(self, sch: _LinkSchedule, now: float) -> LinkSyncReport | None:
        link = sch.link

        tail_due = sch.next_tail <= now
        sweep_table = min(range(len(sch.next_sweeps)), key=sch.next_sweeps.__getitem__)
        sweep_due = sch.next_sweeps[sweep_table] <= now
        if not (tail_due or sweep_due):
            return None

        tail: TailReport | None = None
        swept: TableSyncReport | None = None

        with link.connect() as lc:
            if tail_due:
                tail = sync_link_tail(link, conns=lc)

            if sweep_due:
                swept = sync_table_once(
                    link,
                    link.tables[sweep_table],
                    conns=lc,
                    prune_tombstones_before=(
                        self._wall_clock() - datetime.timedelta(seconds=self._tombstone_keep_s)
                        if self._tombstone_keep_s is not None else None
                    ),
                )

        now = self._clock()

        if tail is not None:
            if tail.entries:
                sch.last_busy = now
            # A batch which came back full has more behind it, and is not made to wait.
            sch.next_tail = now + (self._tail_pacing.interval_s(now - sch.last_busy) if tail.drained else 0.)

        if swept is not None:
            # Nor is a table found to be behind: having had something to ship, it likely has more.
            shipped = (swept.applied + swept.deleted) > 0
            sch.next_sweeps[sweep_table] = now + (0. if shipped else self._sweep_interval_s)

        return LinkSyncReport(
            link=link.name,
            tables=[swept] if swept is not None else [],
            tail=tail,
        )

    def run_once(self) -> WorkerReport:
        """Does whatever is due, which may well be nothing."""

        now = self._clock()
        synced: list[LinkSyncReport] = []
        failed: list[str] = []
        waiting: list[str] = []

        for sch in self._schedules:
            link = sch.link

            if sch.next_attempt is not None:
                if sch.next_attempt > now:
                    waiting.append(link.name)
                    continue
                sch.next_attempt = None

            try:
                rep = self._step(sch, now)
            except Exception:  # noqa
                sch.num_failures += 1
                delay = min(self._backoff_s * (2 ** sch.num_failures), self._max_backoff_s)
                sch.next_attempt = now + delay
                log.exception('Link %r failed (attempt %d); backing off %.1fs', link.name, sch.num_failures, delay)
                failed.append(link.name)
            else:
                sch.num_failures = 0
                if rep is not None:
                    synced.append(rep)

        maintained = self._maybe_maintain(now)

        return WorkerReport(synced=synced, failed=failed, waiting=waiting, maintained=maintained)

    def _maybe_maintain(self, now: float) -> list[MaintenanceReport]:
        # Due on entry and then every interval; a node that fails to be maintained just waits for the next one.
        if (mi := self._maintenance_interval_s) is None:
            return []
        if self._next_maintenance is not None and self._next_maintenance > now:
            return []
        self._next_maintenance = now + mi

        out: list[MaintenanceReport] = []
        for node in self._nodes.values():
            try:
                out.append(maintain_node(
                    node,
                    log_keep_s=self._log_keep_s,
                    now=self._wall_clock(),
                ))
            except Exception:  # noqa
                log.exception('Maintenance of %r failed', node)
        return out

    #

    def next_due(self) -> float:
        """When, by the worker's clock, there will next be something for `run_once` to do."""

        return min([
            *(sch.next_due() for sch in self._schedules),
            self._next_maintenance if self._next_maintenance is not None else math.inf,
        ])

    def stop(self) -> None:
        self._stop.set()

    # However far off the next thing due, the clock is looked at again at least this often.
    _MAX_SLEEP_S: ta.ClassVar[float] = 60.

    def run(self) -> None:
        while not self._stop.is_set():
            self.run_once()
            self._sleeper(min(max(self.next_due() - self._clock(), 0.), self._MAX_SLEEP_S))
