from omcore import inject as inj

from .... import agent as agn
from ....agent.web.backends.duckduckgo.search import DuckduckgoWebSearcher
from ..config import Config


##


def bind_web(config: Config) -> inj.Elements:
    if not config.web:
        return inj.as_elements()

    return inj.as_elements(
        inj.bind(agn.HttpWebFetcher, singleton=True),
        inj.bind(agn.WebFetcher, to_key=agn.HttpWebFetcher),

        inj.bind(DuckduckgoWebSearcher, singleton=True),
        inj.bind(agn.WebSearcher, to_key=DuckduckgoWebSearcher),
    )
