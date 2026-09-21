import os.path
import tempfile

import pytest

from ..... import llm
from ...entries import MessageSessionEntry
from ..fs import FsSessionStorage
from ..types import SessionNotFoundError


##


@pytest.mark.asyncs('asyncio')
async def test_fs_session_storage_reads_entries():
    with tempfile.TemporaryDirectory() as temp_dir:
        session_dir = os.path.join(temp_dir, 'session')
        storage = FsSessionStorage(FsSessionStorage.Config(
            dir_path=session_dir,
        ))

        async with storage:
            with pytest.raises(SessionNotFoundError):
                await storage.get_entries()
            assert not os.path.exists(session_dir)

            await storage.add_entry(
                MessageSessionEntry(llm.UserMessage('hi')),
                MessageSessionEntry(llm.AiMessage([llm.TextContent('hello')])),
            )

            entries = await storage.get_entries()

        assert [type(entry) for entry in entries] == [MessageSessionEntry, MessageSessionEntry]
        first, second = entries
        assert isinstance(first, MessageSessionEntry)
        assert first.message == llm.UserMessage('hi')
        assert isinstance(second, MessageSessionEntry)
        assert isinstance(second.message, llm.AiMessage)
        assert tuple(second.message.content) == (llm.TextContent('hello'),)
