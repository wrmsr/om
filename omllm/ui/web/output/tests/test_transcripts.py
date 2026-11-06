from ..... import agent as agn
from ..... import llm
from ...feed import events as fe
from ...feed.feed import Feed
from ..transcripts import feed_transcript


def test_transcript():
    feed = Feed()

    feed_transcript(feed, [
        llm.UserMessage('hi'),
        llm.AiMessage([
            llm.TextContent('looking'),
            llm.ToolCall('c1', 'ls', {'dir_path': '/'}),
        ]),
        llm.ToolResultMessage(tool_call_id='c1', tool_name='ls', content=[llm.TextContent('a\nb')]),
        llm.AiMessage([llm.TextContent('done')]),
        agn.InfoAgentMessage('noted'),
        llm.UserMessage('bye'),
    ])

    assert [e.event for e in feed.entries_after(0)] == [
        fe.UserMessageFeedEvent(text='hi'),
        fe.RunStartFeedEvent(),
        fe.AiTextFeedEvent(text='looking'),
        fe.ToolStartFeedEvent(key='c1', name='ls', args={'dir_path': '/'}),
        fe.ToolEndFeedEvent(key='c1', ok=True, result='a\nb'),
        fe.AiTextFeedEvent(text='done'),
        fe.NoticeFeedEvent(text='noted'),
        fe.RunEndFeedEvent(reason='completed'),
        fe.UserMessageFeedEvent(text='bye'),
    ]
