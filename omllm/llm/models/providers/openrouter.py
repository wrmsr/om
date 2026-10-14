import typing as ta

from ...types.compat import OpenaiCompletionsCompat
from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ...types.options import ReasoningEffort
from ..manifests import ModelsModuleManifest
from ..modeldb import modeldb_model_limits
from ..modeldb import modeldb_token_pricing


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

# Openrouter normalizes the openai-style reasoning_effort field onto its unified reasoning.effort for every upstream,
# and accepts every level for every model here - but how far the upstream then honors it varies by model (verified
# against the live API). Only the levels which are meaningful everywhere are declared: none disables reasoning where the
# upstream permits that, and the models which do not opt out of it below.
_REASONING_EFFORTS = frozenset({
    ReasoningEffort.NONE,
    ReasoningEffort.LOW,
    ReasoningEffort.MEDIUM,
    ReasoningEffort.HIGH,
})

# Rejected with "Reasoning is mandatory for this endpoint and cannot be disabled."
_MANDATORY_REASONING_EFFORTS = _REASONING_EFFORTS - {ReasoningEffort.NONE}


def _make_model(
        *,
        id: str,  # noqa
        name: str,

        reasoning_efforts: ta.AbstractSet[ReasoningEffort] = _REASONING_EFFORTS,
) -> Model:
    return Model(
        key=ModelKey(
            provider='openrouter',
            id=id,
        ),
        name=name,
        backend='openai-completions',
        compat=_COMPAT,
        reasoning_efforts=reasoning_efforts,
        cache=_CACHE,
        limits=modeldb_model_limits('openrouter', id),
        pricing=modeldb_token_pricing('openrouter', id),
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    )


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    ##
    # deepseek

    _make_model(
        id='deepseek/deepseek-v4-pro-0813',
        name='DeepSeek V4 Pro 0813',
    ),

    _make_model(
        id='deepseek/deepseek-v4-flash-0731',
        name='DeepSeek V4 Flash 0731',
    ),

    ##
    # kimi

    _make_model(
        id='moonshotai/kimi-k3',
        name='Kimi K3',
    ),

    ##
    # glm

    _make_model(
        id='z-ai/glm-5.3',
        name='GLM 5.3',
        reasoning_efforts=_MANDATORY_REASONING_EFFORTS,
    ),

    _make_model(
        id='z-ai/glm-5.3-flash',
        name='GLM 5.3 Flash',
        reasoning_efforts=_MANDATORY_REASONING_EFFORTS,
    ),

    ##
    # ling

    _make_model(
        id='inclusionai/ling-3.0-flash',
        name='Ling 3.0 Flash',
    ),

    ##
    # mercury

    _make_model(
        id='inception/mercury-2.5',
        name='Mercury 2.5',
    ),

    ##
    # mimo

    _make_model(
        id='xiaomi/mimo-v2.6-pro',
        name='MiMo 2.6 Pro',
    ),

    ##
    # mistral

    _make_model(
        id='mistralai/mistral-large-4-0',
        name='Mistral Large 4',
    ),

    ##
    # qwen

    _make_model(
        id='qwen/qwen3.8-max-prime',
        name='Qwen3.8 Max Prime',
        reasoning_efforts=_MANDATORY_REASONING_EFFORTS,
    ),

    _make_model(
        id='qwen/qwen3.8-flash',
        name='Qwen 3.8 Flash',
    ),

]


# @om-manifest
_MANIFEST = ModelsModuleManifest.of(MODELS)
