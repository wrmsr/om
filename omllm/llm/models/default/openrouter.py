import typing as ta

from ...types.compat import OpenaiCompletionsCompat
from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ..manifests import ModelsModuleManifest


##


_BASE_URL = 'https://openrouter.ai/api/v1'

# Upstream providers cache implicitly with no request cache fields. Options.cache_key becomes a session affinity header
# pinning repeat requests to one upstream, without which openrouter's load balancing makes cache hits a matter of
# routing luck.
_CACHE = CacheCapabilities(
    control_style='openrouter',
    key=True,
)

# Openrouter normalizes upstream reasoning text onto a bare reasoning field, and reports each request's actual billed
# cost (which varies by routed upstream) in its usage.
_COMPAT = OpenaiCompletionsCompat(
    reasoning_field='reasoning',
    cost_mode='openrouter',
)


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='openrouter',
            id='deepseek/deepseek-v4-pro-0813',
        ),
        name='DeepSeek V4 Pro 0813',
        backend='openai-completions',
        compat=_COMPAT,
        cache=_CACHE,
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

    Model(
        key=ModelKey(
            provider='openrouter',
            id='deepseek/deepseek-v4-flash-0731',
        ),
        name='DeepSeek V4 Flash 0731',
        backend='openai-completions',
        compat=_COMPAT,
        cache=_CACHE,
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

    #

    Model(
        key=ModelKey(
            provider='openrouter',
            id='moonshotai/kimi-k3',
        ),
        name='Kimi K3',
        backend='openai-completions',
        compat=_COMPAT,
        cache=_CACHE,
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

    #

    Model(
        key=ModelKey(
            provider='openrouter',
            id='z-ai/glm-5.3',
        ),
        name='GLM-5.3',
        backend='openai-completions',
        compat=_COMPAT,
        cache=_CACHE,
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

]


# @om-manifest
_MANIFEST = ModelsModuleManifest.of(MODELS)
