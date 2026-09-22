import os.path
import tempfile

import pytest

from ..... import agent as agn
from ..... import llm
from ...entries import ContextProjectionSessionEntry
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

        projection = agn.ContextProjection(
            summary='The greeting.',
            first_kept_message_index=1,
            tool_results=(agn.ToolResultProjection(message_index=0, max_chars=10),),
        )

        async with storage:
            with pytest.raises(SessionNotFoundError):
                await storage.get_entries()
            assert not os.path.exists(session_dir)

            await storage.add_entry(
                MessageSessionEntry(llm.UserMessage('hi')),
                MessageSessionEntry(llm.AiMessage([llm.TextContent('hello')])),
                ContextProjectionSessionEntry(projection),
            )

            entries = await storage.get_entries()

        assert [type(entry) for entry in entries] == [
            MessageSessionEntry,
            MessageSessionEntry,
            ContextProjectionSessionEntry,
        ]
        first, second, third = entries
        assert isinstance(first, MessageSessionEntry)
        assert first.message == llm.UserMessage('hi')
        assert isinstance(second, MessageSessionEntry)
        assert isinstance(second.message, llm.AiMessage)
        assert tuple(second.message.content) == (llm.TextContent('hello'),)
        assert isinstance(third, ContextProjectionSessionEntry)
        assert third.projection == projection
