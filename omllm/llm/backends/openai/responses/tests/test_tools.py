import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore.secrets.tests.harness import HarnessSecrets

from .....models.default import default_model_catalog
from .....types.backends import ImmediateBackend
from .....types.content import TextContent
from .....types.content import ThinkingContent
from .....types.content import ToolCall
from .....types.context import Context
from .....types.messages import ToolResultMessage
from .....types.messages import UserMessage
from .....types.models import ModelKey
from .....types.options import Options
from .....types.tools import Tool
from .....types.tools import ToolDtype
from .....types.tools import ToolParam
from ..immediate import OpenaiResponsesImmediateBackend
from ..stream import OpenaiResponsesStreamBackend


class TestOpenaiTools:
    @pytest.fixture(params=[
        (ModelKey('openai', 'gpt-5.6-luna'), 'openai_api_key'),
    ])
    def model(self, request):
        return request.param

    @pytest.mark.online
    @pytest.mark.asyncs('asyncio')
    @pytest.mark.parametrize('svc_cls', [
        OpenaiResponsesImmediateBackend,
        OpenaiResponsesStreamBackend,
    ])
    @pytest.mark.parametrize('thinking', [None, True])
    async def test_openai_tools(
            self,
            harness,
            svc_cls,
            model,
            thinking,
    ):
        model_key, api_key_name = model

        svc: ImmediateBackend = svc_cls(  # noqa
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
                            type=ToolDtype.of(str),
                        ),
                    ],
                ),
            ],
        )

        opts = Options(thinking=thinking)

        out = await svc.immediate(ctx, opts)

        tc = check.single([c for c in out.content if isinstance(c, ToolCall)])
        assert tc.name == 'get_weather'
        assert tc.args == {'location': 'Edinburgh, Scotland'}
        assert out.stop_reason == 'tool_use'

        # Any reasoning produced must have come back in replayable (signed) form.
        for c in out.content:
            if isinstance(c, ThinkingContent):
                assert c.backend_signature

        ctx = dc.replace(ctx, messages=[
            *(ctx.messages or []),
            out,
            ToolResultMessage(
                tool_call_id=tc.id,
                tool_name=tc.name,
                content=[TextContent('The weather in Edinburgh, Scotland is sunny.')],
            ),
        ])

        out = await svc.immediate(ctx, opts)

        assert any(isinstance(c, TextContent) and c.text for c in out.content)

        print(out)
