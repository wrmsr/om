import typing as ta

from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ..modeldb import modeldb_token_pricing


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='google',
            id='gemini-3-flash-preview',
        ),
        name='Gemini 3 Flash Preview',
        backend='google-generative',
        # Gemini 2.5+ prompt caching is implicit and needs no generation-request field. Explicit caching instead uses
        # separately managed cachedContents resources, which are intentionally outside request Options for now.
        cache=CacheCapabilities(
            control_style='google_implicit',
        ),
        pricing=modeldb_token_pricing('google', 'gemini-3-flash-preview'),
        http=Model.Http(
            base_url='https://generativelanguage.googleapis.com/v1beta',
        ),
    ),

]
