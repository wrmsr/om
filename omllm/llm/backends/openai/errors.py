import re
import typing as ta

from ..base.http import HttpErrorDetails


##


# OpenAI's native APIs put the actionable reason in error.code. Several OpenAI-compatible servers put the same value
# in error.type instead, so both named fields are accepted. These are exact protocol identifiers, not words searched
# for in a human-readable message. A new identifier therefore fails closed until it is deliberately added here.
_CONTEXT_OVERFLOW_CODES: ta.Final[ta.AbstractSet[str]] = frozenset({
    'context_length_exceeded',
    'context_window_exceeded',
    'max_context_length_exceeded',
    'prompt_too_long',
})


# OpenRouter normally returns a numeric error.code (usually 400), which says nothing more than the HTTP status. It
# routes to many independently implemented upstreams and does not document a symbolic context-overflow code. Its own
# router does, however, emit this stable numeric sentence before the provider-specific recommendation at the end:
#
#   This endpoint's maximum context length is 131072 tokens. However, you requested about 135349 tokens (...).
#
# Matching only that quantified prefix is intentional. The recommendation has changed from the old "middle-out"
# transform to the context-compression plugin and may change again. Conversely, matching a bare phrase such as
# "maximum context length" would recreate the global heuristic this module exists to remove. The classifier also
# requires the OpenRouter model provider and a client-error status, so this compatibility path cannot affect OpenAI,
# Groq, Cerebras, Ollama, or another OpenAI-shaped service.
_OPENROUTER_CONTEXT_OVERFLOW_RE: ta.Final = re.compile(
    r"^this endpoint['\N{RIGHT SINGLE QUOTATION MARK}]s maximum context length is [\d,]+ tokens\.\s+"
    r"however, you requested (?:about )?[\d,]+ tokens\b",
    re.IGNORECASE,
)


def _has_structured_context_overflow_code(error: HttpErrorDetails) -> bool:
    return any(
        isinstance(value, str) and value.casefold() in _CONTEXT_OVERFLOW_CODES
        for value in (error.code, error.error_type)
    )


def is_openai_context_overflow_error(error: HttpErrorDetails, *, provider: str) -> bool:
    """
    Classifies context overflow for OpenAI and the explicitly supported OpenAI-compatible model providers.

    Symbolic protocol codes are authoritative regardless of provider: this is the useful part of the compatibility
    contract. Message interpretation is deliberately *not* part of that generic contract. The only exception is the
    known OpenRouter router sentence above, selected by the model's provider rather than by whichever hostname or
    upstream happened to answer this request.
    """

    if _has_structured_context_overflow_code(error):
        return True

    return (
        provider == 'openrouter' and
        error.http_status in (400, 413) and
        error.message is not None and
        _OPENROUTER_CONTEXT_OVERFLOW_RE.match(error.message) is not None
    )
