import typing as ta

from omcore import check

from ....types.messages import StopReason
from ....types.messages import TokenUsage


##


def translate_token_usage(m: ta.Mapping[str, ta.Any]) -> TokenUsage:
    return TokenUsage(
        input=check.isinstance(m.get('promptTokenCount'), (int, None)),
        output=check.isinstance(m.get('candidatesTokenCount'), (int, None)),
        reasoning=check.isinstance(m.get('thoughtsTokenCount'), (int, None)),
        cache_read=check.isinstance(m.get('cachedContentTokenCount'), (int, None)),
        # Note: the reported total includes thoughts tokens, so it may exceed input + output.
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
