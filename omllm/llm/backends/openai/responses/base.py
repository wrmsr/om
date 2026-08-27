from omcore import cached
from omcore import check
from omcore import lang
from omcore.http import all as http
from omcore.secrets import all as sec

from ....types.compat import OpenaiResponsesCompat
from ....types.models import Model
from ...base.http import BaseHttpBackend


##


class BaseOpenaiResponsesBackend(BaseHttpBackend, lang.Abstract):
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
            self._compat = check.isinstance(model.compat, OpenaiResponsesCompat)
        else:
            self._compat = OpenaiResponsesCompat()

    @cached.property
    def _url(self) -> str:
        return self._base_url + lang.coalesce(self._compat.url_path, '/responses')
