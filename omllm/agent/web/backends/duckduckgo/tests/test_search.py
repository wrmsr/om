import pytest

from omcore import lang
from omcore.testing import pytest as ptu

from ......core.registry.globals import registry_new
from ....search import WebSearcher
from ....search import WebSearchRequest
from ..search import DuckduckgoWebSearcher


@ptu.skip.if_cant_import('ddgs')
@pytest.mark.online
def test_search():
    import ddgs.exceptions

    try:
        res = lang.sync_await(DuckduckgoWebSearcher().search(WebSearchRequest('the disco biscuits')))
    except (ddgs.exceptions.RatelimitException, TimeoutError) as e:
        print(e)
        return

    print(res)
    assert res


@ptu.skip.if_cant_import('ddgs')
def test_manifest():
    svc = registry_new(WebSearcher, 'ddg')
    assert isinstance(svc, DuckduckgoWebSearcher)
