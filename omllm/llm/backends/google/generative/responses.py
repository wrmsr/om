import typing as ta

from omcore import check

from ....types.messages import StopReason
from ....types.messages import TokenUsage


##


def translate_token_usage(m: ta.Mapping[str, ta.Any]) -> TokenUsage:
    prompt_tokens = check.isinstance(m.get('promptTokenCount'), (int, None))
    tool_use_prompt_tokens = check.isinstance(m.get('toolUsePromptTokenCount'), (int, None))
    candidate_tokens = check.isinstance(m.get('candidatesTokenCount'), (int, None))
    reasoning_tokens = check.isinstance(m.get('thoughtsTokenCount'), (int, None))

    input_tokens: int | None = None
    if prompt_tokens is not None:
        input_tokens = prompt_tokens + (tool_use_prompt_tokens or 0)

    # A turn may be all reasoning - candidatesTokenCount is then omitted entirely while thoughtsTokenCount is still
    # reported, and the inclusive output total must still cover it.
    output_tokens: int | None = None
    if candidate_tokens is not None or reasoning_tokens is not None:
        output_tokens = (candidate_tokens or 0) + (reasoning_tokens or 0)

    return TokenUsage(
        input=input_tokens,
        output=output_tokens,
        reasoning=reasoning_tokens,
        cache_read=check.isinstance(m.get('cachedContentTokenCount'), (int, None)),
        total=check.isinstance(m.get('totalTokenCount'), (int, None)),
    )


##


def translate_stop_reason(s: str) -> StopReason:
    if s == 'STOP':
        # Google reports STOP even on tool-calling turns - callers must structurally override this to 'tool_use' when
        # function call parts are present.
        return 'stop'

    elif s == 'MAX_TOKENS':
        return 'length'

    elif s in (
            'SAFETY',
            'RECITATION',
            'LANGUAGE',
            'BLOCKLIST',
            'PROHIBITED_CONTENT',
            'SPII',
            'IMAGE_SAFETY',
            'OTHER',
            'MALFORMED_FUNCTION_CALL',
            'UNEXPECTED_TOOL_CALL',
            'TOO_MANY_TOOL_CALLS',
    ):
        return 'error'

    else:
        raise ValueError(s)
