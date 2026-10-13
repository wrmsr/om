"""
Live checks that the catalog's declared effort levels match what each provider actually accepts: every declared level
must be accepted, with and without tools, and every undeclared level must be rejected by the provider itself - so a
catalog entry can neither advertise a level the provider has dropped nor hide one it offers.

Openrouter is the exception on the rejection side: it accepts every level for every upstream, so for it only the
declared levels are checked.

The matrix is built at collection time so that each case is a real test - the async harness does not report runtime
skips.
"""
import typing as ta

import pytest

from omcore import dataclasses as dc
from omcore.secrets.tests.harness import HarnessSecrets

from ...models.providers import provider_model_catalog
from ...models.providers.anthropic import TEST_MODEL_KEY as ANTHROPIC_TEST_MODEL_KEY
from ...models.providers.google import TEST_MODEL_KEY as GOOGLE_TEST_MODEL_KEY
from ...models.providers.openai import COMPLETIONS_TEST_MODEL_KEY as OPENAI_COMPLETIONS_TEST_MODEL_KEY
from ...models.providers.openai import RESPONSES_TEST_MODEL_KEY as OPENAI_RESPONSES_TEST_MODEL_KEY
from ...types.context import Context
from ...types.errors import BackendError
from ...types.errors import TransientBackendError
from ...types.messages import AiMessage
from ...types.messages import UserMessage
from ...types.models import ModelKey
from ...types.models import supported_reasoning_efforts
from ...types.options import Options
from ...types.options import ReasoningEffort
from ...types.tools import Tool
from ...types.tools import ToolDtype
from ...types.tools import ToolParam
from ..anthropic.messages.immediate import AnthropicMessagesImmediateBackend
from ..google.generative.immediate import GoogleGenerativeImmediateBackend
from ..openai.completions.immediate import OpenaiCompletionsImmediateBackend
from ..openai.responses.immediate import OpenaiResponsesImmediateBackend


##


# (id, model key, backend class, api key name, whether undeclared levels must be rejected, extra marks)
_CASES: ta.Sequence[tuple[str, ModelKey, type, str, bool, ta.Sequence[ta.Any]]] = [
    (
        'openai-responses',
        OPENAI_RESPONSES_TEST_MODEL_KEY,
        OpenaiResponsesImmediateBackend,
        'openai_api_key',
        True,
        [],
    ),
    (
        'openai-completions',
        OPENAI_COMPLETIONS_TEST_MODEL_KEY,
        OpenaiCompletionsImmediateBackend,
        'openai_api_key',
        True,
        [],
    ),
    (
        'anthropic',
        ANTHROPIC_TEST_MODEL_KEY,
        AnthropicMessagesImmediateBackend,
        'anthropic_api_key',
        True,
        [],
    ),
    (
        'google',
        GOOGLE_TEST_MODEL_KEY,
        GoogleGenerativeImmediateBackend,
        'gemini_api_key',
        True,
        # Gemini's implicit prompt cache reliably misses under concurrent same-project traffic, so all google-online
        # tests serialize onto one worker.
        [pytest.mark.xdist_group('google-online')],
    ),
    (
        'openrouter',
        ModelKey('openrouter', 'deepseek/deepseek-v4-flash-0731'),
        OpenaiCompletionsImmediateBackend,
        'openrouter_api_key',
        False,
        [],
    ),
]


def _params() -> list:
    params: list = []

    for case_id, key, backend_cls, api_key_name, strict, marks in _CASES:
        model = provider_model_catalog()[key]  # noqa
        base_levels = supported_reasoning_efforts(model)
        tool_levels = supported_reasoning_efforts(model, with_tools=True)

        for effort in ReasoningEffort:
            for tools, levels in [
                (False, base_levels),
                (True, tool_levels),
            ]:
                # Tools only ever narrow the base set - a level undeclared outright is covered by the tool-free case.
                if tools and effort not in base_levels:
                    continue

                accepted = effort in levels
                if not accepted and not strict:
                    continue

                params.append(pytest.param(
                    key,
                    backend_cls,
                    api_key_name,
                    effort,
                    tools,
                    accepted,
                    id=f'{case_id}-{effort.value}{"-tools" if tools else ""}',
                    marks=marks,
                ))

    return params


_TOOL = Tool(
    name='get_weather',
    description='Get the weather in a given location',
    params=[
        ToolParam(
            name='location',
            description='The city and state, e.g. San Francisco, CA',
            type=ToolDtype.of(str),
        ),
    ],
)


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.parametrize(('key', 'backend_cls', 'api_key_name', 'effort', 'tools', 'accepted'), _params())
async def test_declared_efforts_match_provider(harness, key, backend_cls, api_key_name, effort, tools, accepted):
    model = provider_model_catalog()[key]  # noqa

    # Undeclared levels are sent regardless, so that the provider - not the catalog - is what rejects them.
    svc = backend_cls(
        dc.replace(model, reasoning_efforts=frozenset(ReasoningEffort), reasoning_efforts_with_tools=None),
        api_key=harness[HarnessSecrets].get_or_skip(api_key_name),
    )

    context = Context(
        system_prompt='You are a terse assistant.',
        messages=[
            UserMessage('What is the weather in Edinburgh? Use the tool.' if tools else 'Reply with exactly: ok'),
        ],
        tools=[_TOOL] if tools else None,
    )

    options = Options(
        reasoning_effort=effort,
        max_tokens=2048,
    )

    if accepted:
        out = await svc.immediate(context, options)
        assert isinstance(out, AiMessage)

    else:
        with pytest.raises(BackendError) as ei:
            await svc.immediate(context, options)
        assert not isinstance(ei.value, TransientBackendError), ei.value
