import pytest

from omcore import lang
from omcore.http import all as http
from omcore.secrets.tests.harness import HarnessSecrets

from ....search import WebSearchRequest
from ..search import GoogleCseWebSearcher


@pytest.mark.online
def test_search(harness):
    sec = harness[HarnessSecrets]
    cse_id = sec.get_or_skip('google_cse_id')
    cse_api_key = sec.get_or_skip('google_cse_api_key')

    res = lang.sync_await(GoogleCseWebSearcher(
        cse_id=cse_id.reveal(),
        cse_api_key=cse_api_key,
        http_client=http.SyncAsyncHttpClient(http.client()),
    ).search(WebSearchRequest('lectures')))

    print(res)
    assert res.hits
