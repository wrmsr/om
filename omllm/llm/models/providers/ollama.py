"""
.
https://console.groq.com/docs/models
"""
import typing as ta

from ...types.compat import OpenaiCompletionsCompat
from ...types.models import Model
from ...types.models import ModelKey
from ..manifests import ModelsModuleManifest


##


_DEFAULT_COMPAT = OpenaiCompletionsCompat(
    url_path='/v1/chat/completions',
)

_BASE_URL = 'http://localhost:11434/'

_DEFAULT_HTTP = Model.Http(
    base_url=_BASE_URL,
)


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    ##
    # qwen

    Model(
        key=ModelKey(
            provider='ollama',
            id='qwen3.5:2b',
        ),
        name='qwen3.5:2b',
        backend='openai-completions',
        compat=_DEFAULT_COMPAT,
        http=_DEFAULT_HTTP,
    ),

    Model(
        key=ModelKey(
            provider='ollama',
            id='qwen3.8:27b',
        ),
        name='qwen3.8:27b',
        short_ids=Model.ShortIds(
            short_id='ollama-qwen',
            short_id_aliases=['qwen'],
            exclude_platforms={'darwin'},
        ),
        backend='openai-completions',
        compat=_DEFAULT_COMPAT,
        http=_DEFAULT_HTTP,
    ),

    Model(
        key=ModelKey(
            provider='ollama',
            id='qwen3.8:27b-mlx',
        ),
        name='qwen3.8:27b-mlx',
        short_ids=Model.ShortIds(
            short_id='ollama-qwen',
            short_id_aliases=['qwen'],
            include_platforms={'darwin'},
        ),
        backend='openai-completions',
        compat=_DEFAULT_COMPAT,
        http=_DEFAULT_HTTP,
    ),

]


# @om-manifest
_MODELS_MANIFEST = ModelsModuleManifest.of(MODELS)
