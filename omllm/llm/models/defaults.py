import sys
import typing as ta

from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang
from omcore.formats.json import all as json

from ..types.models import ModelKey
from .apikeys import ApiKey
from .apikeys import secret_or_env_var_api_key


##


@dc.dataclass(frozen=True, kw_only=True)
class DefaultModel:
    name: str
    aliases: lang.SequenceNotStr | None = None

    key: ModelKey

    api_keys: ta.Sequence[ApiKey] | None = None

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
        key=ModelKey('anthropic', 'claude-fable-5-1'),
        api_keys=(ANTHROPIC_API_KEYS := secret_or_env_var_api_key('anthropic_api_key')),
    ),

    DefaultModel(
        name='claude-opus',
        aliases=['opus'],
        key=ModelKey('anthropic', 'claude-opus-5-5'),
        api_keys=ANTHROPIC_API_KEYS,
    ),

    DefaultModel(
        name='claude-sonnet',
        aliases=['sonnet', 'claude'],
        key=ModelKey('anthropic', 'claude-sonnet-5-5'),
        api_keys=ANTHROPIC_API_KEYS,
    ),

    DefaultModel(
        name='claude-haiku',
        aliases=['haiku'],
        key=ModelKey('anthropic', 'claude-haiku-5-5'),
        api_keys=ANTHROPIC_API_KEYS,
    ),

    ##
    # cerebras

    DefaultModel(
        name='cerebras-gpt',
        aliases=['cerebras'],
        key=ModelKey('cerebras', 'gpt-oss-120b'),
        api_keys=(CEREBRAS_API_KEYS := secret_or_env_var_api_key('cerebras_api_key')),
    ),

    ##
    # google

    DefaultModel(
        name='gemini-argon',
        aliases=['argon'],
        key=ModelKey('google', 'gemini-4-argon'),
        api_keys=(GEMINI_API_KEYS := secret_or_env_var_api_key('gemini_api_key')),
    ),

    DefaultModel(
        name='gemini-flash',
        aliases=['gemini', 'google'],
        key=ModelKey('google', 'gemini-3.8-flash'),
        api_keys=GEMINI_API_KEYS,
    ),

    DefaultModel(
        name='gemini-cheap',
        key=ModelKey('google', 'gemini-2.5-flash'),
        api_keys=GEMINI_API_KEYS,
    ),

    ##
    # groq

    DefaultModel(
        name='groq',
        key=ModelKey('groq', 'openai/gpt-oss-120b'),
        api_keys=(GROQ_API_KEYS := secret_or_env_var_api_key('groq_api_key')),
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
        api_keys=(OPENAI_API_KEYS := secret_or_env_var_api_key('openai_api_key')),
    ),

    DefaultModel(
        name='gpt-sol',
        aliases=['sol'],
        key=ModelKey('openai', 'gpt-6.1-sol'),
        api_keys=OPENAI_API_KEYS,
    ),

    DefaultModel(
        name='gpt-terra',
        aliases=['terra'],
        key=ModelKey('openai', 'gpt-6.1-terra'),
        api_keys=OPENAI_API_KEYS,
    ),

    DefaultModel(
        name='gpt-luna',
        aliases=['luna', 'gpt'],
        key=ModelKey('openai', 'gpt-6-luna'),
        api_keys=OPENAI_API_KEYS,
    ),

    DefaultModel(
        name='gpt-nano',
        aliases=['nano'],
        key=ModelKey('openai', 'gpt-5.4-nano'),
        api_keys=OPENAI_API_KEYS,
    ),

    ##
    # openrouter

    DefaultModel(
        name='deepseek-pro',
        key=ModelKey('openrouter', 'deepseek/deepseek-v4-pro-0813'),
        api_keys=(OPENROUTER_API_KEYS := secret_or_env_var_api_key('openrouter_api_key')),
    ),

    DefaultModel(
        name='deepseek-flash',
        aliases=['deepseek'],
        key=ModelKey('openrouter', 'deepseek/deepseek-v4.1-flash-1017'),
        api_keys=OPENROUTER_API_KEYS,
    ),

    DefaultModel(
        name='kimi',
        key=ModelKey('openrouter', 'moonshotai/kimi-k3'),
        api_keys=OPENROUTER_API_KEYS,
    ),

    DefaultModel(
        name='glm',
        key=ModelKey('openrouter', 'z-ai/glm-5.3'),
        api_keys=OPENROUTER_API_KEYS,
    ),

    DefaultModel(
        name='ling',
        key=ModelKey('openrouter', 'inclusionai/ling-3.0-flash'),
        api_keys=OPENROUTER_API_KEYS,
    ),

    DefaultModel(
        name='mercury',
        key=ModelKey('openrouter', 'inception/mercury-2.5'),
        api_keys=OPENROUTER_API_KEYS,
    ),

    DefaultModel(
        name='mimo',
        key=ModelKey('openrouter', 'xiaomi/mimo-v2.6-pro'),
        api_keys=OPENROUTER_API_KEYS,
    ),

    DefaultModel(
        name='mistral',
        key=ModelKey('openrouter', 'mistralai/mistral-large-4-0'),
        api_keys=OPENROUTER_API_KEYS,
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


##


def _main() -> None:
    from .providers import provider_model_catalog

    dcts: dict[str, dict] = {}

    mc = provider_model_catalog()
    for dm in ALL_DEFAULT_MODELS:
        m = mc[dm.key]

        dct: dict = {}

        limits = m.limits
        if callable(limits):
            limits = limits()
        if limits is not None:
            dct.update(
                limits={k: v for k, v in dc.asdict(limits).items() if v is not None},
            )

        pricing = m.pricing
        if callable(pricing):
            pricing = pricing()
        if pricing is not None:
            dct.update(
                pricing={k: v for k, v in dc.asdict(pricing).items() if v is not None},
            )

        dcts[dm.key.joined] = dct

    print(json.dumps_pretty(dcts))


if __name__ == '__main__':
    _main()
