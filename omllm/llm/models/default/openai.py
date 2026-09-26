"""
https://developers.openai.com/api/docs/models/all
https://platform.openai.com/docs/models/compare
"""
import typing as ta

from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ...types.options import CacheRetention
from ...types.options import ReasoningEffort
from ..manifests import ModelsModuleManifest
from ..modeldb import modeldb_model_limits
from ..modeldb import modeldb_token_pricing


##


_BASE_URL = 'https://api.openai.com/v1'

_REASONING_EFFORTS = frozenset({
    ReasoningEffort.NONE,
    ReasoningEffort.LOW,
    ReasoningEffort.MEDIUM,
    ReasoningEffort.HIGH,
    ReasoningEffort.XHIGH,
    ReasoningEffort.MAX,
})


MODELS: ta.Final[ta.Sequence[Model]] = [

    ##
    # 6

    Model(
        key=ModelKey(
            provider='openai',
            id='gpt-6-astra',
        ),
        name='GPT 6 Astra',
        backend='openai-responses',
        reasoning_efforts=_REASONING_EFFORTS - {ReasoningEffort.NONE},
        cache=CacheCapabilities(
            control_style='openai_ttl',
            retentions=frozenset({
                CacheRetention.THIRTY_MINUTES,
            }),
            key=True,
        ),
        limits=modeldb_model_limits('openai', 'gpt-6-astra'),
        pricing=modeldb_token_pricing('openai', 'gpt-6-astra'),
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

    Model(
        key=ModelKey(
            provider='openai',
            id='gpt-6-sol',
        ),
        name='GPT 6 Sol',
        backend='openai-responses',
        reasoning_efforts=_REASONING_EFFORTS,
        cache=CacheCapabilities(
            control_style='openai_ttl',
            retentions=frozenset({
                CacheRetention.THIRTY_MINUTES,
            }),
            key=True,
        ),
        limits=modeldb_model_limits('openai', 'gpt-6-sol'),
        pricing=modeldb_token_pricing('openai', 'gpt-6-sol'),
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

    Model(
        key=ModelKey(
            provider='openai',
            id='gpt-6-luna',
        ),
        name='GPT 6 Luna',
        backend='openai-responses',
        reasoning_efforts=_REASONING_EFFORTS,
        cache=CacheCapabilities(
            control_style='openai_ttl',
            retentions=frozenset({
                CacheRetention.THIRTY_MINUTES,
            }),
            key=True,
        ),
        limits=modeldb_model_limits('openai', 'gpt-6-luna'),
        pricing=modeldb_token_pricing('openai', 'gpt-6-luna'),
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

    ##
    # 5.6

    Model(
        key=ModelKey(
            provider='openai',
            id='gpt-5.6-terra',
        ),
        name='GPT 5.6 Terra',
        backend='openai-responses',
        reasoning_efforts=_REASONING_EFFORTS,
        cache=CacheCapabilities(
            control_style='openai_ttl',
            retentions=frozenset({
                CacheRetention.THIRTY_MINUTES,
            }),
            key=True,
        ),
        limits=modeldb_model_limits('openai', 'gpt-5.6-terra'),
        pricing=modeldb_token_pricing('openai', 'gpt-5.6-terra'),
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

    ##
    # 5.4

    Model(
        key=ModelKey(
            provider='openai',
            id='gpt-5.4-nano',
        ),
        name='GPT 5.4 Nano',
        backend='openai-completions',
        reasoning_efforts=_REASONING_EFFORTS - {ReasoningEffort.MAX},
        # This endpoint rejects function tools combined with non-none effort (verified against the live API).
        reasoning_efforts_with_tools=frozenset({ReasoningEffort.NONE}),
        cache=CacheCapabilities(
            control_style='openai_legacy',
            retentions=frozenset({
                CacheRetention.IN_MEMORY,
                CacheRetention.ONE_DAY,
            }),
            key=True,
        ),
        limits=modeldb_model_limits('openai', 'gpt-5.4-nano'),
        pricing=modeldb_token_pricing('openai', 'gpt-5.4-nano'),
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

]


# @om-manifest
_MANIFEST = ModelsModuleManifest.of(MODELS)
