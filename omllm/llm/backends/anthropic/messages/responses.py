import typing as ta

from omcore import check

from ....types.messages import StopReason
from ....types.messages import TokenUsage


##


def translate_token_usage(m: ta.Mapping[str, ta.Any]) -> TokenUsage:
    input_tokens = check.isinstance(m.get('input_tokens'), (int, None))
    output_tokens = check.isinstance(m.get('output_tokens'), (int, None))
    cache_read = check.isinstance(m.get('cache_read_input_tokens'), (int, None))
    cache_write = check.isinstance(m.get('cache_creation_input_tokens'), (int, None))

    # No total is reported, and the reported input tokens exclude cached ones - the computed total includes everything.
    # No reasoning count is reported either - thinking tokens are folded into the output count.
    total: int | None = None
    if input_tokens is not None and output_tokens is not None:
        total = input_tokens + output_tokens + (cache_read or 0) + (cache_write or 0)

    return TokenUsage(
        input=input_tokens,
        output=output_tokens,
        cache_read=cache_read,
        cache_write=cache_write,
        total=total,
    )


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
