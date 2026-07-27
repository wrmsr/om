from omcore import check

from ... import llm
from ..types.tools import Tool
from ..types.tools import ToolContext
from ..types.tools import ToolResult


##


async def execute_weather_tool(ctx: ToolContext) -> ToolResult:
    location = check.non_empty_str(ctx.args['location'])

    if 'edinburgh' in location.lower():
        return ToolResult(content=llm.TextContent('The weather in Edinburgh, Scotland is sunny.'))

    else:
        return ToolResult(content=llm.TextContent('Invalid location'))


WEATHER_TOOL = Tool(
    llm_tool=llm.Tool(
        name='get_weather',
        description='Get the weather in a given location',
        params=[
            llm.ToolParam(
                name='location',
                description='The city and state, e.g. San Francisco, CA',
                type='string',
            ),
        ],
    ),
    executor=execute_weather_tool,
)
