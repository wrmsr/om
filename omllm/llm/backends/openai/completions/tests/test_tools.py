import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore.http import all as http
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
from .....types.tools import ToolDtype
from .....types.tools import ToolParam
from ..immediate import OpenaiCompletionsImmediateBackend
from ..stream import OpenaiCompletionsStreamBackend


class BaseToolsTest:
    @pytest.mark.online
    @pytest.mark.asyncs('asyncio')
    @pytest.mark.parametrize('svc_cls', [
        OpenaiCompletionsImmediateBackend,
        OpenaiCompletionsStreamBackend,
    ])
    async def test_openai_tools(
            self,
            harness,
            svc_cls,
            model,
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

        out = await svc.immediate(ctx)

        tc = check.isinstance(check.single(out.content), ToolCall)
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


class TestOpenaiTools(BaseToolsTest):
    @pytest.fixture(params=[
        (ModelKey('openai', 'gpt-5.4-nano'), 'openai_api_key'),
    ])
    def model(self, request):
        return request.param


class TestGroqTools(BaseToolsTest):
    @pytest.fixture(params=[
        (ModelKey('groq', 'openai/gpt-oss-120b'), 'groq_api_key'),
    ])
    def model(self, request):
        return request.param


class TestCerebrasTools(BaseToolsTest):
    @pytest.fixture(params=[
        (ModelKey('cerebras', 'gpt-oss-120b'), 'cerebras_api_key'),
    ])
    def model(self, request):
        return request.param


class TestOllamaTools(BaseToolsTest):
    @pytest.fixture(params=[
        (ModelKey('ollama', 'qwen3.5:2b'), None),
    ])
    def model(self, request):
        from .....models.default.ollama import _BASE_URL

        try:
            http.request(_BASE_URL)
        except http.HttpClientError:
            pytest.skip('No ollama server')

        return request.param
