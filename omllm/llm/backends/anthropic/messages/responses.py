import typing as ta

from omcore import check

from ....types.messages import StopReason
from ....types.messages import TokenUsage


##


def translate_token_usage(m: ta.Mapping[str, ta.Any]) -> TokenUsage:
    uncached_input_tokens = check.isinstance(m.get('input_tokens'), (int, None))
    output_tokens = check.isinstance(m.get('output_tokens'), (int, None))
    cache_read = check.isinstance(m.get('cache_read_input_tokens'), (int, None))
    cache_write = check.isinstance(m.get('cache_creation_input_tokens'), (int, None))
    raw_output_details = check.isinstance(m.get('output_tokens_details'), (ta.Mapping, None))

    input_tokens: int | None = None
    if uncached_input_tokens is not None:
        input_tokens = uncached_input_tokens + (cache_read or 0) + (cache_write or 0)

    # Anthropic does not report a total. Its raw input_tokens field excludes cache reads and writes, while output_tokens
    # is already the inclusive billed output total.
    total: int | None = None
    if input_tokens is not None and output_tokens is not None:
        total = input_tokens + output_tokens

    return TokenUsage(
        input=input_tokens,
        output=output_tokens,
        reasoning=(
            check.isinstance(raw_output_details.get('thinking_tokens'), (int, None))
            if raw_output_details is not None
            else None
        ),
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
