import pytest

from omcore.secrets.tests.harness import HarnessSecrets

from .....models.default import default_model_catalog
from .....types.context import Context
from .....types.messages import UserMessage
from .....types.models import ModelKey
from .....types.options import Options
from ..immediate import GoogleGenerativeImmediateBackend


# Gemini's implicit prompt cache reliably misses under concurrent same-project traffic, so all
# google-online tests serialize onto one worker.
pytestmark = pytest.mark.xdist_group('google-online')


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

        svc = GoogleGenerativeImmediateBackend(
            default_model_catalog()[model_key],  # noqa
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


class TestGoogleBackend(BaseBackendTest):
    @pytest.fixture(params=[
        (ModelKey('google', 'gemini-3-flash-preview'), 'gemini_api_key'),
    ])
    def model(self, request):
        return request.param
