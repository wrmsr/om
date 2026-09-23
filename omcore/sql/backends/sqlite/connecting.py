import concurrent.futures as cf
import contextlib
import os.path
import typing as ta

from .... import check
from .... import dataclasses as dc
from .... import lang
from ... import api
from .adapters import sqlite_adapter


with lang.auto_proxy_import(globals()):
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


def sqlite_db(config: SqliteDbConfig) -> api.Db:
    return api.DbapiDb(
        lambda: contextlib.closing(connect_sqlite(config)),  # noqa

        # An orm session reads before it writes, so with other writers about its transactions have to be immediate.
        adapter=sqlite_adapter(immediate=True),
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
