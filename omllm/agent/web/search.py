import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


##


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


class WebSearcher(lang.Abstract):
    @abc.abstractmethod
    def search(self, query: str) -> ta.Awaitable[WebSearchResult]:
        raise NotImplementedError
