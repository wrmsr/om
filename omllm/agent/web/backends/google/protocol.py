"""
https://developers.google.com/custom-search/vo1/reference/rest/v1/cse/list?apix=true
https://developers.google.com/custom-search/v1/reference/rest/v1/Search
https://google.aip.dev/127
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh


##


@dc.dataclass(frozen=True)
@msh.update_object_options(field_naming='low_camel', unknown_field='x')
class CseSearchResult(lang.Final):
    kind: str | None = None

    title: str | None = None
    html_title: str | None = None

    link: str | None = None
    display_link: str | None = None

    snippet: str | None = None
    html_snippet: str | None = None

    cache_id: str | None = None

    formatted_url: str | None = None
    html_formatted_url: str | None = None

    mime: str | None = None
    file_format: str | None = None

    x: ta.Mapping[str, ta.Any] | None = dc.field(default=None, repr=False)


@dc.dataclass(frozen=True)
@msh.update_object_options(field_naming='low_camel', unknown_field='x')
class CseSearchInfo(lang.Final):
    search_time: float | None = None
    total_results: int | None = None

    x: ta.Mapping[str, ta.Any] | None = dc.field(default=None, repr=False)


@dc.dataclass(frozen=True)
@msh.update_object_options(field_naming='low_camel', unknown_field='x')
class CseSearchResponse(lang.Final):
    kind: str | None = None
    info: CseSearchInfo | None = dc.xfield(None) | msh.dc_field_options(name='searchInformation')
    items: ta.Sequence[CseSearchResult] | None = None

    x: ta.Mapping[str, ta.Any] | None = dc.field(default=None, repr=False)
