import typing as ta

from omcore import dataclasses as dc

from ..tools.classes import ToolClass
from ..types.tools import ToolContext
from ..types.tools import ToolDescription


##


@dc.dataclass(frozen=True)
class GetWeatherParams:
    location: str


class GetWeatherTool(ToolClass[GetWeatherParams]):
    name: ta.Final = 'get_weather'

    params_cls: ta.Final = GetWeatherParams

    description: ta.Final = ToolDescription(
        'Get the weather in a given location.',
        dict(
            location='The city and state, e.g. San Francisco, CA.',
        ),
    )

    async def execute(self, ctx: ToolContext, params: GetWeatherParams) -> str:
        if 'edinburgh' in params.location.lower():
            return 'The weather in Edinburgh, Scotland is sunny.'

        else:
            return 'Invalid location'
