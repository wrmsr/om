import contextlib
import datetime
import os
import socket
import threading
import typing as ta

from .... import check
from .... import lang
from ...api.core import Conn
from ...api.core import Db
from .backends import SandboxBackend
from .config import SandboxesConfig
from .errors import SandboxStateError
from .names import SandboxNames
from .names import new_run_id
from .reaping import Reaper
from .reaping import ReapReport
from .registry import SandboxKind
from .registry import SandboxRecord
from .registry import SandboxRegistry


##


class Sandbox(lang.Final):
    """An isolated namespace a test owns until it is released; a context manager for exactly that."""

    def __init__(self, allocator: SandboxAllocator, name: str) -> None:
        super().__init__()

        self._allocator = allocator
        self._name = name

        self._db: Db | None = None
        self._released = False

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._name!r})'

    @property
    def name(self) -> str:
        return self._name

    @property
    def run_id(self) -> str:
        return self._allocator.run_id

    @property
    def released(self) -> bool:
        return self._released

    def db(self) -> Db:
        if self._released:
            raise SandboxStateError(f'{self!r} is released')
        if (db := self._db) is None:
            db = self._db = self._allocator.backend.sandbox_db(self.run_id, self._name)
        return db

    def release(self) -> None:
        if not self._released:
            self._allocator.release(self)

    def _mark_released(self) -> None:
        self._released = True

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class SandboxAllocator(lang.Final):
    """
    One per process, for its lifetime: it holds the run id, a session to the sandbox database, and the sandboxes it
    has handed out. Entering it runs the safety guard, self-bootstraps the registry under a lock, and makes a
    best-effort reaping pass; exiting it releases whatever the process still holds. Allocation, release, and renewal
    share one connection and are serialized on a lock, so they may be called from any thread.
    """

    def __init__(
            self,
            backend: SandboxBackend,
            *,
            run_id: str | None = None,
            owner: str | None = None,
            no_reap_on_open: bool = False,
    ) -> None:
        super().__init__()

        self._backend = backend
        self._cfg = backend.config
        self._names = SandboxNames(self._cfg)
        self._registry = SandboxRegistry(self._cfg)
        self._reaper = Reaper(backend, self._registry, self._names)

        self._run_id = self._names.check_run_id(run_id if run_id is not None else new_run_id())
        self._owner = owner if owner is not None else f'{socket.gethostname()}:{os.getpid()}'
        self._no_reap_on_open = no_reap_on_open

        self._lock = threading.Lock()
        self._seq = 0
        self._sandboxes: dict[str, Sandbox] = {}

        self._es: contextlib.ExitStack | None = None
        self._db: Db | None = None
        self._conn: Conn | None = None

    @property
    def backend(self) -> SandboxBackend:
        return self._backend

    @property
    def config(self) -> SandboxesConfig:
        return self._cfg

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def registry(self) -> SandboxRegistry:
        return self._registry

    @property
    def sandboxes(self) -> ta.Sequence[Sandbox]:
        return list(self._sandboxes.values())

    #

    def _open_conn(self) -> Conn:
        if (conn := self._conn) is None:
            raise SandboxStateError('not entered')
        return conn

    def __enter__(self) -> ta.Self:
        check.none(self._es)
        es = contextlib.ExitStack()
        try:
            self._db = db = self._backend.open_db(self._run_id)
            self._conn = conn = es.enter_context(db.connect())

            self._backend.guard(conn)

            # Registry creation is not concurrency-safe on its own (two runs racing to create the same schema), so it
            # waits on the lock rather than skipping like the reaper does; it is over in a moment.
            self._backend.lock(conn, 'registry')
            try:
                self._backend.ensure_registry(conn, self._registry)
            finally:
                self._backend.unlock(conn, 'registry')

            if not self._no_reap_on_open:
                self.reap()

        except BaseException:
            es.close()
            self._db = self._conn = None
            raise

        self._es = es
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        es = check.not_none(self._es)
        try:
            self.release_all()
        finally:
            self._es = self._db = self._conn = None
            es.close()

    def abandon(self) -> None:
        """
        Drops the session without releasing anything, leaving the sandboxes exactly as a crashed process would. For
        exercising the reaper; not for ordinary use.
        """

        es = check.not_none(self._es)
        self._es = self._db = self._conn = None
        es.close()

    #

    def _expires_at(self, now: datetime.datetime) -> datetime.datetime:
        return now + datetime.timedelta(seconds=self._cfg.lease_ttl_s)

    def allocate(self) -> Sandbox:
        with self._lock:
            conn = self._open_conn()

            self._seq += 1
            name = self._names.sandbox_name(self._run_id, self._seq)

            now = self._backend.server_now(conn)
            with conn.begin() as txn:
                self._registry.insert(txn, SandboxRecord(
                    name=name,
                    kind=SandboxKind.SCHEMA,
                    run_id=self._run_id,
                    owner=self._owner,
                    created_at=now,
                    expires_at=self._expires_at(now),
                ))
                self._backend.create_sandbox(txn, name)

            # Any activity keeps the whole run's leases fresh, so an idle sibling sandbox never expires under a run
            # that is still going.
            self._registry.renew_run(conn, self._run_id, self._expires_at(now))

            sb = Sandbox(self, name)
            self._sandboxes[name] = sb
            return sb

    def release(self, sb: Sandbox) -> None:
        with self._lock:
            check.is_(self._sandboxes.get(sb.name), sb)
            conn = self._open_conn()

            # Drop first, then unregister: a crash in between leaves a registered name with nothing behind it, which
            # the reaper cleans up; the reverse order could leak an unregistered schema.
            self._backend.drop_sandbox(conn, sb.name)
            self._registry.delete(conn, sb.name)

            del self._sandboxes[sb.name]
            sb._mark_released()  # noqa

    def release_all(self) -> None:
        for sb in list(self._sandboxes.values()):
            sb.release()

    def renew(self) -> None:
        with self._lock:
            conn = self._open_conn()
            self._registry.renew_run(conn, self._run_id, self._expires_at(self._backend.server_now(conn)))

    def reap(self) -> ReapReport:
        with self._lock:
            self._open_conn()
            return self._reaper.reap(check.not_none(self._db))
