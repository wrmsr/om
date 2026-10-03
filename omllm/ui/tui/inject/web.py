from omcore import inject as inj

from ....agent.web.backends.duckduckgo.search import DuckduckgoWebSearcher
from ....agent.web.fetching import HttpWebFetcher
from ....agent.web.fetching import WebFetcher
from ....agent.web.search import WebSearcher
from ..config import Config


##


def bind_web(config: Config) -> inj.Elements:
    if not config.web:
        return inj.as_elements()

    return inj.as_elements(
        inj.bind(HttpWebFetcher, singleton=True),
        inj.bind(WebFetcher, to_key=HttpWebFetcher),

        inj.bind(DuckduckgoWebSearcher, singleton=True),
        inj.bind(WebSearcher, to_key=DuckduckgoWebSearcher),
    )
