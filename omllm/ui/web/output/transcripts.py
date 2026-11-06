import typing as ta

from .... import agent as agn
from .... import llm
from ..feed import events as fe
from ..feed.feed import Feed
from ..tools import clip_json_strs
from .agents import AgentEventFeederLimits
from .agents import clip_text


##


def feed_transcript(
        feed: Feed,
        messages: ta.Sequence[agn.Message],
        *,
        limits: AgentEventFeederLimits | None = None,
) -> None:
    """
    Replays a stored transcript - a resumed session's - into the feed, as what it would have shown, clipped as it would
    have been.
    """

    limits = limits if limits is not None else AgentEventFeederLimits()

    run_open = False

    for message in messages:
        if isinstance(message, llm.UserMessage):
            if run_open:
                feed.append(fe.RunEndFeedEvent(reason='completed'))
                run_open = False

            user_content = message.content
            feed.append(fe.UserMessageFeedEvent(
                text=user_content if isinstance(user_content, str) else user_content.text,
            ))
            continue

        if not isinstance(message, (llm.AiMessage, llm.ToolResultMessage, agn.InfoAgentMessage)):
            continue

        if not run_open:
            feed.append(fe.RunStartFeedEvent())
            run_open = True

        if isinstance(message, llm.AiMessage):
            for ai_content in message.content:
                if isinstance(ai_content, llm.TextContent) and ai_content.text:
                    feed.append(fe.AiTextFeedEvent(text=ai_content.text))

                elif isinstance(ai_content, llm.ThinkingContent) and ai_content.text:
                    feed.append(fe.ThinkingEndFeedEvent(text=ai_content.text))

                elif isinstance(ai_content, llm.ToolCall):
                    feed.append(fe.ToolStartFeedEvent(
                        key=ai_content.id,
                        name=ai_content.name,
                        args=clip_json_strs(dict(ai_content.args), limits.max_arg_chars),
                    ))

        elif isinstance(message, llm.ToolResultMessage):
            feed.append(fe.ToolEndFeedEvent(
                key=message.tool_call_id,
                ok=not message.is_error,
                result=clip_text('\n'.join(content.text for content in message.content), limits.max_result_chars),
            ))

        elif isinstance(message, agn.InfoAgentMessage):
            feed.append(fe.NoticeFeedEvent(text=message.info))

    if run_open:
        feed.append(fe.RunEndFeedEvent(reason='completed'))
