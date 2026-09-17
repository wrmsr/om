import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore.asyncs.asynclite import all as asl

from .... import llm
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.tools import EchoTool
from ...turns.loop import TurnLoop
from ...types.contexts import Context
from ...types.lifecycle import ContextProjection
from ...types.lifecycle import ToolResultProjection
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


def test_tool_results_are_reduced_only_in_the_model_projection():
    full_text = 'head-' + ('x' * 200) + '-tail'
    result = llm.ToolResultMessage(
        tool_call_id='t1',
        tool_name='read',
        content=(llm.TextContent(full_text),),
    )
    context = Context(
        messages=[
            llm.UserMessage('read it'),
            llm.AiMessage([llm.ToolCall('t1', 'read', {})]),
            result,
        ],
        projection=ContextProjection(tool_results=(ToolResultProjection(message_index=2, max_chars=80),)),
    )

    projected = StandardLlmContextBuilder().build(context)

    # The transcript is lossless and the model-facing result retains the provider protocol identity.
    assert context.messages is not None and context.messages[2] is result
    assert result.content[0].text == full_text
    model_result = check.isinstance((projected.messages or [])[2], llm.ToolResultMessage)
    assert model_result.tool_call_id == 't1'
    assert model_result.tool_name == 'read'
    assert len(model_result.content[0].text) == 80
    assert 'result truncated from 210 characters' in model_result.content[0].text

    pruned = dc.replace(
        context,
        projection=context.projection.with_tool_result(ToolResultProjection(message_index=2, max_chars=0)),
    )
    pruned_result = check.isinstance(
        (StandardLlmContextBuilder().build(pruned).messages or [])[2],
        llm.ToolResultMessage,
    )
    assert 'Earlier read result pruned' in pruned_result.content[0].text
    assert pruned_result.tool_call_id == 't1'


def test_summary_projection_keeps_only_the_selected_tail():
    context = Context(
        messages=[
            llm.UserMessage('old'),
            llm.AiMessage([llm.TextContent('old answer')]),
            llm.UserMessage('new'),
        ],
        projection=ContextProjection(
            summary='The old exchange established the constraints.',
            first_kept_message_index=2,
        ),
    )

    projected = StandardLlmContextBuilder().build(context)

    assert _user_texts(projected.messages or []) == [
        'Earlier conversation summary:\n\nThe old exchange established the constraints.\n\nnew',
    ]


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
