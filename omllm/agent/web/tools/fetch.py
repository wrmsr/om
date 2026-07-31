import typing as ta
import urllib.parse

from omcore import check
from omcore import dataclasses as dc

from ...permissions.types import PermissionDecider
from ...permissions.url import UrlPermissionTarget
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ..fetching import WebFetcher
from ..fetching import page_to_text


##


MAX_CHARS: ta.Final = 50_000


@dc.dataclass(frozen=True)
class WebFetchParams:
    url: str


class WebFetchTool(ToolClass[WebFetchParams]):
    name: ta.Final = 'web_fetch'

    params_cls: ta.Final = WebFetchParams

    description: ta.Final = ToolDescription(
        'Fetches a web page and returns its content as text (HTML is reduced to readable text).',
        dict(
            url='The absolute URL to fetch.',
        ),
    )

    def __init__(
            self,
            *,
            permissions: PermissionDecider,
            fetcher: WebFetcher,
    ) -> None:
        super().__init__()

        self._permissions = permissions
        self._fetcher = fetcher

    async def execute(self, ctx: ToolContext, params: WebFetchParams) -> str:
        parsed_url = urllib.parse.urlparse(params.url)
        url = check.non_empty_str(urllib.parse.urlunparse(parsed_url))  # noqa

        await self._permissions.check_allowed(ctx, UrlPermissionTarget(url, method='GET'))

        page = await self._fetcher.fetch(url)
        if not (200 <= page.status < 300):
            raise ValueError(f'fetching {url!r} returned HTTP {page.status}')

        text = page_to_text(page)
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + '\n... (truncated)'
        return text
