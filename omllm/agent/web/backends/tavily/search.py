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
#     name='tavily',
#     type='$.agent.web.search.WebSearcher',
# )
class TavilyWebSearcher(WebSearcher):
    def __init__(
            self,
            *,
            api_key: sec.Secret | None = None,

            http_client: http.AsyncHttpClient | None = None,
    ) -> None:
        super().__init__()

        self._api_key = api_key
        self._http_client = http_client

    async def search(self, request: WebSearchRequest) -> WebSearchResult:
        pt_request = pt.SearchRequest(
            query=request.query,
        )

        raw_request = msh.marshal(pt_request)

        http_response = await http.async_request(
            'https://api.tavily.com/search',
            headers={
                http.consts.HEADER_CONTENT_TYPE: http.consts.CONTENT_TYPE_JSON,
                http.consts.HEADER_AUTH: http.consts.format_bearer_auth_header(check.not_none(self._api_key).reveal()),
            },
            data=json.dumps(raw_request).encode('utf-8'),
            client=self._http_client,
        )

        raw_response = json.loads(check.not_none(http_response.data).decode('utf-8'))

        pt_response = msh.unmarshal(raw_response, pt.SearchResponse)

        return WebSearchResult(
            hits=[
                WebSearchHit(
                    title=r.title,
                    url=r.url,
                )
                for r in pt_response.results or []
            ],
        )
