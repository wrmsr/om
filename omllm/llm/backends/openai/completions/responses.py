from ....types.messages import StopReason


##


def translate_stop_reason(s: str) -> StopReason:
    if s == 'stop':
        return 'stop'

    elif s == 'length':
        return 'length'

    elif s in ('tool_calls', 'function_call'):
        return 'tool_use'

    elif s == 'content_filter':
        return 'error'

    else:
        raise ValueError(s)
