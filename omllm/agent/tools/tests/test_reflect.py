from ...types.tools import ToolContext
from ..reflect import reflect_tool


def add_2(ctx: ToolContext, a: int, b: int) -> int:
    """Adds 2 integers."""

    return a + b


def test_reflect_tool():
    tool = reflect_tool(add_2)
    print(tool)
