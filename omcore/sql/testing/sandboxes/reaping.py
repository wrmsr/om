import typing as ta

from .... import dataclasses as dc
from .... import lang
from ....logs import all as logs
from ...api.core import Db
from ...api.queriers import Querier
from .backend import SandboxBackend
from .names import SandboxNames
from .registry import SandboxKind


log = logs.get_module_logger(globals())


##


@dc.dataclass(frozen=True, kw_only=True)
class ReapReport(lang.Final):
    skipped: bool = False  # another reaper held the lock; nothing was examined

    reaped: ta.Sequence[str] = ()
    failed: ta.Sequence[str] = ()        # gave up after the configured attempts; the next pass will try again
    live: ta.Sequence[str] = ()          # lease expired but the run still has a session open, so left alone
    unrecognized: ta.Sequence[str] = ()  # under the prefix but not a sandbox name; never touched, only reported


class Reaper(lang.Final):
    """
    Cleans up after runs that died without cleaning up after themselves. There is no coordinator: whichever run gets the
    advisory lock does the work, and any other run that finds it held simply skips. A sandbox is reaped when its lease
    has expired and no session of its run is still connected, or when it exists under the prefix with no registry row at
    all. Each drop is attempted a bounded number of times and a failure never stops the pass.
    """

    LOCK_NAME: ta.ClassVar[str] = 'reaper'

    def __init__(
            self,
            backend: SandboxBackend,
            names: SandboxNames,
    ) -> None:
        super().__init__()

        self._backend = backend
        self._registry = backend.registry
        self._names = names

    def reap(self, db: Db) -> ReapReport:
        # The lock is session-level, so it gets a connection of its own and is released with it no matter what.
        with db.connect() as conn:
            if not self._backend.try_lock(conn, self.LOCK_NAME):
                return ReapReport(skipped=True)

            try:
                return self._reap(conn)
            finally:
                self._backend.unlock(conn, self.LOCK_NAME)

    def _reap(self, q: Querier) -> ReapReport:
        now = self._backend.server_now(q)

        reaped: list[str] = []
        failed: list[str] = []
        live: list[str] = []
        unrecognized: list[str] = []

        for rec in self._registry.list_all(q):
            if rec.expires_at >= now:
                continue
            if self._backend.run_is_live(q, rec.run_id):
                live.append(rec.name)
                continue
            self._reap_one(q, rec.name, rec.kind, reaped, failed)

        for u in self._backend.list_unregistered(q):
            if self._names.parse_sandbox_name(u.name) is None:
                unrecognized.append(u.name)
                continue
            self._reap_one(q, u.name, u.kind, reaped, failed)

        return ReapReport(
            reaped=reaped,
            failed=failed,
            live=live,
            unrecognized=unrecognized,
        )

    def _reap_one(
            self,
            q: Querier,
            name: str,
            kind: SandboxKind,
            reaped: list[str],
            failed: list[str],
    ) -> None:
        self._names.check_sandbox_name(name)

        for attempt in range(self._backend.config.reap_attempts):
            try:
                self._backend.drop_sandbox(q, name, kind)
                self._registry.delete(q, name)
            except Exception:  # noqa
                log.exception('Failed to reap sandbox %r (attempt %d)', name, attempt + 1)
                continue
            else:
                log.info('Reaped orphaned sandbox %r', name)
                reaped.append(name)
                return

        failed.append(name)
