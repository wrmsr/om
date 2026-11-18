"""
.
https://platform.claude.com/docs/en/models/overview

TODO:
 - bring back opus 4.8
"""
import typing as ta

from ....core.apikeys import secret_or_env_var_api_key
from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ...types.models import ModelShortIds
from ...types.options import CacheRetention
from ...types.options import Options
from ...types.options import ReasoningEffort
from ..manifests import ModelsModuleManifest
from ..modeldb import modeldb_model_limits
from ..modeldb import modeldb_token_pricing


##


_BASE_URL = 'https://api.anthropic.com/v1'

_DEFAULT_HTTP = Model.Http(
    base_url=_BASE_URL,
    extra_headers={
        'anthropic-version': '2023-06-01',
    },
)

_API_KEYS = secret_or_env_var_api_key('anthropic_api_key')


_REASONING_EFFORTS = frozenset({
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
        provider='anthropic',
        id=id,
    )

    return Model(
        key=key,
        name=name,

        **{
            **dict(
                backend='anthropic-messages',

                reasoning_efforts=_REASONING_EFFORTS,

                cache=CacheCapabilities(
                    control_style='anthropic',
                    retentions=frozenset({
                        CacheRetention.FIVE_MINUTES,
                        CacheRetention.ONE_HOUR,
                    }),
                ),

                limits=modeldb_model_limits('anthropic', key.id),
                pricing=modeldb_token_pricing('anthropic', key.id),

                http=_DEFAULT_HTTP,

                api_keys=_API_KEYS,
            ),

            **kwargs,
        },
    )


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    _make_model(
        id='claude-fable-5-2',
        name='Claude Fable 5.2',

        short_ids=ModelShortIds(
            short_id='claude-fable',
            short_id_aliases=['fable'],
        ),

        default_options=Options(
            max_tokens=128000,
        ),
    ),

    _make_model(
        id='claude-opus-5-5',
        name='Claude Opus 5.5',

        short_ids=ModelShortIds(
            short_id='claude-opus',
            short_id_aliases=['opus'],
        ),

        default_options=Options(
            max_tokens=128000,
        ),
    ),

    _make_model(
        id=(TEST_MODEL_KEY := ModelKey('anthropic', 'claude-sonnet-5-5')),
        name='Claude Sonnet 5.5',

        short_ids=ModelShortIds(
            short_id='claude-sonnet',
            short_id_aliases=['sonnet', 'claude'],
        ),

        default_options=Options(
            max_tokens=128000,
        ),
    ),

    _make_model(
        id='claude-haiku-5-5',
        name='Claude Haiku 5.5',

        short_ids=ModelShortIds(
            short_id='claude-haiku',
            short_id_aliases=['haiku'],
        ),

        default_options=Options(
            max_tokens=64000,
        ),
    ),

]


# @om-manifest
_MODELS_MANIFEST = ModelsModuleManifest.of(__name__, MODELS)
