import re
import typing as ta

from ...base.http import HttpErrorDetails


##


# Anthropic uses invalid_request_error for many unrelated failures: malformed tool history, unsupported parameters,
# invalid thinking-block signatures, spend limits, and oversized prompts can all share that type. It therefore is not
# sufficient by itself. These expressions describe complete messages observed from the direct Messages API rather
# than looking for suggestive words anywhere in the response body.
#
# There are three generations of the provider wording in active clients and captured API responses:
#
#   prompt is too long: 200680 tokens > 200000 maximum
#   input length and `max_tokens` exceed context limit: 197089 + 21333 > 200000, ...
#   Request size exceeds model context window
#
# The numeric forms accept comma separators but otherwise match the complete sentence. The last form sounds broad in
# isolation, but is constrained by Anthropic's error envelope, invalid-request type, and 400/413 status. In particular,
# the documented 413 request-size error for exceeding the HTTP byte limit has different wording and is not recoverable
# by pruning model context, so it must remain an ordinary BackendError.
_CONTEXT_OVERFLOW_MESSAGE_RES: ta.Final[ta.Sequence[re.Pattern[str]]] = (
    re.compile(
        r'prompt is too long(?:: [\d,]+ tokens > [\d,]+ maximum)?\.?',
        re.IGNORECASE,
    ),
    re.compile(
        r'input length and `max_tokens` exceed context limit: '
        r'[\d,]+ \+ [\d,]+ > [\d,]+, decrease input length or `max_tokens` and try again\.?',
        re.IGNORECASE,
    ),
    re.compile(
        r'request size exceeds model context window\.?',
        re.IGNORECASE,
    ),
)


def is_anthropic_context_overflow_error(error: HttpErrorDetails) -> bool:
    """Recognizes only Anthropic's invalid-request envelopes whose complete message denotes model-context overflow."""

    return (
        error.http_status in (400, 413) and
        error.error_type == 'invalid_request_error' and
        error.message is not None and
        any(pattern.fullmatch(error.message) is not None for pattern in _CONTEXT_OVERFLOW_MESSAGE_RES)
    )
