from omcore import dataclasses as dc
from omcore import lang

from .....core.asyncs.base import AsyncJob
from .....core.asyncs.base import AsyncJobRunner
from ...search import WebSearcher
from ...search import WebSearchHit
from ...search import WebSearchRequest
from ...search import WebSearchResult


with lang.auto_proxy_import(globals()):
    import ddgs


##


@dc.dataclass(frozen=True)
class _SearchJob(AsyncJob[WebSearchResult]):
    request: WebSearchRequest
    timeout_s: int

    def run(self) -> WebSearchResult:
        res = ddgs.DDGS(timeout=self.timeout_s).text(self.request.query, max_results=10)
        return WebSearchResult(hits=[
            WebSearchHit(
                title=d.get('title'),
                url=d.get('href'),
                description=d.get('description'),
                snippets=[body] if (body := d.get('body')) is not None else None,
            )
            for d in res
        ])


# @om-manifest $.core.registry.manifests.RegistryManifest(
#     name='duckduckgo',
#     aliases=['ddg'],
#     type='$.agent.web.search.WebSearcher',
# )
class DuckduckgoWebSearcher(WebSearcher):
    def __init__(self, *, job_runner: AsyncJobRunner | None = None, timeout_s: int = 15) -> None:
        super().__init__()

        self._job_runner = job_runner
        self._timeout_s = timeout_s

    async def search(self, request: WebSearchRequest) -> WebSearchResult:
        job = _SearchJob(request, self._timeout_s)
        if self._job_runner is not None:
            return await self._job_runner.run(job, timeout=self._timeout_s)
        return job.run()
