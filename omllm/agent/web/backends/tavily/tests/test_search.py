import pytest

from omcore import lang
from omcore.http import all as http
from omcore.secrets.tests.harness import HarnessSecrets

from ......core.registry.globals import registry_new
from ....search import WebSearcher
from ....search import WebSearchRequest
from ..search import TavilyWebSearcher


@pytest.mark.skip_unless_alone
@pytest.mark.online
def test_search(harness):
    svc = TavilyWebSearcher(
        api_key=harness[HarnessSecrets].get_or_skip('tavily_api_key'),
        http_client=http.SyncAsyncHttpClient(http.client()),
    )

    res = lang.sync_await(svc.search(WebSearchRequest('the disco biscuits')))

    print(res)
    assert res


def test_manifest():
    svc = registry_new(WebSearcher, 'tavily')
    assert isinstance(svc, TavilyWebSearcher)
