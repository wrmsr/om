import pytest

from omcore import check
from omcore.asyncs.asynclite import all as asl

from .... import llm
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.tools import EchoTool
from ...turns.loop import TurnLoop
from ...types.contexts import Context
from ...types.messages import AgentMessage
from ...types.messages import InfoAgentMessage
from ...types.tools import ToolSet
from ..builders import StandardLlmContextBuilder
from ..messages import TypeMapAgentMessageProjector
from ..types import AgentMessageProjector


##


class _NoteProjector(AgentMessageProjector):
    def __init__(self, prefix: str = 'note') -> None:
        super().__init__()

        self._prefix = prefix

    def project(self, message):
        return [llm.UserMessage(f'[{self._prefix}: {check.isinstance(message, InfoAgentMessage).info}]')]


def _user_texts(messages):
    return [m.content for m in messages if isinstance(m, llm.UserMessage)]


def test_agent_messages_are_invisible_by_default():
    ctx = Context(
        system_prompt='sys',
        messages=[
            llm.UserMessage('hi'),
            InfoAgentMessage('x'),
            llm.AiMessage([llm.TextContent('yo')]),
        ],
        tools=ToolSet([EchoTool().tool()]),
    )

    out = StandardLlmContextBuilder().build(ctx)

    assert out.system_prompt == 'sys'
    assert [type(m) for m in out.messages or []] == [llm.UserMessage, llm.AiMessage]
    assert [t.name for t in out.tools or []] == ['echo']


def test_an_empty_context_builds_empty():
    out = StandardLlmContextBuilder().build(Context())

    assert out.messages is None
    assert out.tools is None


def test_type_map_dispatches_nearest_class_first():
    info = InfoAgentMessage('x')

    by_base = TypeMapAgentMessageProjector({AgentMessage: _NoteProjector('base')})
    assert _user_texts(by_base.project(info)) == ['[base: x]']

    by_both = TypeMapAgentMessageProjector({
        AgentMessage: _NoteProjector('base'),
        InfoAgentMessage: _NoteProjector('exact'),
    })
    assert _user_texts(by_both.project(info)) == ['[exact: x]']

    assert TypeMapAgentMessageProjector().project(info) == ()


def test_projected_notes_merge_with_adjacent_user_turns():
    builder = StandardLlmContextBuilder(
        projector=TypeMapAgentMessageProjector({InfoAgentMessage: _NoteProjector()}),
    )

    out = builder.build(Context(messages=[
        llm.UserMessage('hi'),
        InfoAgentMessage('x'),
        llm.UserMessage('go'),
        llm.AiMessage([llm.TextContent('ok')]),
        InfoAgentMessage('y'),
    ]))

    assert [type(m) for m in out.messages or []] == [llm.UserMessage, llm.AiMessage, llm.UserMessage]
    assert _user_texts(out.messages or []) == ['hi\n\n[note: x]\n\ngo', '[note: y]']


@pytest.mark.asyncs('asyncio')
async def test_loop_sends_the_builders_view():
    seen: list = []

    def expect(inv):
        seen.append(inv.context)

    loop = TurnLoop(
        new_messages=[llm.UserMessage('hi')],
        context=Context(messages=[InfoAgentMessage('earlier')]),
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
        llm_backend=scripted_backend(llm.BackendScriptTurn(text_message('ok'), expect=expect)),
        context_builder=StandardLlmContextBuilder(
            projector=TypeMapAgentMessageProjector({InfoAgentMessage: _NoteProjector()}),
        ),
    )

    result = await loop.run()

    # The transcript keeps the agent message as it was; the model saw it rendered and merged into the prompt.
    assert [type(m) for m in result.context.messages or []] == [InfoAgentMessage, llm.UserMessage, llm.AiMessage]
    [llm_ctx] = seen
    assert _user_texts(llm_ctx.messages or []) == ['[note: earlier]\n\nhi']
