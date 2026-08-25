import pytest

from omcore import lang
from omcore.http import all as http
from omcore.secrets.tests.harness import HarnessSecrets

from .....models.default import default_model_catalog
from .....types.context import Context
from .....types.messages import AiMessage
from .....types.messages import UserMessage
from .....types.models import ModelKey
from .....types.options import Options
from ..stream import OpenaiCompletionsStreamBackend


class BaseBackendTest:
    @pytest.mark.asyncs('asyncio')
    @pytest.mark.online
    async def test_openai_chat_stream_model_async(
            self,
            harness,
            model,
    ):
        model_key, api_key_name = model

        svc = OpenaiCompletionsStreamBackend(
            default_model_catalog()[model_key],  # noqa
            **(dict(api_key=harness[HarnessSecrets].get_or_skip(api_key_name)) if api_key_name is not None else {}),
        )

        #

        events: list = []

        async with (await svc.stream(
            ctx := Context(
                system_prompt='You are a helpful assistant.',
                messages=[
                    UserMessage('hi'),
                ],
            ),
            opts := Options(
                max_tokens=None,
            ),
        )) as it:
            async for e in it:
                events.append(e)
            out = it.result.must()

        assert isinstance(out, AiMessage)

        #

        out = await svc.immediate(ctx, opts)

        assert isinstance(out, AiMessage)

    @pytest.mark.online
    def test_openai_chat_stream_model_sync(
            self,
            harness,
            model,
    ):
        model_key, api_key_name = model

        svc = OpenaiCompletionsStreamBackend(
            default_model_catalog()[model_key],  # noqa
            **(dict(api_key=harness[HarnessSecrets].get_or_skip(api_key_name)) if api_key_name is not None else {}),
            http_client=http.SyncAsyncHttpClient(http.client()),
        )

        #

        ctx = Context(
            system_prompt='You are a helpful assistant.',
            messages=[
                UserMessage('hi'),
            ],
        )

        opts = Options(
            max_tokens=None,
        )

        events: list = []

        with lang.sync_async_with(lang.sync_await(svc.stream(
                ctx,
                opts,
        ))) as it:
            for e in lang.sync_aiter(it):
                events.append(e)  # noqa
            out = it.result.must()

        assert isinstance(out, AiMessage)

        #

        out = lang.sync_await(svc.immediate(ctx, opts))

        assert isinstance(out, AiMessage)


class TestOpenaiBackend(BaseBackendTest):
    @pytest.fixture(params=[
        (ModelKey('openai', 'gpt-5.4-mini'), 'openai_api_key'),
    ])
    def model(self, request):
        return request.param


class TestOpenrouterBackend(BaseBackendTest):
    @pytest.fixture(params=[
        (ModelKey('openrouter', 'deepseek/deepseek-v4-flash-0731'), 'openrouter_api_key'),
    ])
    def model(self, request):
        return request.param


class TestGroqBackend(BaseBackendTest):
    @pytest.fixture(params=[
        (ModelKey('groq', 'openai/gpt-oss-120b'), 'groq_api_key'),
    ])
    def model(self, request):
        return request.param


class TestCerebrasBackend(BaseBackendTest):
    @pytest.fixture(params=[
        (ModelKey('cerebras', 'gpt-oss-120b'), 'cerebras_api_key'),
    ])
    def model(self, request):
        return request.param


class TestOllamaBackend(BaseBackendTest):
    @pytest.fixture(params=[
        (ModelKey('ollama', 'qwen3.5:2b'), None),
    ])
    def model(self, request):
        from .....models.default.ollama import DEFAULT_OLLAMA_URL

        try:
            http.request(DEFAULT_OLLAMA_URL)
        except http.HttpClientError:
            pytest.skip('No ollama server')

        return request.param
