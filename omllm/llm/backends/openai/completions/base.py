from omcore import cached
from omcore import check
from omcore import lang
from omcore.http import all as http
from omcore.secrets import all as sec

from ....types.compat import OpenaiCompletionsCompat
from ....types.models import Model
from ...base.http import BaseHttpBackend
from ...base.http import HttpErrorDetails
from ..errors import is_openai_context_overflow_error


##


class BaseOpenaiCompletionsBackend(BaseHttpBackend, lang.Abstract):
    def __init__(
            self,
            model: Model,
            *,
            api_key: sec.Secret | None = None,
            http_client: http.AsyncHttpClient | None = None,
    ) -> None:
        super().__init__(
            model,
            api_key=api_key,
            http_client=http_client,
        )

        if model.compat is not None:
            self._compat = check.isinstance(model.compat, OpenaiCompletionsCompat)
        else:
            self._compat = OpenaiCompletionsCompat()

    @cached.property
    def _url(self) -> str:
        return self._base_url + lang.coalesce(self._compat.url_path, '/chat/completions')

    def _is_context_overflow_http_error(self, error: HttpErrorDetails) -> bool:
        # The completions transport is shared by native OpenAI, Groq, Cerebras, Ollama, and OpenRouter models. Passing
        # the catalog provider is what lets the classifier retain exact-code compatibility for all of them while
        # confining OpenRouter's unavoidable message fallback to OpenRouter alone.
        return is_openai_context_overflow_error(error, provider=self._model.key_.provider)
