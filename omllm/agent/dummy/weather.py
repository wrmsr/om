from omcore import lang

from ..tools.reflect import reflect_tool
from ..types.tools import Tool


##


async def get_weather(location: str) -> str:
    """
    Get the weather in a given location.

    Args:
        location: The city and state, e.g. San Francisco, CA
    """

    if 'edinburgh' in location.lower():
        return 'The weather in Edinburgh, Scotland is sunny.'

    else:
        return 'Invalid location'


@lang.cached_function
def weather_tool() -> Tool:
    return reflect_tool(get_weather)
