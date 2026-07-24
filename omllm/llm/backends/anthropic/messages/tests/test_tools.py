import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore.secrets.tests.harness import HarnessSecrets

from .....models.default import default_model_catalog
from .....types.backends import ImmediateBackend
from .....types.content import TextContent
from .....types.content import ToolCall
from .....types.context import Context
from .....types.messages import ToolResultMessage
from .....types.messages import UserMessage
from .....types.models import ModelKey
from .....types.tools import Tool
from .....types.tools import ToolParam
from ..immediate import AnthropicMessagesImmediateBackend
from ..stream import AnthropicMessagesStreamBackend


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.parametrize('svc_cls', [
    AnthropicMessagesImmediateBackend,
    AnthropicMessagesStreamBackend,
])
async def test_anthropic_tools(
        harness,
        svc_cls,
):
    model_key, api_key_name = (ModelKey('anthropic', 'claude-sonnet-5'), 'anthropic_api_key')

    svc: ImmediateBackend = svc_cls(
        default_model_catalog()[model_key],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip(api_key_name),
    )

    ctx = Context(
        system_prompt='You are a helpful assistant.',
        messages=[
            UserMessage('What is the weather in Edinburgh, Scotland?'),
        ],
        tools=[
            Tool(
                name='get_weather',
                description='Get the weather in a given location',
                params=[
                    ToolParam(
                        name='location',
                        description='The city and state, e.g. San Francisco, CA',
                        type='string',
                    ),
                ],
            ),
        ],
    )

    out = await svc.immediate(ctx)

    # The model may or may not emit preamble text alongside the tool call.
    tc = check.single([c for c in out.content if isinstance(c, ToolCall)])
    assert tc.name == 'get_weather'
    assert tc.args == {'location': 'Edinburgh, Scotland'}

    ctx = dc.replace(ctx, messages=[
        *(ctx.messages or []),
        out,
        ToolResultMessage(
            tool_call_id=tc.id,
            tool_name=tc.name,
            content=[TextContent('The weather in Edinburgh, Scotland is sunny.')],
        ),
    ])

    out = await svc.immediate(ctx)

    print(out)
