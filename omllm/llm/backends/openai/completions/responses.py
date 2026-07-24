import typing as ta

from omcore import check

from ....types.messages import StopReason
from ....types.messages import TokenUsage


##


def translate_token_usage(m: ta.Mapping[str, ta.Any]) -> TokenUsage:
    raw_ptd = check.isinstance(m.get('prompt_tokens_details'), (ta.Mapping, None))
    raw_ctd = check.isinstance(m.get('completion_tokens_details'), (ta.Mapping, None))

    return TokenUsage(
        input=check.isinstance(m.get('prompt_tokens'), (int, None)),
        output=check.isinstance(m.get('completion_tokens'), (int, None)),
        reasoning=check.isinstance(raw_ctd.get('reasoning_tokens'), (int, None)) if raw_ctd is not None else None,
        # No cache write count is reported - caching is automatic.
        cache_read=check.isinstance(raw_ptd.get('cached_tokens'), (int, None)) if raw_ptd is not None else None,
        total=check.isinstance(m.get('total_tokens'), (int, None)),
    )


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
