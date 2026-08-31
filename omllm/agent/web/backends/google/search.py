"""
https://developers.google.com/custom-search/vo1/reference/rest/v1/cse/list?apix=true
https://developers.google.com/custom-search/v1/reference/rest/v1/Search
https://google.aip.dev/127
"""
import urllib.parse

from omcore import check
from omcore import marshal as msh
from omcore.formats.json import all as json
from omcore.http import all as http
from omcore.secrets import all as sec

from ...search import WebSearcher
from ...search import WebSearchHit
from ...search import WebSearchRequest
from ...search import WebSearchResult
from . import protocol as pt


##


# @om-manifest $.core.registry.manifests.RegistryManifest(
#     name='google-cse',
#     type='$.agent.web.search.WebSearcher',
# )
class GoogleCseWebSearcher(WebSearcher):
    def __init__(
            self,
            *,
            cse_id: str | None = None,
            cse_api_key: sec.Secret | None = None,

            http_client: http.AsyncHttpClient | None = None,
    ) -> None:
        super().__init__()

        self._cse_id = cse_id
        self._cse_api_key = cse_api_key

        self._http_client = http_client

    async def search(self, request: WebSearchRequest) -> WebSearchResult:
        qs = urllib.parse.urlencode(dict(
            key=check.not_none(self._cse_api_key).reveal(),
            cx=check.non_empty_str(self._cse_id),
            q=request.query,
        ))
        resp = await http.async_request(
            f'https://www.googleapis.com/customsearch/v1?{qs}',
            client=self._http_client,
        )
        out = check.not_none(resp.data)

        dct = json.loads(out.decode('utf-8'))
        res = msh.unmarshal(dct, pt.CseSearchResponse)
        return WebSearchResult(
            hits=[
                WebSearchHit(
                    title=i.title,
                    url=i.link,
                    snippets=[i.snippet],
                )
                for i in res.items or ()
            ],
            total_results=res.info.total_results if res.info is not None else None,
        )
