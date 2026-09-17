from omcore import lang
from omcore.http import all as http
from omcore.secrets import all as sec

from ....types.models import Model
from ...base.http import BaseHttpBackend
from ...base.http import HttpErrorDetails
from .errors import is_google_context_overflow_error


##


class BaseGoogleGenerativeBackend(BaseHttpBackend, lang.Abstract):
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

    def _is_context_overflow_http_error(self, error: HttpErrorDetails) -> bool:
        return is_google_context_overflow_error(error)
