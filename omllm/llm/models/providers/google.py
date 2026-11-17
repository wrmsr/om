"""
.
https://ai.google.dev/gemini-api/docs/models
"""
import typing as ta

from ....core.apikeys import secret_or_env_var_api_key
from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ...types.options import ReasoningEffort
from ..manifests import ModelsModuleManifest
from ..modeldb import modeldb_model_limits
from ..modeldb import modeldb_token_pricing


##


_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta'

_API_KEYS = secret_or_env_var_api_key('gemini_api_key')


##


def _make_model(
        *,
        id: str | ModelKey,  # noqa
        name: str,

        **kwargs: ta.Any,
) -> Model:
    key = id if isinstance(id, ModelKey) else ModelKey(
        provider='google',
        id=id,
    )

    return Model(
        key=key,
        name=name,

        **{
            **dict(
                backend='google-generative',

                # The thinkingLevel enum also has MINIMAL, but this model rejects it with "Thinking level MINIMAL is not
                # supported for this model" (verified against the live API).
                reasoning_efforts=frozenset({
                    ReasoningEffort.LOW,
                    ReasoningEffort.MEDIUM,
                    ReasoningEffort.HIGH,
                }),

                # Gemini 2.5+ prompt caching is implicit and needs no generation-request field. Explicit caching instead
                # uses separately managed cachedContents resources, which are intentionally outside request Options for
                # now.
                cache=CacheCapabilities(
                    control_style='google_implicit',
                ),

                limits=modeldb_model_limits('google', key.id),
                pricing=modeldb_token_pricing('google', key.id),

                http=Model.Http(
                    base_url=_BASE_URL,
                ),

                api_keys=_API_KEYS,
            ),

            **kwargs,
        },
    )


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    _make_model(
        id='gemini-4-carbon',
        name='Gemini 4 Carbon',

        short_id='gemini-carbon',
        short_id_aliases=['carbon'],
    ),

    _make_model(
        id='gemini-4-argon',
        name='Gemini 4 Argon',

        short_id='gemini-argon',
        short_id_aliases=['argon'],
    ),

    _make_model(
        id='gemini-4-hydrogen',
        name='Gemini 4 Hydrogen',

        short_id='gemini-hydrogen',
        short_id_aliases=['hydrogen'],
    ),

    _make_model(
        id=(TEST_MODEL_KEY := ModelKey('google', 'gemini-3.8-flash')),
        name='Gemini 3.8 Flash',

        short_id='gemini-flash',
        short_id_aliases=['gemini', 'google'],
    ),

    _make_model(
        id='gemini-2.5-flash-lite',
        name='Gemini 2.5 Flash Lite',

        short_id='gemini-cheap',
    ),

]


# @om-manifest
_MODELS_MANIFEST = ModelsModuleManifest.of(MODELS)
