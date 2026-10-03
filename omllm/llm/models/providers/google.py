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


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=(TEST_MODEL_KEY := ModelKey(
            provider='google',
            id='gemini-3.8-flash',
        )),
        name='Gemini 3.8 Flash',
        backend='google-generative',
        reasoning_efforts=frozenset({
            ReasoningEffort.MINIMAL,
            ReasoningEffort.LOW,
            ReasoningEffort.MEDIUM,
            ReasoningEffort.HIGH,
        }),
        # Gemini 2.5+ prompt caching is implicit and needs no generation-request field. Explicit caching instead uses
        # separately managed cachedContents resources, which are intentionally outside request Options for now.
        cache=CacheCapabilities(
            control_style='google_implicit',
        ),
        limits=modeldb_model_limits('google', 'gemini-3.8-flash'),
        pricing=modeldb_token_pricing('google', 'gemini-3.8-flash'),
        http=Model.Http(
            base_url='https://generativelanguage.googleapis.com/v1beta',
        ),
    ),

]


# @om-manifest
_MANIFEST = ModelsModuleManifest.of(MODELS)
