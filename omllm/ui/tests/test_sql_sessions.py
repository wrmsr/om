"""The ui's own wiring of sql session storage, end to end but for the terminal: config to injector to a sqlite file."""
import os.path
import sqlite3
import tempfile
import uuid

import pytest

from omcore import inject as inj
from omcore import sql

from ... import agent as agn
from ... import llm
from ...agent.sessions.storage.orm.tests.scenarios import check_stored_transcript
from ...agent.tests.scripted import text_message
from ...agent.tests.scripted import tool_call_message
from ...agent.tests.tools import EchoTool
from ..config import UiConfig
from ..inject.tools import bind_agent_tool_class
from .headless import bind_headless_ui
from .headless import bind_scripted_backend
from .headless import headless_ui


##


def test_config_arguments():
    assert not UiConfig.parse_from_arguments([]).jsonl
    assert UiConfig.parse_from_arguments(['--jsonl']).jsonl

    session_id = uuid.uuid7()
    assert UiConfig.parse_from_arguments(['--resume', str(session_id)]).resume == session_id

    with pytest.raises(RuntimeError):  # noqa
        bind_headless_ui(UiConfig(
            model='scripted',
            jsonl=True,
            in_memory=True,
        ))

    with pytest.raises(RuntimeError):  # noqa
        bind_headless_ui(UiConfig(
            model='scripted',
            in_memory=True,
            resume=session_id,
        ))


@pytest.mark.asyncs('asyncio')
async def test_sql_sessions():
    db_path = os.path.join(tempfile.mkdtemp(), 'state', 'llm', 'sessions.db')
    db_sets = sql.DbSets({'sessions': sql.DbSet(
        writer=sql.DbSpec(
            'sessions',
            sql.DbFamilies.SQLITE,
            sql.be.sqlite.connecting.SqliteDbConfig(file_path=db_path),
        ),
        reader='writer',
    )})

    def bind(*turns, resume=None):
        return inj.as_elements(
            inj.override(
                bind_headless_ui(UiConfig(
                    model='scripted',
                    immediate=True,
                    resume=resume,
                )),
                bind_scripted_backend(*turns),
                inj.bind(db_sets),
            ),

            inj.bind(EchoTool, singleton=True),
            bind_agent_tool_class(EchoTool),
        )

    async with headless_ui(bind(
            tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'x'})),
            text_message('ok'),
            text_message('ok again'),
    )) as hui:
        storage = await hui.injector[agn.SessionStorage]
        assert isinstance(storage, agn.OrmSessionStorage)
        assert isinstance(await hui.injector[agn.Orm], agn.SqlOrm)

        await hui.agent.prompt('hi')
        await hui.agent.prompt('again')
        assert (await hui.injector[EchoTool]).calls == ['x']

        # A command is not the transcript's business, so none of storage's either.
        await hui.commands.parse('echo hi').run()

        assert len(await storage.get_entries()) == 6
        await check_stored_transcript(storage, hui.agent)

        first_session_id = hui.session.id

    # The next run of the ui is another session, in the same db.
    async with headless_ui(bind(text_message('hello'))) as hui:
        assert hui.session.id != first_session_id

        await hui.agent.prompt('hi')

        await check_stored_transcript(await hui.injector[agn.OrmSessionStorage], hui.agent)

        second_session_id = hui.session.id

    # A requested id restores its transcript into a fresh agent and appends to the same session.
    async with headless_ui(bind(text_message('resumed'), resume=first_session_id.v)) as hui:
        assert hui.session.id == first_session_id
        assert len(hui.agent.state.context.messages or ()) == 6
        resumed_storage = await hui.injector[agn.OrmSessionStorage]
        assert len(await resumed_storage.get_entries()) == 6

        await hui.agent.prompt('resuming')

        assert len(hui.agent.state.context.messages or ()) == 8
        await check_stored_transcript(resumed_storage, hui.agent)

    with sqlite3.connect(db_path) as conn:
        assert conn.execute('select id, num_entries from sessions order by id').fetchall() == [
            (str(first_session_id.v), 8),
            (str(second_session_id.v), 2),
        ]
