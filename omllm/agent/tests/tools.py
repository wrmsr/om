"""Small tools for exercising the loop's tool handling offline."""
import typing as ta

from omcore import dataclasses as dc

from ... import llm
from ..tools.classes import ToolClass
from ..types.tools import Tool
from ..types.tools import ToolContext
from ..types.tools import ToolDescription
from ..types.tools import ToolExecutor


##


@dc.dataclass(frozen=True)
class EchoToolParams:
    text: str


class EchoTool(ToolClass[EchoToolParams]):
    """Returns its argument, and remembers every call it was actually executed with."""

    name: ta.Final = 'echo'

    params_cls: ta.Final = EchoToolParams

    description: ta.Final = ToolDescription(
        'Echoes the given text.',
        dict(
            text='The text to echo.',
        ),
    )

    def __init__(self) -> None:
        super().__init__()

        self.calls: list[str] = []

    async def execute(self, ctx: ToolContext, params: EchoToolParams) -> str:
        self.calls.append(params.text)
        return params.text


class RaisingTool(ToolClass[EchoToolParams]):
    name: ta.Final = 'raiser'

    params_cls: ta.Final = EchoToolParams

    description: ta.Final = ToolDescription(
        'Raises with the given text.',
        dict(
            text='The message to raise with.',
        ),
    )

    async def execute(self, ctx: ToolContext, params: EchoToolParams) -> str:
        raise ValueError(params.text)


##


def bare_tool(name: str, executor: ToolExecutor) -> Tool:
    """A tool with no class behind it: whatever the executor raises reaches the loop directly."""

    return Tool(
        llm_tool=llm.Tool(name=name),
        executor=executor,
    )
