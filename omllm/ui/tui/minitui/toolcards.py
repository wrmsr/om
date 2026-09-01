from .... import agent as agn


##


def tool_card_key(context: agn.ToolContext) -> str:
    if (tool_call := context.llm_tool_call) is not None:
        return tool_call.id
    return f'context:{id(context)}'
