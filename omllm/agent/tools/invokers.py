from ..types.tools import Tool
from ..types.tools import ToolContext
from ..types.tools import ToolInvoker
from ..types.tools import ToolResult


##


class DirectToolInvoker(ToolInvoker):
    """Invokes the tool's executor directly, with nothing around it: what the loop does unless told otherwise."""

    async def invoke_tool(self, tool: Tool, ctx: ToolContext) -> ToolResult:
        return await tool.executor(ctx)
