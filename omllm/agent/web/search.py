import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True)
class WebSearchRequest(lang.Final):
    query: str


@dc.dataclass(frozen=True, kw_only=True)
class WebSearchHit(lang.Final):
    title: str | None
    url: str | None
    description: str | None = None
    snippets: lang.SequenceNotStr[str] | None = None


@dc.dataclass(frozen=True, kw_only=True)
class WebSearchResult(lang.Final):
    hits: ta.Sequence[WebSearchHit]

    total_results: int | None = None


# @om-manifest $.core.registry.manifests.RegistryTypeManifest
class WebSearcher(lang.Abstract):
    @abc.abstractmethod
    def search(self, request: WebSearchRequest) -> ta.Awaitable[WebSearchResult]:
        raise NotImplementedError
