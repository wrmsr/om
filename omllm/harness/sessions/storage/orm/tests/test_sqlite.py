import os.path
import sqlite3
import tempfile
import uuid

import pytest

from omcore import orm
from omcore import sql

from ....types import SessionId
from ...types import SessionNotFoundError
from ..models import OrmSession
from ..models import orm_mappers
from ..sql import SqlOrm
from ..sqlite import SqliteDbConfig
from ..sqlite import asyncio_sqlite_db
from ..storage import OrmSessionStorage
from .scenarios import check_orm_session_storage
from .scenarios import check_stored_transcript
from .scenarios import scripted_session
from .scenarios import text_message


def _sql_orm(db: sql.AsyncDb) -> SqlOrm:
    return SqlOrm(
        registry=orm.registry(*orm_mappers()),
        db=db,
        backend=sql.be.sqlite.backend.SqliteBackend(),
    )


@pytest.mark.asyncs('asyncio')
async def test_sqlite():
    config = SqliteDbConfig(file_path=os.path.join(tempfile.mkdtemp(), 'state', 'sessions.db'))

    async with asyncio_sqlite_db(config) as db, _sql_orm(db) as sql_orm:
        missing_session_id = SessionId(uuid.uuid7())
        with pytest.raises(SessionNotFoundError):
            await OrmSessionStorage(missing_session_id, sql_orm).get_entries()

        async with sql_orm.new_session():
            assert await orm.get(OrmSession, missing_session_id.v) is None

        await check_orm_session_storage(sql_orm)


@pytest.mark.asyncs('asyncio')
async def test_sqlite_db_is_created_shareable_and_reopens():
    config = SqliteDbConfig(file_path=os.path.join(tempfile.mkdtemp(), 'state', 'sessions.db'))
    assert not os.path.exists(config.file_path)

    # Entering the orm is enough to have a db there, schema and all, before anything is stored in it.
    async with asyncio_sqlite_db(config) as db, _sql_orm(db) as sql_orm:
        with sqlite3.connect(config.file_path) as conn:
            assert conn.execute('pragma journal_mode').fetchone() == ('wal',)
            tables = {n for [n] in conn.execute("select name from sqlite_master where type = 'table'")}
            assert tables == {'sessions', 'session_entries'}

        session, agent, storage = await scripted_session(sql_orm, text_message('hello'), text_message('hello again'))
        await session.prompt('hi')

    # What was stored is there for whoever opens the db next, and they add to it rather than start over.
    async with asyncio_sqlite_db(config) as db, _sql_orm(db) as sql_orm:
        storage = type(storage)(session.id, sql_orm)
        assert len(await storage.get_entries()) == 2
        await check_stored_transcript(storage, agent)

        other_session, other_agent, other_storage = await scripted_session(sql_orm, text_message('hello'))
        await other_session.prompt('hi')
        await check_stored_transcript(other_storage, other_agent)

    with sqlite3.connect(config.file_path) as conn:
        assert conn.execute('select count(*) from sessions').fetchone() == (2,)
        assert conn.execute('select count(*) from session_entries').fetchone() == (4,)
