import pytest

from omcore import lang
from omcore.http import all as http
from omcore.secrets.tests.harness import HarnessSecrets

from .....models.default import default_model_catalog
from .....types.context import Context
from .....types.messages import UserMessage
from .....types.models import ModelKey
from .....types.options import Options
from ..immediate import OpenaiCompletionsImmediateBackend


class BaseBackendTest:
    @pytest.mark.online
    @pytest.mark.asyncs('asyncio')
    @pytest.mark.parametrize('max_tokens', [None, 1024])
    async def test_backend(
            self,
            harness,
            model,
            max_tokens,
    ):
        model_key, api_key_name = model

        svc = OpenaiCompletionsImmediateBackend(
            default_model_catalog()[model_key],  # noqa
            **(dict(api_key=harness[HarnessSecrets].get_or_skip(api_key_name)) if api_key_name is not None else {}),
        )

        out = await svc.immediate(
            Context(
                system_prompt='You are a helpful assistant.',
                messages=[
                    UserMessage('hi'),
                ],
            ),
            Options(
                max_tokens=max_tokens,
            ),
        )

        print(out)

    @pytest.mark.online
    def test_backend_sync(
            self,
            harness,
            model,
    ):
        model_key, api_key_name = model

        svc = OpenaiCompletionsImmediateBackend(
            default_model_catalog()[model_key],  # noqa
            **(dict(api_key=harness[HarnessSecrets].get_or_skip(api_key_name)) if api_key_name is not None else {}),
            http_client=http.SyncAsyncHttpClient(http.client()),
        )

        out = lang.sync_await(svc.immediate(
            Context(
                system_prompt='You are a helpful assistant.',
                messages=[
                    UserMessage('hi'),
                ],
            ),
        ))

        print(out)


class TestOpenaiBackend(BaseBackendTest):
    @pytest.fixture(params=[
        (ModelKey('openai', 'gpt-5.4-nano'), 'openai_api_key'),
    ])
    def model(self, request):
        return request.param


# Openrouter routes across upstream providers of varying speed - an uncapped generation can exceed the default
# per-test timeout on a slow one.
@pytest.mark.timeout(180)
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
        from .....models.default.ollama import _BASE_URL

        try:
            http.request(_BASE_URL)
        except http.HttpClientError:
            pytest.skip('No ollama server')

        return request.param
