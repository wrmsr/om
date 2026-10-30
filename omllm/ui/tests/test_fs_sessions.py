import os.path
import tempfile

import pytest

from omcore import inject as inj

from ... import agent as agn
from ...agent.tests.scripted import text_message
from ..config import UiConfig
from .headless import bind_headless_ui
from .headless import bind_scripted_backend
from .headless import headless_ui


##


@pytest.mark.asyncs('asyncio')
async def test_fs_session_resume():
    with tempfile.TemporaryDirectory() as temp_dir:
        session_dir = os.path.join(temp_dir, 'session')

        def bind(*turns, resume=None):
            return inj.override(
                bind_headless_ui(UiConfig(
                    model='scripted',
                    immediate=True,
                    jsonl=True,
                    resume=resume,
                )),
                bind_scripted_backend(*turns),
                inj.bind(agn.FsSessionStorage.Config(dir_path=session_dir)),
            )

        async with headless_ui(bind(text_message('hello'))) as hui:
            await hui.agent.prompt('hi')
            session_id = hui.session.id

        async with headless_ui(bind(text_message('continued'), resume=session_id.v)) as hui:
            assert hui.session.id == session_id
            assert len(hui.agent.state.context.messages or ()) == 2

            await hui.agent.prompt('again')

            assert len(hui.agent.state.context.messages or ()) == 4
            storage = await hui.injector[agn.FsSessionStorage]
            assert len(await storage.get_entries()) == 4

        with open(os.path.join(session_dir, agn.FsSessionStorage.ENTRIES_FILE_NAME), encoding='utf-8') as f:  # noqa
            assert len(f.readlines()) == 4
