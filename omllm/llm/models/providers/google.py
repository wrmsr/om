"""
.
https://ai.google.dev/gemini-api/docs/models
"""
import typing as ta

from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ...types.options import ReasoningEffort
from ..manifests import ModelsModuleManifest
from ..modeldb import modeldb_model_limits
from ..modeldb import modeldb_token_pricing


##


_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta'


def _make_model(
        *,
        id: str,  # noqa
        name: str,

        **kwargs: ta.Any,
) -> Model:
    return Model(
        key=ModelKey(
            provider='google',
            id=id,
        ),
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

                limits=modeldb_model_limits('google', id),
                pricing=modeldb_token_pricing('google', id),

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
        id='gemini-4-argon',
        name='Gemini 4 Argon',
    ),

    _make_model(
        id=(TEST_MODEL_KEY := ModelKey('google', 'gemini-3.8-flash')).id,
        name='Gemini 3.8 Flash',
    ),

    _make_model(
        id='gemini-2.5-flash',
        name='Gemini 2.5 Flash',
    ),

    _make_model(
        id='gemini-2.5-flash-lite',
        name='Gemini 2.5 Flash Lite',
    ),

]


# @om-manifest
_MANIFEST = ModelsModuleManifest.of(MODELS)
