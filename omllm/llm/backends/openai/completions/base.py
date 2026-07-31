from omcore import check
from omcore import lang
from omcore.http import all as http
from omcore.secrets import all as sec

from ....types.compat import OpenaiCompat
from ....types.models import Model
from ...base.http import BaseHttpBackend


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
            self._compat = check.isinstance(model.compat, OpenaiCompat)
        else:
            self._compat = OpenaiCompat()
