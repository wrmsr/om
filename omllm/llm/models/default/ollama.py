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


MODELS: ta.Final[ta.Sequence[Model]] = [

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
        backend='openai-completions',
        compat=_DEFAULT_COMPAT,
        http=_DEFAULT_HTTP,
    ),

]


# @om-manifest
_MANIFEST = ModelsModuleManifest.of(MODELS)
