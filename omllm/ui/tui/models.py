import typing as ta

from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang

from ... import llm


##


DEFAULT_MODEL_NAME: ta.Final = 'gpt-luna'


@dc.dataclass(frozen=True, kw_only=True)
class Model:
    name: str
    aliases: lang.SequenceNotStr | None = None

    key: llm.ModelKey

    api_key_name: str | None = None


MODELS: ta.Final[ta.Sequence[Model]] = [

    ##
    # anthropic

    Model(
        name='claude-fable',
        key=llm.ModelKey('anthropic', 'claude-fable-5'),
        api_key_name='anthropic_api_key',
    ),

    Model(
        name='claude-opus',
        key=llm.ModelKey('anthropic', 'claude-opus-5'),
        api_key_name='anthropic_api_key',
    ),

    Model(
        name='claude-sonnet',
        aliases=['claude'],
        key=llm.ModelKey('anthropic', 'claude-sonnet-5'),
        api_key_name='anthropic_api_key',
    ),

    Model(
        name='claude-haiku',
        key=llm.ModelKey('anthropic', 'claude-haiku-4-5-20251001'),
        api_key_name='anthropic_api_key',
    ),

    ##
    # cerebras

    Model(
        name='cerebras-gpt',
        aliases=['cerebras'],
        key=llm.ModelKey('cerebras', 'gpt-oss-120b'),
        api_key_name='cerebras_api_key',
    ),

    ##
    # google

    Model(
        name='google-flash',
        aliases=['google'],
        key=llm.ModelKey('google', 'gemini-3-flash-preview'),
        api_key_name='gemini_api_key',
    ),

    ##
    # groq

    Model(
        name='groq',
        key=llm.ModelKey('groq', 'openai/gpt-oss-120b'),
        api_key_name='groq_api_key',
    ),

    ##
    # ollama

    Model(
        name='ollama-qwen',
        key=llm.ModelKey('ollama', 'qwen3.8:27b'),
    ),

    Model(
        name='ollama-qwen-mlx',
        key=llm.ModelKey('ollama', 'qwen3.8:27b-mlx'),
    ),

    ##
    # openai

    Model(
        name='gpt-sol',
        key=llm.ModelKey('openai', 'gpt-5.6-sol'),
        api_key_name='openai_api_key',
    ),

    Model(
        name='gpt-terra',
        key=llm.ModelKey('openai', 'gpt-5.6-terra'),
        api_key_name='openai_api_key',
    ),

    Model(
        name='gpt-luna',
        aliases=['gpt'],
        key=llm.ModelKey('openai', 'gpt-5.6-luna'),
        api_key_name='openai_api_key',
    ),

    Model(
        name='gpt-nano',
        key=llm.ModelKey('openai', 'gpt-5.4-nano'),
        api_key_name='openai_api_key',
    ),

    ##
    # openrouter

    Model(
        name='deepseek-pro',
        key=llm.ModelKey('openrouter', 'deepseek/deepseek-v4-pro-0813'),
        api_key_name='openrouter_api_key',
    ),

    Model(
        name='deepseek-flash',
        aliases=['deepseek'],
        key=llm.ModelKey('openrouter', 'deepseek/deepseek-v4-flash-0731'),
        api_key_name='openrouter_api_key',
    ),

    Model(
        name='kimi',
        key=llm.ModelKey('openrouter', 'moonshotai/kimi-k3'),
        api_key_name='openrouter_api_key',
    ),

    Model(
        name='glm',
        key=llm.ModelKey('openrouter', 'z-ai/glm-5.3'),
        api_key_name='openrouter_api_key',
    ),

]


MODELS_BY_NAME: ta.Final[ta.Mapping[str, Model]] = col.make_map((
    (n, m)
    for m in MODELS
    for n in [m.name, *(m.aliases or [])]
), strict=True)
