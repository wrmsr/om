import typing as ta

from omcore import check

from ....types.compat import TokenCostMode
from ....types.messages import StopReason
from ....types.messages import TokenCost
from ....types.messages import TokenUsage


##


def _translate_openrouter_token_cost(m: ta.Mapping[str, ta.Any]) -> TokenCost | None:
    raw_total = check.isinstance(m.get('cost'), (int, float, None))

    raw_input: int | float | None = None
    raw_output: int | float | None = None
    if (raw_details := check.isinstance(m.get('cost_details'), (ta.Mapping, None))) is not None:
        raw_input = check.isinstance(raw_details.get('upstream_inference_prompt_cost'), (int, float, None))
        raw_output = check.isinstance(raw_details.get('upstream_inference_completions_cost'), (int, float, None))

    if raw_total is None and raw_input is None and raw_output is None:
        return None

    # Reported figures pass through as billed - including a legitimate 0.0, such as for free models or byok requests.
    # No cache-level breakdown is reported, only the prompt/completions split.
    return TokenCost(
        source='reported',
        input=float(raw_input) if raw_input is not None else None,
        output=float(raw_output) if raw_output is not None else None,
        total=float(raw_total) if raw_total is not None else None,
    )


def translate_token_usage(
        m: ta.Mapping[str, ta.Any],
        *,
        cost_mode: TokenCostMode | None = None,
) -> TokenUsage:
    raw_ptd = check.isinstance(m.get('prompt_tokens_details'), (ta.Mapping, None))
    raw_ctd = check.isinstance(m.get('completion_tokens_details'), (ta.Mapping, None))

    cost: TokenCost | None = None
    if cost_mode == 'openrouter':
        cost = _translate_openrouter_token_cost(m)
    elif cost_mode is not None:
        raise ValueError(cost_mode)

    return TokenUsage(
        input=check.isinstance(m.get('prompt_tokens'), (int, None)),
        output=check.isinstance(m.get('completion_tokens'), (int, None)),
        reasoning=check.isinstance(raw_ctd.get('reasoning_tokens'), (int, None)) if raw_ctd is not None else None,
        cache_read=check.isinstance(raw_ptd.get('cached_tokens'), (int, None)) if raw_ptd is not None else None,
        cache_write=check.isinstance(raw_ptd.get('cache_write_tokens'), (int, None)) if raw_ptd is not None else None,
        total=check.isinstance(m.get('total_tokens'), (int, None)),
        cost=cost,
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
