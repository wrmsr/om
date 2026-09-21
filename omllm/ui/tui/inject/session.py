import os.path
import uuid

from omcore import check
from omcore import inject as inj
from omdev.home.paths import get_home_paths

from .... import harness as har
from ....harness.sessions.storage.orm.inject import bind_asyncio_sqlite_orm
from ....harness.sessions.storage.orm.inject import bind_orm_session_storage
from ..config import Config


##


def bind_sessions(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    session_id = har.SessionId(config.resume if config.resume is not None else uuid.uuid7())

    lst.extend([
        inj.bind(session_id),

        inj.bind(har.Session, singleton=True),
    ])

    #

    check.arg(not (config.in_memory and config.sql), 'Session storage is in memory or in sql, not both')
    check.arg(not (config.in_memory and config.resume is not None), 'An in-memory session cannot be resumed')

    state_dir_path = os.path.join(get_home_paths().state_dir, 'llm')

    if config.sql:
        # One db for every session, unlike the directory each gets otherwise.
        lst.extend([
            bind_orm_session_storage(),

            bind_asyncio_sqlite_orm(har.SqliteDbConfig(
                file_path=os.path.join(state_dir_path, 'sessions.db'),
            )),
        ])

    elif not config.in_memory:
        lst.extend([
            inj.bind(har.FsSessionStorage.Config(
                dir_path=os.path.join(state_dir_path, 'sessions', str(session_id.v)),
            )),
            inj.bind(
                har.FsSessionStorage,
                singleton=True,
                to_async_fn=inj.make_async_managed_provider(har.FsSessionStorage),
            ),
            inj.bind(har.SessionStorage, to_key=har.FsSessionStorage),
        ])

    else:
        lst.extend([
            inj.bind(har.InMemorySessionStorage()),
            inj.bind(har.SessionStorage, to_key=har.InMemorySessionStorage),
        ])

    #

    return inj.as_elements(*lst)
