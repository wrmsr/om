from omcore import lang

from ...search import WebSearcher
from ...search import WebSearchHit
from ...search import WebSearchRequest
from ...search import WebSearchResult


with lang.auto_proxy_import(globals()):
    import ddgs


##


# @om-manifest $.core.registry.manifests.RegistryManifest(
#     name='duckduckgo',
#     aliases=['ddg'],
#     type='WebSearcher',
# )
class DuckduckgoWebSearcher(WebSearcher):
    async def search(self, request: WebSearchRequest) -> WebSearchResult:
        dsch = ddgs.DDGS()
        res = dsch.text(request.query)
        return WebSearchResult(
            hits=[
                WebSearchHit(
                    title=d.get('title'),
                    url=d.get('href'),
                    description=d.get('description'),
                    snippets=[body] if (body := d.get('body')) is not None else None,
                )
                for d in res
            ],
        )
