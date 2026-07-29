import typing as ta

import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh
from omcore.formats.json import all as json
from omcore.http import all as http
from omcore.secrets.tests.harness import HarnessSecrets

from .. import protocol as pt


@dc.dataclass(frozen=True, kw_only=True)
class SearchHit(lang.Final):
    title: str | None
    url: str | None
    description: str | None = None
    snippets: lang.SequenceNotStr[str] | None = None


@dc.dataclass(frozen=True, kw_only=True)
class SearchHits(lang.Final):
    l: ta.Sequence[SearchHit]

    total_results: int | None = None


class TavilySearchService:
    def __init__(
            self,
            api_key: str,
            http_client: http.AsyncHttpClient | None = None,
    ) -> None:
        super().__init__()

        self._api_key = api_key
        self._http_client = http_client

    async def invoke(self, request: str) -> SearchHits:
        pt_request = pt.SearchRequest(
            query=request,
        )

        raw_request = msh.marshal(pt_request)

        http_response = await http.async_request(
            'https://api.tavily.com/search',
            headers={
                http.consts.HEADER_CONTENT_TYPE: http.consts.CONTENT_TYPE_JSON,
                http.consts.HEADER_AUTH: http.consts.format_bearer_auth_header(check.not_none(self._api_key)),
            },
            data=json.dumps(raw_request).encode('utf-8'),
            client=self._http_client,
        )

        raw_response = json.loads(check.not_none(http_response.data).decode('utf-8'))

        pt_response = msh.unmarshal(raw_response, pt.SearchResponse)

        return SearchHits(
            l=[
                SearchHit(
                    title=r.title,
                    url=r.url,
                )
                for r in pt_response.results or []
            ],
        )


@pytest.mark.skip_unless_alone
@pytest.mark.online
def test_search(harness):
    svc = TavilySearchService(
        harness[HarnessSecrets].get_or_skip('tavily_api_key').reveal(),
        http_client=http.SyncAsyncHttpClient(http.client()),
    )

    res = lang.sync_await(svc.invoke('the disco biscuits'))

    print(res)
    assert res
