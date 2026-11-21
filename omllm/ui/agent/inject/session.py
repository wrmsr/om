import os.path
import uuid

from omcore import check
from omcore import inject as inj
from omcore import sql
from omdev.home.paths import get_home_paths

from .... import agent as agn
from ....agent.sessions.storage.orm.inject import bind_asyncio_sqlite_orm
from ....agent.sessions.storage.orm.inject import bind_orm_session_storage
from ..config import AgentConfig


##


def _state_dir_path() -> str:
    return os.path.join(get_home_paths().state_dir, 'llm')


def bind_session_infrastructure(config: AgentConfig) -> inj.Elements:
    """
    Host-level session storage infrastructure shared across agents: for SQLite ORM sessions, one database and ORM
    registry serve every session in the host process.
    """

    check.arg(not (config.in_memory and config.jsonl), 'Session storage is in memory or in jsonl, not both')
    check.arg(not (config.in_memory and config.resume is not None), 'An in-memory session cannot be resumed')

    if config.in_memory or config.jsonl:
        return inj.as_elements()

    # One db for every session, unlike the directory each gets otherwise.
    return inj.as_elements(
        bind_asyncio_sqlite_orm(sql.be.sqlite.connecting.SqliteDbConfig(
            file_path=os.path.join(_state_dir_path(), 'sessions.db'),
        )),
    )


def bind_agent_session(config: AgentConfig) -> inj.Elements:
    """Per-agent session bindings: `SessionId`, `SessionStorage`, and `Session`."""

    lst: list[inj.Elemental] = []

    #

    session_id = agn.SessionId(config.resume if config.resume is not None else uuid.uuid7())

    lst.extend([
        inj.bind(session_id),

        inj.bind(agn.Session, singleton=True),
    ])

    #

    check.arg(not (config.in_memory and config.jsonl), 'Session storage is in memory or in jsonl, not both')
    check.arg(not (config.in_memory and config.resume is not None), 'An in-memory session cannot be resumed')

    if config.in_memory:
        lst.extend([
            inj.bind(agn.InMemorySessionStorage()),
            inj.bind(agn.SessionStorage, to_key=agn.InMemorySessionStorage),
        ])

    elif config.jsonl:
        lst.extend([
            inj.bind(agn.FsSessionStorage.Config(
                dir_path=os.path.join(_state_dir_path(), 'sessions', str(session_id.v)),
            )),
            inj.bind(
                agn.FsSessionStorage,
                singleton=True,
                to_async_fn=inj.make_async_managed_provider(agn.FsSessionStorage),
            ),
            inj.bind(agn.SessionStorage, to_key=agn.FsSessionStorage),
        ])

    else:
        lst.append(bind_orm_session_storage())

    #

    return inj.as_elements(*lst)
