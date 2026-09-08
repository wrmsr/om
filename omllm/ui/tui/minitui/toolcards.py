from .... import agent as agn


##


_MAX_CALL_SUMMARY_LEN = 160


def tool_card_key(context: agn.ToolContext) -> str:
    if (tool_call := context.llm_tool_call) is not None:
        return tool_call.id
    return f'context:{id(context):x}'


def tool_call_summary(context: agn.ToolContext) -> str | None:
    if (tool := context.tool) is None or (summarizer := tool.summarizer) is None:
        return None

    try:
        summary = summarizer(context)
    except Exception:  # noqa: BLE001
        # FIXME: display error lol
        return None

    if not isinstance(summary, str):
        # FIXME: handle ui text lol
        raise TypeError(summary)

    if not (summary := ' '.join(summary.split())):
        return None

    if len(summary) > _MAX_CALL_SUMMARY_LEN:
        summary = summary[:_MAX_CALL_SUMMARY_LEN - 3] + '...'

    return summary
