import pytest

from omcore.secrets.tests.harness import HarnessSecrets

from .....models.providers import provider_model_catalog
from .....models.providers.google import TEST_MODEL_KEY
from .....types.context import Context
from .....types.messages import AiMessage
from .....types.messages import UserMessage
from .....types.options import Options
from ..stream import GoogleGenerativeStreamBackend


# Gemini's implicit prompt cache reliably misses under concurrent same-project traffic, so all google-online tests
# serialize onto one worker.
pytestmark = pytest.mark.xdist_group('google-online')


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
async def test_google_chat_stream_model_async(harness):
    model = (TEST_MODEL_KEY, 'gemini_api_key')

    model_key, api_key_name = model

    svc = GoogleGenerativeStreamBackend(
        provider_model_catalog()[model_key],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip(api_key_name),
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
