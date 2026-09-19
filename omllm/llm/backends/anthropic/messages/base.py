from omcore import lang
from omcore.http import all as http
from omcore.secrets import all as sec

from ....types.models import Model
from ...base.http import BaseHttpBackend
from ...base.http import HttpErrorDetails
from .errors import is_anthropic_context_overflow_error


##


class BaseAnthropicMessagesBackend(BaseHttpBackend, lang.Abstract):
    def __init__(
            self,
            model: Model,
            *,
            api_key: sec.Secret | None = None,
            http_client: http.AsyncHttpClient | None = None,
            base_url: str | None = None,
    ) -> None:
        super().__init__(
            model,
            api_key=api_key,
            http_client=http_client,
            base_url=base_url,
        )

    def _is_context_overflow_http_error(self, error: HttpErrorDetails) -> bool:
        return is_anthropic_context_overflow_error(error)
