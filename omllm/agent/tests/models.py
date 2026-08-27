import typing as ta

from ... import llm


##


class ModelForTest(ta.NamedTuple):
    model_key: llm.ModelKey
    api_key_name: str
    stream_backend_cls: ta.Callable[..., llm.StreamBackend]


OPENAI = ModelForTest(
    llm.ModelKey('openai', 'gpt-5.4-nano'),
    'openai_api_key',
    llm.OpenaiCompletionsStreamBackend,
)

ANTHROPIC = ModelForTest(
    llm.ModelKey('anthropic', 'claude-sonnet-5'),
    'anthropic_api_key',
    llm.AnthropicMessagesStreamBackend,
)

GOOGLE = ModelForTest(
    llm.ModelKey('google', 'gemini-3-flash-preview'),
    'gemini_api_key',
    llm.GoogleGenerativeStreamBackend,
)
