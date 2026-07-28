from omcore import dataclasses as dc
from omcore import lang

from ..tools.reflect import reflect_tool_fn
from ..types.tools import Tool
from ..types.tools import ToolDescription


##


@dc.dataclass(frozen=True)
class GetWeatherParams:
    location: str


GET_WEATHER_DESCRIPTION = ToolDescription(
    'Get the weather in a given location.',
    dict(
        location='The city and state, e.g. San Francisco, CA.',
    ),
)


async def get_weather(params: GetWeatherParams) -> str:
    if 'edinburgh' in params.location.lower():
        return 'The weather in Edinburgh, Scotland is sunny.'

    else:
        return 'Invalid location'


@lang.cached_function
def weather_tool() -> Tool:
    return reflect_tool_fn(GET_WEATHER_DESCRIPTION, get_weather)
