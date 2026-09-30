import pytest

from omcore.secrets.tests.harness import HarnessSecrets

from .....models.providers import provider_model_catalog
from .....models.providers.anthropic import TEST_MODEL_KEY
from .....types.context import Context
from .....types.messages import UserMessage
from .....types.options import Options
from ..immediate import AnthropicMessagesImmediateBackend


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

        svc = AnthropicMessagesImmediateBackend(
            provider_model_catalog()[model_key],  # noqa
            api_key=harness[HarnessSecrets].get_or_skip(api_key_name),
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


class TestAnthropicBackend(BaseBackendTest):
    @pytest.fixture(params=[
        (TEST_MODEL_KEY, 'anthropic_api_key'),
    ])
    def model(self, request):
        return request.param
