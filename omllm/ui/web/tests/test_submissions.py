import pytest

from omcore import inject as inj

from .... import agent as agn
from ....agent.tests.scripted import scripted_backend
from ....agent.tests.scripted import text_message
from ..config import WebConfig
from ..feed import events as fe
from ..feed.feed import Feed
from ..inject import bind_web
from ..submissions import Submitter
from ..submissions import SubmitterBusyError


##


@pytest.mark.asyncs('asyncio')
async def test_cancelled_before_it_starts():
    async with inj.create_asyncio_managed_injector(
        inj.override(
            bind_web(WebConfig(in_memory=True, port=0)),
            inj.bind(agn.BackendManager, to_const=agn.DictBackendManager.of(scripted_backend(text_message('hi')))),
        ),
    ) as injector:
        submitter = await injector[Submitter]
        feed = await injector[Feed]

        # Cancelled before its task first runs, the submission never runs a line - and still ends, in the feed.
        sub = await submitter.submit('hi')
        assert submitter.cancel()
        await sub.join()

        ends = [e.event for e in feed.entries_after(0) if isinstance(e.event, fe.SubmissionEndFeedEvent)]
        assert ends == [fe.SubmissionEndFeedEvent(id=sub.id, status='cancelled')]

        # And the submitter is free again.
        assert not submitter.is_busy
        sub2 = await submitter.submit('/echo again')
        await sub2.join()

        # Whereas one submitted while another is running is turned away.
        sub3 = await submitter.submit('hi')
        with pytest.raises(SubmitterBusyError):
            await submitter.submit('hi')
        await sub3.join()
