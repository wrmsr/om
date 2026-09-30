import typing as ta

from ... import llm
from ...llm.models.providers.anthropic import TEST_MODEL_KEY as ANTHROPIC_TEST_MODEL_KEY
from ...llm.models.providers.google import TEST_MODEL_KEY as GOOGLE_TEST_API_KEY
from ...llm.models.providers.openai import COMPLETIONS_TEST_MODEL_KEY as OPENAI_TEST_MODEL_KEY


##


class ModelForTest(ta.NamedTuple):
    model_key: llm.ModelKey
    api_key_name: str
    stream_backend_cls: ta.Callable[..., llm.StreamBackend]


OPENAI = ModelForTest(
    OPENAI_TEST_MODEL_KEY,
    'openai_api_key',
    llm.OpenaiCompletionsStreamBackend,
)

ANTHROPIC = ModelForTest(
    ANTHROPIC_TEST_MODEL_KEY,
    'anthropic_api_key',
    llm.AnthropicMessagesStreamBackend,
)

GOOGLE = ModelForTest(
    GOOGLE_TEST_API_KEY,
    'gemini_api_key',
    llm.GoogleGenerativeStreamBackend,
)
