import re
import typing as ta

from ...base.http import HttpErrorDetails


##


# GenerateContent represents context overflow as the same 400 / INVALID_ARGUMENT pair used for ordinary malformed
# requests. The message is the only remaining discriminator in the REST contract. Keep the match anchored to the full
# quantified sentence returned by the API: accepting a loose phrase such as "maximum number of tokens" could mistake
# an invalid maxOutputTokens parameter (or some future validation diagnostic) for reducible prompt pressure.
_INPUT_TOKEN_LIMIT_RE: ta.Final = re.compile(
    r'the input token count \([\d,]+\) exceeds the maximum number of tokens allowed \([\d,]+\)\.?',
    re.IGNORECASE,
)


def is_google_context_overflow_error(error: HttpErrorDetails) -> bool:
    """Recognizes Gemini GenerateContent's exact input-token overflow form and no other INVALID_ARGUMENT failure."""

    return (
        error.http_status == 400 and
        error.provider_status == 'INVALID_ARGUMENT' and
        error.message is not None and
        _INPUT_TOKEN_LIMIT_RE.fullmatch(error.message) is not None
    )
