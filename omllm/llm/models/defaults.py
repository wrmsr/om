import sys
import typing as ta

from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang

from ..types.models import ModelKey


##


@dc.dataclass(frozen=True, kw_only=True)
class DefaultModel:
    name: str
    aliases: lang.SequenceNotStr | None = None

    key: ModelKey

    api_key_name: str | None = None

    include_platforms: ta.AbstractSet[str] | None = None
    exclude_platforms: ta.AbstractSet[str] | None = None


##


DEFAULT_MODEL_NAME: ta.Final = 'gpt'


ALL_DEFAULT_MODELS: ta.Final[ta.Sequence[DefaultModel]] = [

    ##
    # anthropic

    DefaultModel(
        name='claude-fable',
        aliases=['fable'],
        key=ModelKey('anthropic', 'claude-fable-5.1'),
        api_key_name='anthropic_api_key',
    ),

    DefaultModel(
        name='claude-opus',
        aliases=['opus'],
        key=ModelKey('anthropic', 'claude-opus-5.5'),
        api_key_name='anthropic_api_key',
    ),

    DefaultModel(
        name='claude-sonnet',
        aliases=['sonnet', 'claude'],
        key=ModelKey('anthropic', 'claude-sonnet-5-5'),
        api_key_name='anthropic_api_key',
    ),

    DefaultModel(
        name='claude-haiku',
        aliases=['haiku'],
        key=ModelKey('anthropic', 'claude-haiku-4-5-20251001'),
        api_key_name='anthropic_api_key',
    ),

    ##
    # cerebras

    DefaultModel(
        name='cerebras-gpt',
        aliases=['cerebras'],
        key=ModelKey('cerebras', 'gpt-oss-120b'),
        api_key_name='cerebras_api_key',
    ),

    ##
    # google

    DefaultModel(
        name='gemini-flash',
        aliases=['gemini', 'google'],
        key=ModelKey('google', 'gemini-3.8-flash'),
        api_key_name='gemini_api_key',
    ),

    ##
    # groq

    DefaultModel(
        name='groq',
        key=ModelKey('groq', 'openai/gpt-oss-120b'),
        api_key_name='groq_api_key',
    ),

    ##
    # ollama

    DefaultModel(
        name='ollama-qwen',
        aliases=['qwen'],
        key=ModelKey('ollama', 'qwen3.8:27b'),
        exclude_platforms={'darwin'},
    ),

    DefaultModel(
        name='ollama-qwen',
        aliases=['qwen'],
        key=ModelKey('ollama', 'qwen3.8:27b-mlx'),
        include_platforms={'darwin'},
    ),

    ##
    # openai

    DefaultModel(
        name='gpt-astra',
        aliases=['astra'],
        key=ModelKey('openai', 'gpt-6-astra'),
        api_key_name='openai_api_key',
    ),

    DefaultModel(
        name='gpt-sol',
        aliases=['sol'],
        key=ModelKey('openai', 'gpt-6.1-sol'),
        api_key_name='openai_api_key',
    ),

    DefaultModel(
        name='gpt-terra',
        aliases=['terra'],
        key=ModelKey('openai', 'gpt-5.6-terra'),
        api_key_name='openai_api_key',
    ),

    DefaultModel(
        name='gpt-luna',
        aliases=['luna', 'gpt'],
        key=ModelKey('openai', 'gpt-6-luna'),
        api_key_name='openai_api_key',
    ),

    DefaultModel(
        name='gpt-nano',
        aliases=['nano'],
        key=ModelKey('openai', 'gpt-5.4-nano'),
        api_key_name='openai_api_key',
    ),

    ##
    # openrouter

    DefaultModel(
        name='deepseek-pro',
        key=ModelKey('openrouter', 'deepseek/deepseek-v4-pro-0813'),
        api_key_name='openrouter_api_key',
    ),

    DefaultModel(
        name='deepseek-flash',
        aliases=['deepseek'],
        key=ModelKey('openrouter', 'deepseek/deepseek-v4-flash-0731'),
        api_key_name='openrouter_api_key',
    ),

    DefaultModel(
        name='kimi',
        key=ModelKey('openrouter', 'moonshotai/kimi-k3'),
        api_key_name='openrouter_api_key',
    ),

    DefaultModel(
        name='glm',
        key=ModelKey('openrouter', 'z-ai/glm-5.3'),
        api_key_name='openrouter_api_key',
    ),

    DefaultModel(
        name='ling',
        key=ModelKey('openrouter', 'inclusionai/ling-3.0-flash'),
        api_key_name='openrouter_api_key',
    ),

    DefaultModel(
        name='mercury',
        key=ModelKey('openrouter', 'inception/mercury-2.5'),
        api_key_name='openrouter_api_key',
    ),

]


##


@lang.cached_function
def default_models_by_name(
        *,
        platform: str | None = None,
) -> ta.Mapping[str, DefaultModel]:
    if platform is None:
        platform = sys.platform

    return col.make_map((
        (n, m)
        for m in ALL_DEFAULT_MODELS
        if (ip := m.include_platforms) is None or platform in ip
        if (ep := m.exclude_platforms) is None or platform not in ep
        for n in [m.name, *(m.aliases or [])]
    ), strict=True)
