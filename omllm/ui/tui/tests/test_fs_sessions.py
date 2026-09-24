import os.path
import tempfile

import pytest

from omcore import inject as inj

from .... import harness as har
from ....agent.tests.scripted import text_message
from ..config import Config
from .headless import bind_headless_tui
from .headless import bind_scripted_backend
from .headless import headless_tui


##


@pytest.mark.asyncs('asyncio')
async def test_fs_session_resume():
    with tempfile.TemporaryDirectory() as temp_dir:
        session_dir = os.path.join(temp_dir, 'session')

        def bind(*turns, resume=None):
            return inj.override(
                bind_headless_tui(Config(model='scripted', immediate=True, jsonl=True, resume=resume)),
                bind_scripted_backend(*turns),
                inj.bind(har.FsSessionStorage.Config(dir_path=session_dir)),
            )

        async with headless_tui(bind(text_message('hello'))) as tui:
            await tui.session.prompt('hi')
            session_id = tui.session.id

        async with headless_tui(bind(text_message('continued'), resume=session_id.v)) as tui:
            assert tui.session.id == session_id
            assert len(tui.agent.state.context.messages or ()) == 2

            await tui.session.prompt('again')

            assert len(tui.agent.state.context.messages or ()) == 4
            storage = await tui.injector[har.FsSessionStorage]
            assert len(await storage.get_entries()) == 4

        with open(os.path.join(session_dir, har.FsSessionStorage.ENTRIES_FILE_NAME), encoding='utf-8') as f:  # noqa
            assert len(f.readlines()) == 4
