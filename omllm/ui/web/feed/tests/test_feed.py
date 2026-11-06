import asyncio

import pytest

from .. import events as fe
from ..feed import Feed


@pytest.mark.asyncs('asyncio')
async def test_feed():
    feed = Feed()
    assert feed.last_seq == 0
    assert feed.entries_after(0) == []

    changed = feed.changed()
    assert feed.changed() is changed
    assert not changed.done()

    assert feed.append(fe.RunStartFeedEvent(), fe.AiTextFeedEvent(text='hi')) == 2
    assert changed.done()

    assert [e.seq for e in feed.entries_after(0)] == [1, 2]
    assert [e.event for e in feed.entries_after(1)] == [fe.AiTextFeedEvent(text='hi')]
    assert feed.entries_after(2) == []

    # A reader which gives up waiting leaves the future be for the others.
    changed = feed.changed()
    done, _ = await asyncio.wait([changed], timeout=.01)
    assert not done
    assert feed.changed() is changed
