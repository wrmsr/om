import typing as ta

from omcore import check
from omcore.formats.json import all as json

from ....types.messages import StopReason
from ....types.messages import TokenUsage


##


def stringify_error(error: ta.Any) -> str:
    if isinstance(error, str):
        return error
    try:
        return json.dumps(error)
    except (TypeError, ValueError):
        return str(error)


##


def translate_token_usage(m: ta.Mapping[str, ta.Any]) -> TokenUsage:
    raw_itd = check.isinstance(m.get('input_tokens_details'), (ta.Mapping, None))
    raw_otd = check.isinstance(m.get('output_tokens_details'), (ta.Mapping, None))

    return TokenUsage(
        input=check.isinstance(m.get('input_tokens'), (int, None)),
        output=check.isinstance(m.get('output_tokens'), (int, None)),
        reasoning=check.isinstance(raw_otd.get('reasoning_tokens'), (int, None)) if raw_otd is not None else None,
        cache_read=check.isinstance(raw_itd.get('cached_tokens'), (int, None)) if raw_itd is not None else None,
        cache_write=check.isinstance(raw_itd.get('cache_write_tokens'), (int, None)) if raw_itd is not None else None,
        total=check.isinstance(m.get('total_tokens'), (int, None)),
    )


##


def translate_stop_reason(
        status: str,
        *,
        incomplete_reason: str | None = None,
        has_tool_calls: bool = False,
) -> StopReason:
    if status == 'completed':
        # There is no distinct tool-call status - it is inferred from the presence of function_call output items.
        return 'tool_use' if has_tool_calls else 'stop'

    elif status == 'incomplete':
        if incomplete_reason == 'max_output_tokens':
            return 'length'

        # Any other incompletion (such as content filtering) surfaces as an error-shaped stop.
        return 'error'

    # A failed response raises before translation - cancellation is the remaining terminal state, reachable only for
    # server-side cancellable (background) work, and error-shaped if it ever arrives here.
    elif status == 'cancelled':
        return 'error'

    else:
        raise ValueError(status)
