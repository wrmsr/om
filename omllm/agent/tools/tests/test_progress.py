import pytest

from omcore import dataclasses as dc

from .... import llm
from ...exec.tools.details import ExecToolResultDetails
from ...tests.tools import EchoToolParams
from ...types.progress import OutputToolProgressUpdate
from ...types.progress import ToolProgressSink
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ...types.tools import ToolResult
from ..classes import ToolClass
from ..reflect import reflect_tool_fn


##


class _RecordingSink(ToolProgressSink):
    def __init__(self) -> None:
        super().__init__()

        self.updates: list = []

    async def report(self, update):
        self.updates.append(update)


@dc.dataclass(frozen=True)
class _CountParams:
    n: int


async def _count(params: _CountParams, progress: ToolProgressSink) -> str:
    for i in range(params.n):
        await progress.report(OutputToolProgressUpdate(str(i)))
    return 'done'


@pytest.mark.asyncs('asyncio')
async def test_reflected_function_receives_the_contexts_sink():
    tool = reflect_tool_fn(ToolDescription('Counts.', dict(n='How far.')), _count)
    sink = _RecordingSink()

    result = await tool.executor(ToolContext(args={'n': 3}, progress=sink))

    assert result.content.text == 'done'
    assert [u.text for u in sink.updates] == ['0', '1', '2']


@pytest.mark.asyncs('asyncio')
async def test_reflected_function_gets_a_sink_even_when_nobody_listens():
    tool = reflect_tool_fn(ToolDescription('Counts.', dict(n='How far.')), _count)

    result = await tool.executor(ToolContext(args={'n': 2}))

    assert result.content.text == 'done'


@pytest.mark.asyncs('asyncio')
async def test_tool_class_may_return_a_full_result():
    details = ExecToolResultDetails(rc=0, stdout='x', stderr='')

    class Detailed(ToolClass[EchoToolParams]):
        name = 'detailed'
        params_cls = EchoToolParams
        description = ToolDescription('Details.', dict(text='Text.'))

        async def execute(self, ctx, params):
            return ToolResult(content=llm.TextContent(params.text), details=details)

    result = await Detailed().execute_context(ToolContext(args={'text': 'x'}))

    assert result.content.text == 'x'
    assert result.details is details
