"""
A sqlite file as the sql db of a `SqlOrm`, set up to be shared: the one file holds every session of every harness
running on the machine, and is read - and pruned - by whatever replicates it elsewhere, all at once.
"""
import contextlib
import os.path
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import sql


with lang.auto_proxy_import(globals()):
    import concurrent.futures as cf
    import sqlite3


##


@dc.dataclass(frozen=True, kw_only=True)
class SqliteDbConfig:
    file_path: str

    busy_timeout_s: float = 30.


def connect_sqlite(config: SqliteDbConfig) -> sqlite3.Connection:
    file_path = check.non_empty_str(config.file_path)

    if (dir_path := os.path.dirname(file_path)):
        os.makedirs(dir_path, exist_ok=True)

    conn = sqlite3.connect(
        file_path,
        autocommit=True,
        timeout=config.busy_timeout_s,
    )

    try:
        # Readers and the writer stay out of each other's way. This is a property of the file, and persists in it.
        mode = conn.execute('pragma journal_mode = wal').fetchone()[0]
        if mode != 'wal':
            raise RuntimeError(f'Failed to enable wal mode: {mode!r}')  # noqa

        # Under wal this still cannot corrupt the db - an os crash or power loss can at worst cost the last commits -
        # and it spares every commit an fsync.
        conn.execute('pragma synchronous = normal')

    except BaseException:
        conn.close()
        raise

    return conn


def sqlite_db(config: SqliteDbConfig) -> sql.Db:
    return sql.api.DbapiDb(
        lambda: contextlib.closing(connect_sqlite(config)),

        # An orm session reads before it writes, so with other writers about its transactions have to be immediate.
        adapter=sql.be.sqlite.adapters.sqlite_adapter(immediate=True),
    )


##


@contextlib.asynccontextmanager
async def asyncio_sqlite_db(config: SqliteDbConfig) -> ta.AsyncIterator[sql.AsyncDb]:
    """
    The db on a thread of its own, for as long as this is entered. It is one thread and not a pool of them as a sqlite
    connection is best kept to the thread which made it - and as everything sent its way then happens in the order it
    was sent, including the rollback of something cancelled midway.
    """

    with cf.ThreadPoolExecutor(max_workers=1, thread_name_prefix='sqlite-orm') as exe:
        yield sql.api.SyncToAsyncDb(
            sql.api.AsyncioToExecutorSyncToAsyncRunner.factory(exe),
            sqlite_db(config),
        )
