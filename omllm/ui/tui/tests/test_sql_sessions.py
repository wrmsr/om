"""The tui's own wiring of sql session storage, end to end but for the terminal: config to injector to a sqlite file."""
import os.path
import sqlite3
import tempfile

import pytest

from omcore import inject as inj

from .... import harness as har
from .... import llm
from ....agent.tests.scripted import text_message
from ....agent.tests.scripted import tool_call_message
from ....agent.tests.tools import EchoTool
from ....harness.sessions.storage.orm.tests.scenarios import check_stored_transcript
from ..config import Config
from ..inject import bind_agent_tool_class
from .headless import bind_headless_tui
from .headless import bind_scripted_backend
from .headless import headless_tui


##


def test_config_arguments():
    assert not Config.parse_from_arguments([]).sql
    assert Config.parse_from_arguments(['--sql']).sql

    with pytest.raises(RuntimeError):  # noqa
        bind_headless_tui(Config(model='scripted', sql=True, in_memory=True))


@pytest.mark.asyncs('asyncio')
async def test_sql_sessions():
    db_path = os.path.join(tempfile.mkdtemp(), 'state', 'llm', 'sessions.db')

    def bind(*turns):
        return inj.as_elements(
            inj.override(
                bind_headless_tui(Config(model='scripted', immediate=True, sql=True)),
                bind_scripted_backend(*turns),
                inj.bind(har.SqliteDbConfig(file_path=db_path)),
            ),

            inj.bind(EchoTool, singleton=True),
            bind_agent_tool_class(EchoTool),
        )

    async with headless_tui(bind(
            tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'x'})),
            text_message('ok'),
            text_message('ok again'),
    )) as tui:
        storage = await tui.injector[har.SessionStorage]
        assert isinstance(storage, har.OrmSessionStorage)
        assert isinstance(await tui.injector[har.Orm], har.SqlOrm)

        await tui.session.prompt('hi')
        await tui.session.prompt('again')
        assert (await tui.injector[EchoTool]).calls == ['x']

        # A command is the session's business but not the transcript's, so none of storage's either.
        await tui.session.prompt('/echo hi')

        assert len(await storage.get_entries()) == 6
        await check_stored_transcript(storage, tui.agent)

        first_session_id = tui.session.id

    # The next run of the tui is another session, in the same db.
    async with headless_tui(bind(text_message('hello'))) as tui:
        assert tui.session.id != first_session_id

        await tui.session.prompt('hi')

        await check_stored_transcript(await tui.injector[har.OrmSessionStorage], tui.agent)

    with sqlite3.connect(db_path) as conn:
        assert conn.execute('select id, num_entries from sessions order by id').fetchall() == [
            (str(first_session_id.v), 6),
            (str(tui.session.id.v), 2),
        ]
