from ....types.messages import StopReason


##


def translate_stop_reason(s: str) -> StopReason:
    if s in ('end_turn', 'stop_sequence'):
        return 'stop'

    elif s in ('max_tokens', 'model_context_window_exceeded'):
        return 'length'

    elif s == 'tool_use':
        return 'tool_use'

    elif s == 'refusal':
        return 'error'

    else:
        raise ValueError(s)
