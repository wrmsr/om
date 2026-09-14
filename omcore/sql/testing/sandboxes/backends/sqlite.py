import datetime
import fcntl
import os
import re
import shutil
import sqlite3
import tempfile
import threading
import typing as ta

from ..... import check
from ....api import querierfuncs as qf
from ....api.core import Conn
from ....api.core import Db
from ....api.dbapi import ClosingDbapiConnector
from ....api.dbapi import DbapiDb
from ....api.queriers import Querier
from ....backends import sqlite as be
from ....qualifiedname import qn
from ....tabledefs.rendering import Renderer
from ..backend import SandboxBackend
from ..backend import UnregisteredSandbox
from ..config import SandboxesConfig
from ..errors import SandboxSafetyError
from ..errors import SandboxStateError
from ..names import SandboxNames
from ..registry import IsoTimestampCodec
from ..registry import SandboxKind
from ..registry import SandboxRecord
from ..registry import SandboxRegistry


##


_LOCK_NAME_PAT = re.compile(r'^[a-z_]+$')


class SqliteSandboxBackend(SandboxBackend):
    """
    A sandbox is a directory under a base directory, holding its database file. There is no server, so the registry is
    a sqlite file of its own in the base directory, the advisory locks are file locks, the clock is the local one (every
    run shares a host), and a run holds a file lock named after itself for as long as it lives - released by the kernel
    if it dies - which is what a reaper checks.
    """

    DB_FILE_NAME: ta.ClassVar[str] = 'db.sqlite'

    def __init__(
            self,
            cfg: SandboxesConfig,
            *,
            base_dir: str | None = None,
    ) -> None:
        super().__init__()

        self._cfg = cfg
        if base_dir is None:
            base_dir = os.path.join(tempfile.gettempdir(), cfg.internal_prefix + 'sqlite')
        self._base_dir = os.path.abspath(base_dir)

        self._locks_dir = os.path.join(self._base_dir, cfg.internal_prefix + 'locks')
        self._registry_path = os.path.join(self._base_dir, cfg.registry_schema + '.sqlite')

        self._names = SandboxNames(cfg)
        self._renderer = be.td.SqliteTabledefRenderer()
        # The registry file is the connection's main database, so its table is unqualified; timestamps are text.
        self._registry = SandboxRegistry(
            cfg,
            table_name=qn(SandboxRegistry.TABLE_NAME),
            timestamp_codec=IsoTimestampCodec(),
        )

        self._mutex = threading.Lock()
        self._locks: dict[tuple[int, str], int] = {}
        self._run_locks: dict[str, int] = {}

    @property
    def config(self) -> SandboxesConfig:
        return self._cfg

    @property
    def registry(self) -> SandboxRegistry:
        return self._registry

    @property
    def supported_kinds(self) -> ta.AbstractSet[SandboxKind]:
        return {SandboxKind.DATABASE}

    @property
    def default_kind(self) -> SandboxKind:
        return SandboxKind.DATABASE

    @property
    def base_dir(self) -> str:
        return self._base_dir

    def sandbox_dir(self, name: str) -> str:
        return os.path.join(self._base_dir, self._names.check_sandbox_name(name))

    def sandbox_db_path(self, name: str) -> str:
        return os.path.join(self.sandbox_dir(name), self.DB_FILE_NAME)

    #

    def _check_base_dir(self) -> None:
        # The base directory is the whole of what this backend may touch, so it must itself be under the prefix - and
        # that is checked before anything is created in it, not just by the guard.
        if not os.path.basename(self._base_dir).startswith(self._cfg.internal_prefix):
            raise SandboxSafetyError(
                f'base dir {self._base_dir!r} is not under the internal prefix {self._cfg.internal_prefix!r}',
            )

    def _ensure_dirs(self) -> None:
        self._check_base_dir()
        os.makedirs(self._locks_dir, exist_ok=True)

    def _db(self, path: str) -> Db:
        return DbapiDb(
            ClosingDbapiConnector(
                sqlite3.connect,
                path,
                autocommit=True,
                check_same_thread=False,
                timeout=30.,
            ),
            adapter=be.adapters.sqlite_adapter(),
        )

    def open_db(self, run_id: str) -> Db:
        self._names.check_run_id(run_id)
        self._ensure_dirs()
        return self._db(self._registry_path)

    def sandbox_db(self, run_id: str, name: str, kind: SandboxKind) -> Db:
        check.is_(kind, SandboxKind.DATABASE)
        return self._db(self.sandbox_db_path(name))

    #

    def guard(self, q: Querier) -> None:
        self._check_base_dir()
        if not os.path.isdir(self._base_dir):
            raise SandboxSafetyError(f'base dir {self._base_dir!r} does not exist')

    def ensure_registry(self, q: Querier) -> None:
        for s in self._renderer.render_create_statements(
                self._registry.table_def,
                Renderer.CreateOptions(if_not_exists=True),
        ):
            qf.exec(q, s)

    #

    def _lock_path(self, name: str) -> str:
        check.arg(_LOCK_NAME_PAT.fullmatch(name) is not None, name)
        return os.path.join(self._locks_dir, name + '.lock')

    def _open_lock(self, path: str) -> int:
        return os.open(path, os.O_RDWR | os.O_CREAT, 0o644)

    def _flock(self, path: str, *, blocking: bool) -> int | None:
        fd = self._open_lock(path)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            os.close(fd)
            return None
        except BaseException:
            os.close(fd)
            raise
        return fd

    def _funlock(self, fd: int) -> None:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    # Locks are keyed by the querier they were taken through, mirroring a server's session-level locks: each open of a
    # lock file is its own file description, so two takers conflict even within one process.

    def try_lock(self, q: Querier, name: str) -> bool:
        key = (id(q), name)
        with self._mutex:
            check.not_in(key, self._locks)
            if (fd := self._flock(self._lock_path(name), blocking=False)) is None:
                return False
            self._locks[key] = fd
            return True

    def lock(self, q: Querier, name: str) -> None:
        key = (id(q), name)
        with self._mutex:
            check.not_in(key, self._locks)
        fd = check.not_none(self._flock(self._lock_path(name), blocking=True))
        with self._mutex:
            self._locks[key] = fd

    def unlock(self, q: Querier, name: str) -> None:
        with self._mutex:
            fd = self._locks.pop((id(q), name))
        self._funlock(fd)

    def server_now(self, q: Querier) -> datetime.datetime:
        return datetime.datetime.now(datetime.UTC)

    #

    def _run_lock_path(self, run_id: str) -> str:
        return os.path.join(self._locks_dir, 'run_' + self._names.check_run_id(run_id).replace('-', '_') + '.lock')

    def mark_run_live(self, q: Querier, run_id: str) -> None:
        with self._mutex:
            check.not_in(run_id, self._run_locks)
            if (fd := self._flock(self._run_lock_path(run_id), blocking=False)) is None:
                raise SandboxStateError(f'run {run_id!r} is already marked live elsewhere')
            self._run_locks[run_id] = fd

    def _unlink_run_lock(self, run_id: str) -> None:
        # Only ever called while holding the lock of a run known to be over: run ids are never reused, so nobody can
        # be racing to take it.
        try:
            os.unlink(self._run_lock_path(run_id))
        except FileNotFoundError:
            pass

    def unmark_run_live(self, q: Querier, run_id: str) -> None:
        with self._mutex:
            fd = self._run_locks.pop(run_id)
        try:
            self._unlink_run_lock(run_id)
        finally:
            self._funlock(fd)

    def run_is_live(self, q: Querier, run_id: str) -> bool:
        if (fd := self._flock(self._run_lock_path(run_id), blocking=False)) is None:
            return True
        try:
            self._unlink_run_lock(run_id)
        finally:
            self._funlock(fd)
        return False

    #

    def create_sandbox(self, conn: Conn, rec: SandboxRecord) -> None:
        check.is_(rec.kind, SandboxKind.DATABASE)
        path = self.sandbox_dir(rec.name)

        # A directory and a row cannot commit together, so register first; a crash in between leaves a phantom row,
        # harmless to reap.
        self._registry.insert(conn, rec)
        os.mkdir(path)

    def drop_sandbox(self, q: Querier, name: str, kind: SandboxKind) -> None:
        check.is_(kind, SandboxKind.DATABASE)
        path = self.sandbox_dir(name)
        # Belt and braces: the name was validated, and the path it yields must still sit directly under the base dir.
        check.equal(os.path.dirname(os.path.realpath(path)), os.path.realpath(self._base_dir))
        if os.path.isdir(path):
            shutil.rmtree(path)

    def list_unregistered(self, q: Querier) -> list[UnregisteredSandbox]:
        # The directory listing is taken *before* the registry is read: a sandbox is registered before its directory
        # exists, so a directory seen here has its row in any registry read afterwards, and cannot be mid-creation.
        prefix = self._cfg.prefix
        internal_prefix = self._cfg.internal_prefix
        dirs = sorted(
            d for d in os.listdir(self._base_dir)
            if d.startswith(prefix) and not d.startswith(internal_prefix) and os.path.isdir(os.path.join(self._base_dir, d))  # noqa
        )
        registered = {r.name for r in self._registry.list_all(q)}
        return [UnregisteredSandbox(d, SandboxKind.DATABASE) for d in dirs if d not in registered]
