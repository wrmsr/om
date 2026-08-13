import io
import typing as ta

from omcore import dataclasses as dc

from ...permissions.types import PermissionDecider
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ..search import WebSearcher


##


MAX_SEARCH_RESULTS: ta.Final = 10


@dc.dataclass(frozen=True)
class WebSearchToolParams:
    query: str


class WebSearchTool(ToolClass[WebSearchToolParams]):
    name: ta.Final = 'web_search'

    params_cls: ta.Final = WebSearchToolParams

    description: ta.Final = ToolDescription(
        'Searches the web and returns a list of result titles, urls, and snippets.',
        dict(
            query='The search query.',
        ),
    )

    def __init__(
            self,
            *,
            permissions: PermissionDecider,
            searcher: WebSearcher,
    ) -> None:
        super().__init__()

        self._permissions = permissions
        self._searcher = searcher

    async def execute(self, ctx: ToolContext, params: WebSearchToolParams) -> str:
        # TODO: permission lol

        result = await self._searcher.search(params.query)

        out = io.StringIO()
        out.write('<results>\n')
        for h in list(result.hits)[:MAX_SEARCH_RESULTS]:
            out.write(f'- {h.title or "(untitled)"}\n')
            if h.url:
                out.write(f'  {h.url}\n')
            for sn in (h.snippets or ([h.description] if h.description else [])):
                out.write(f'  {sn}\n')
        out.write('</results>\n')

        return out.getvalue()
