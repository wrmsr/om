"""
TODO:
 - begin immediate vs deferred (per txn)
 - `conn.interrupt`
 - single-worker deadlock
"""
import concurrent.futures as cf
import contextlib
import logging
import os.path
import secrets
import typing as ta
import urllib.parse

from .... import check
from .... import dataclasses as dc
from .... import lang
from ... import api
from ...dbs.specs import DbLoc
from .adapters import sqlite_adapter


with lang.auto_proxy_import(globals()):
    import sqlite3


log = logging.getLogger(__name__)


##


SynchronousMode: ta.TypeAlias = ta.Literal[
    'off',
    'normal',
    'full',
]

TempStoreMode: ta.TypeAlias = ta.Literal[
    'default',
    'file',
    'memory',
]

JournalMode: ta.TypeAlias = ta.Literal[
    'wal',
    'delete',
]

AutoVacuumMode: ta.TypeAlias = ta.Literal[
    'none',
    'full',
    'incremental',
]


@dc.dataclass(frozen=True, kw_only=True)
class SqliteDbConfig(DbLoc):
    file_path: str

    # Open

    # 'rwc' creates a missing file - fully formed, built in a temp file and published with one atomic link - and
    # otherwise behaves as 'rw'. sqlite itself is never allowed to create the file, so a zero-byte one is never left
    # about. 'rw' is writable but the file must already exist. 'ro' is enforced by the os.
    mode: ta.Literal['rwc', 'rw', 'ro'] = 'rwc'

    # Skips locking entirely. Only for a file nothing will ever write to - not even a checkpoint from elsewhere.
    immutable: bool = False

    # Logical, per-connection read-only, enforced by sqlite however the file was opened. What in-process readers use.
    query_only: bool = False

    busy_timeout_s: float = 30.

    # Per-connection - none of these persist in the file, all are re-applied on every connect.

    foreign_keys: bool = True
    synchronous: SynchronousMode = 'normal'
    fullfsync: bool = False  # F_FULLFSYNC on every sync. Darwin only, a no-op elsewhere.
    checkpoint_fullfsync: bool = False  # F_FULLFSYNC on checkpoint syncs only. Darwin only.
    journal_size_limit: int | None = 64 << 20
    wal_autocheckpoint_pages: int | None = None  # None = sqlite's default (1000). 0 = never - run checkpoints yourself.
    mmap_size: int | None = None
    cache_size_kib: int | None = None
    temp_store: TempStoreMode = 'default'
    trusted_schema: bool = False
    double_quoted_strings: bool = False  # Double-quoted string literals. SQLITE_DBCONFIG_DQS_DDL and _DML.
    defensive: bool = False  # SQLITE_DBCONFIG_DEFENSIVE.

    # File-level - these persist in the file. Applied on creation, verified on every open.

    journal_mode: JournalMode | None = 'wal'  # None = leave as is, don't check.
    page_size: int | None = None  # Only takes on a file with no pages yet.
    auto_vacuum: AutoVacuumMode | None = None  # Likewise.
    application_id: int | None = None  # None = neither stamp nor check. An unstamped (0) file is adopted.

    # Lifecycle

    optimize: bool = True  # `pragma optimize=0x10002` on open, `pragma optimize` on close.
    analysis_limit: int = 1000  # Bounds the analyze that optimize may run. 100-1000 recommended.
    checkpoint_on_close: bool = True  # `pragma wal_checkpoint(truncate)` on close.
    min_sqlite_version: tuple[int, ...] = (3, 35)

    #

    @property
    def writable(self) -> bool:
        return self.mode != 'ro' and not self.immutable and not self.query_only

    # Defaults for a reader. Has no file_path - `dc.replace(SqliteDbConfig.READONLY, file_path=...)`.
    READONLY: ta.ClassVar[SqliteDbConfig]


SqliteDbConfig.READONLY = SqliteDbConfig(
    file_path='',

    mode='ro',
    query_only=True,  # Belt and braces - and keeps a replace(mode='rw') from quietly becoming a writer.

    foreign_keys=False,  # Nothing to enforce.
    synchronous='off',  # Nothing to sync.
    journal_size_limit=None,  # Couldn't truncate the wal anyway.
    wal_autocheckpoint_pages=0,  # Never commits so never checkpoints - just saying so.
    defensive=True,  # Costs a reader nothing.

    journal_mode=None,  # A reader doesn't get a say in the file's journal mode.

    optimize=False,  # Would want to write stat tables.
    checkpoint_on_close=False,
    min_sqlite_version=(3, 22),  # First able to open a wal db read-only.
)


##


_SYNCHRONOUS_MODES: ta.Mapping[SynchronousMode, int] = {
    'off': 0,
    'normal': 1,
    'full': 2,
}

_TEMP_STORE_MODES: ta.Mapping[TempStoreMode, int] = {
    'default': 0,
    'file': 1,
    'memory': 2,
}

_JOURNAL_MODES: ta.Mapping[JournalMode, str] = {
    'wal': 'wal',
    'delete': 'delete',
}

_AUTO_VACUUM_MODES: ta.Mapping[AutoVacuumMode, int] = {
    'none': 0,
    'full': 1,
    'incremental': 2,
}


def _pragma(conn: sqlite3.Connection, stmt: str) -> ta.Any:
    cur = conn.execute(f'pragma {stmt}')
    try:
        row = cur.fetchone()
    finally:
        cur.close()
    return row[0] if row is not None else None


def _dbconfig(conn: sqlite3.Connection, name: str, value: bool) -> None:
    try:
        op = getattr(sqlite3, f'SQLITE_DBCONFIG_{name}')
    except AttributeError:
        raise RuntimeError(f'sqlite {sqlite3.sqlite_version} has no SQLITE_DBCONFIG_{name}') from None  # noqa
    conn.setconfig(op, value)


def _sqlite_file_uri(abs_path: str, params: ta.Mapping[str, str]) -> str:
    uri = 'file://' + urllib.parse.quote(abs_path)  # Quotes the '?', '#' and '%' a plain path can't carry.
    if params:
        uri += '?' + urllib.parse.urlencode(params)
    return uri


##


def _setup_file_level(conn: sqlite3.Connection, config: SqliteDbConfig, *, writable: bool) -> None:
    if writable:
        if _pragma(conn, 'page_count') == 0:
            # These only take while no page has been written, and the first write transaction - which a switch to wal is
            # - fixes both. So they go here, before anything else, and are best effort: verified below, not guaranteed.
            if (ps := config.page_size) is not None:
                _pragma(conn, f'page_size = {check.isinstance(ps, int)}')
            if (av := config.auto_vacuum) is not None:
                _pragma(conn, f'auto_vacuum = {_AUTO_VACUUM_MODES[av]}')

        if (jm := config.journal_mode) is not None:
            # Persistent, so a write to the header. The first switch needs an exclusive lock: with any other connection
            # in a read transaction it waits out busy_timeout and then hands back the old mode. Thereafter it's a read.
            got = _pragma(conn, f'journal_mode = {_JOURNAL_MODES[jm]}')
            if got != jm:
                raise RuntimeError(f'Failed to set journal mode {jm!r}: {got!r}')  # noqa

        if (aid := config.application_id) is not None:
            got = _pragma(conn, 'application_id')
            if got == 0:
                _pragma(conn, f'application_id = {check.isinstance(aid, int)}')
            elif got != aid:
                raise RuntimeError(f'Not our file: application_id {got!r}, expected {aid!r}')  # noqa

    # Read it all back. For a writer this catches a creation-time pragma that didn't stick - someone else wrote page 1
    # first. For a reader it's the whole check.

    if (jm := config.journal_mode) is not None and not config.immutable:
        if (got := _pragma(conn, 'journal_mode')) != jm:
            raise RuntimeError(f'Journal mode is {got!r}, expected {jm!r}')  # noqa

    if (ps := config.page_size) is not None:
        if (got := _pragma(conn, 'page_size')) != ps:
            raise RuntimeError(f'Page size is {got!r}, expected {ps!r}')  # noqa

    if (av := config.auto_vacuum) is not None:
        if (got := _pragma(conn, 'auto_vacuum')) != _AUTO_VACUUM_MODES[av]:
            raise RuntimeError(f'Auto vacuum is {got!r}, expected {av!r}')  # noqa

    if (aid := config.application_id) is not None:
        got = _pragma(conn, 'application_id')
        if got != aid and not (got == 0 and not writable):  # A reader tolerates an unstamped file - it can't adopt it.
            raise RuntimeError(f'Not our file: application_id {got!r}, expected {aid!r}')  # noqa


def _apply_connection_pragmas(conn: sqlite3.Connection, config: SqliteDbConfig) -> None:
    # Silently a no-op if issued inside a transaction - autocommit keeps us out of one.
    _pragma(conn, f'foreign_keys = {int(config.foreign_keys)}')

    _pragma(conn, f'synchronous = {_SYNCHRONOUS_MODES[config.synchronous]}')
    _pragma(conn, f'fullfsync = {int(config.fullfsync)}')
    _pragma(conn, f'checkpoint_fullfsync = {int(config.checkpoint_fullfsync)}')

    if (jsl := config.journal_size_limit) is not None:
        _pragma(conn, f'journal_size_limit = {check.isinstance(jsl, int)}')

    if (wac := config.wal_autocheckpoint_pages) is not None:
        _pragma(conn, f'wal_autocheckpoint = {check.isinstance(wac, int)}')

    if (ms := config.mmap_size) is not None:
        _pragma(conn, f'mmap_size = {check.isinstance(ms, int)}')
        # Capped by the build's SQLITE_MAX_MMAP_SIZE, which may well be zero.
        if ms > 0 and not _pragma(conn, 'mmap_size'):
            raise RuntimeError('mmap is unavailable in this sqlite build')  # noqa

    if (cs := config.cache_size_kib) is not None:
        _pragma(conn, f'cache_size = -{check.isinstance(cs, int)}')

    _pragma(conn, f'temp_store = {_TEMP_STORE_MODES[config.temp_store]}')
    _pragma(conn, f'trusted_schema = {int(config.trusted_schema)}')


##


def _fsync_dir(dir_path: str) -> None:
    fd = os.open(dir_path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _publish_file(tmp_path: str, dst_path: str) -> bool:
    """
    Gives tmp_path the name dst_path without ever exposing a half-written file there. Returns whether it did - False
    means dst_path already existed, and the caller lost a race.
    """

    try:
        os.link(tmp_path, dst_path)  # The create-exclusive primitive: fails, atomically, if dst_path exists.

    except FileExistsError:
        return False

    except OSError:
        # No hard links on this filesystem. rename is just as atomic but on posix not exclusive - it would replace a
        # file that appeared since the caller looked. The re-check narrows that window, it can't close it.
        if os.path.exists(dst_path):
            return False
        try:
            os.rename(tmp_path, dst_path)
        except FileExistsError:
            return False

    _fsync_dir(os.path.dirname(dst_path))
    return True


def _create_sqlite_file(config: SqliteDbConfig, file_path: str) -> bool:
    """
    Builds a fully formed database file in private and publishes it in one step, so no one can ever open an empty or
    half-initialized one - and so the creation-time pragmas apply with no one to race. Returns whether this call was the
    one that created the file; the file exists afterwards either way.
    """

    dir_path, base_name = os.path.split(file_path)
    tmp_path = os.path.join(dir_path, f'.{base_name}.{os.getpid()}.{secrets.token_hex(4)}.tmp')

    # O_EXCL claims the name. Letting the os create it rather than mkstemp keeps sqlite's usual 0644 & ~umask, and a
    # zero-byte file is a valid empty db for sqlite to open.
    os.close(os.open(tmp_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644))

    try:
        conn = sqlite3.connect(tmp_path, autocommit=True)
        try:
            _setup_file_level(conn, config, writable=True)
        finally:
            conn.close()

        # The last connection's close checkpoints and removes the wal. One still here means that didn't happen, and
        # the file isn't to be trusted.
        if os.path.exists(tmp_path + '-wal'):
            raise RuntimeError(f'Wal left behind creating {file_path!r}')  # noqa

        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_path + '-shm')

        return _publish_file(tmp_path, file_path)

    finally:
        # A link leaves tmp_path as a second name for the published file, a rename leaves nothing, a loss or a failure
        # leaves the lot.
        for p in (tmp_path, tmp_path + '-wal', tmp_path + '-shm', tmp_path + '-journal'):
            with contextlib.suppress(FileNotFoundError):
                os.unlink(p)


##


def connect_sqlite(config: SqliteDbConfig) -> sqlite3.Connection:
    """Pair with close_sqlite - or use sqlite_connection - so the on-close lifecycle runs."""

    if sqlite3.sqlite_version_info < tuple(config.min_sqlite_version):
        raise RuntimeError(f'sqlite {sqlite3.sqlite_version} is older than required {config.min_sqlite_version}')  # noqa

    file_path = os.path.abspath(check.non_empty_str(config.file_path))
    writable = config.writable

    if config.mode == 'rwc':
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not os.path.exists(file_path):
            # Racing another creator is fine - exactly one wins, and the file exists afterwards either way.
            if not _create_sqlite_file(config, file_path):
                log.debug('Lost race creating %r', file_path)

    # Having created it ourselves if need be, sqlite is opened without permission to - so a file that vanishes between
    # here and the open is an error, not a fresh empty db.
    params: dict[str, str] = {'mode': 'ro' if config.mode == 'ro' else 'rw'}
    if config.immutable:
        params['immutable'] = '1'

    conn = sqlite3.connect(
        _sqlite_file_uri(file_path, params),
        uri=True,
        autocommit=True,  # Transactions are ours to begin, and the pragmas below that refuse to run inside one can run.
        timeout=config.busy_timeout_s,  # busy_timeout.
    )

    try:
        # Before any statement.
        _dbconfig(conn, 'DQS_DDL', config.double_quoted_strings)
        _dbconfig(conn, 'DQS_DML', config.double_quoted_strings)
        _dbconfig(conn, 'DEFENSIVE', config.defensive)

        if config.query_only:
            _pragma(conn, 'query_only = 1')

        _setup_file_level(conn, config, writable=writable)

        _apply_connection_pragmas(conn, config)

        if writable and config.optimize:
            _pragma(conn, f'analysis_limit = {check.isinstance(config.analysis_limit, int)}')
            _pragma(conn, 'optimize = 0x10002')

    except BaseException:
        conn.close()
        raise

    return conn


def close_sqlite(conn: sqlite3.Connection, config: SqliteDbConfig) -> None:
    try:
        # Not mid-transaction: the analyze would run inside it, and a checkpoint can't get past it.
        if config.writable and not conn.in_transaction:
            if config.optimize:
                _pragma(conn, 'optimize')

            if config.checkpoint_on_close:
                _pragma(conn, 'wal_checkpoint(truncate)')  # A straggling reader leaves this incomplete. That's fine.

    except sqlite3.Error:
        log.warning('Error closing sqlite connection %r', conn, exc_info=True)

    finally:
        conn.close()


@contextlib.contextmanager
def sqlite_connection(config: SqliteDbConfig) -> ta.Iterator[sqlite3.Connection]:
    conn = connect_sqlite(config)
    try:
        yield conn
    finally:
        close_sqlite(conn, config)


##


def sqlite_db(config: SqliteDbConfig) -> api.Db:
    return api.DbapiDb(
        lambda: sqlite_connection(config),

        # An orm session reads before it writes, so with other writers about its transactions have to be immediate. A
        # reader can't take the reserved lock that asks for at all, so it begins deferred - which is right for it
        # anyway, as it never needs to upgrade.
        adapter=sqlite_adapter(immediate=config.writable),
    )


@contextlib.asynccontextmanager
async def asyncio_sqlite_db(config: SqliteDbConfig) -> ta.AsyncIterator[api.AsyncDb]:
    """
    The db on a thread of its own, for as long as this is entered. It is one thread and not a pool of them as a sqlite
    connection is best kept to the thread which made it - and as everything sent its way then happens in the order it
    was sent, including the rollback of something cancelled midway.
    """

    with cf.ThreadPoolExecutor(max_workers=1, thread_name_prefix=__name__) as exe:
        yield api.SyncToAsyncDb(
            api.AsyncioToExecutorSyncToAsyncRunner.factory(exe),
            sqlite_db(config),
        )
