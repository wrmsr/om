from omcore import cached
from omcore import check
from omcore import lang
from omcore.http import all as http
from omcore.secrets import all as sec

from ....types.compat import OpenaiResponsesCompat
from ....types.models import Model
from ...base.http import BaseHttpBackend
from ...base.http import HttpErrorDetails
from ..errors import is_openai_context_overflow_error


##


class BaseOpenaiResponsesBackend(BaseHttpBackend, lang.Abstract):
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

        if model.compat is not None:
            self._compat = check.isinstance(model.compat, OpenaiResponsesCompat)
        else:
            self._compat = OpenaiResponsesCompat()

    @cached.property
    def _url(self) -> str:
        return self._base_url + lang.coalesce(self._compat.url_path, '/responses')

    def _is_context_overflow_http_error(self, error: HttpErrorDetails) -> bool:
        # Responses models are native OpenAI today. Retaining the provider argument keeps the dispatch honest if an
        # OpenAI-compatible Responses endpoint is added later: it will receive exact-code support automatically, but no
        # provider-specific message fallback merely because it happens to share the wire format.
        return is_openai_context_overflow_error(error, provider=self._model.key_.provider)
