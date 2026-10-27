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


##


def _make_model(
        *,
        id: str | ModelKey,  # noqa
        name: str,

        **kwargs: ta.Any,
) -> Model:
    key = id if isinstance(id, ModelKey) else ModelKey(
        provider='openai',
        id=id,
    )

    return Model(
        key=key,
        name=name,

        **{
            **dict(
                backend='openai-responses',

                reasoning_efforts=_REASONING_EFFORTS,

                cache=CacheCapabilities(
                    control_style='openai_ttl',
                    retentions=frozenset({
                        CacheRetention.THIRTY_MINUTES,
                    }),
                    key=True,
                ),

                limits=modeldb_model_limits('openai', key.id),
                pricing=modeldb_token_pricing('openai', key.id),

                http=Model.Http(
                    base_url=_BASE_URL,
                ),
            ),

            **kwargs,
        },
    )


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    _make_model(
        id='gpt-6-astra',
        name='GPT 6 Astra',

        reasoning_efforts=_REASONING_EFFORTS - {ReasoningEffort.NONE},
    ),

    _make_model(
        id='gpt-6.1-sol',
        name='GPT 6.1 Sol',

        # Like astra, this model rejects none (verified against the live API).
        reasoning_efforts=_REASONING_EFFORTS - {ReasoningEffort.NONE},
    ),

    _make_model(
        id='gpt-6.1-terra',
        name='GPT 6.1 Terra',
    ),

    _make_model(
        id=(RESPONSES_TEST_MODEL_KEY := ModelKey('openai', 'gpt-6-luna')),
        name='GPT 6 Luna',
    ),

    _make_model(
        id=(COMPLETIONS_TEST_MODEL_KEY := ModelKey('openai', 'gpt-5.4-nano')),
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
    ),

]


# @om-manifest
_MANIFEST = ModelsModuleManifest.of(MODELS)
