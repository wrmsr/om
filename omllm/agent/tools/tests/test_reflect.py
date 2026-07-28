from omcore import dataclasses as dc

from ...types.tools import ToolDescription
from ..reflect import reflect_tool_fn


@dc.dataclass(frozen=True)
class Add2Params:
    a: int
    b: int


ADD2_DESCRIPTION = ToolDescription(
    'Adds 2 integers.',
)


def add2(params: Add2Params) -> int:
    return params.a + params.b


def test_reflect_tool():
    tool = reflect_tool_fn(ADD2_DESCRIPTION, add2)
    print(tool)
