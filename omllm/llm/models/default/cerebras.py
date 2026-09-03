"""
.
https://inference-docs.cerebras.ai/models/overview
"""
import typing as ta

from ...types.models import Model
from ...types.models import ModelKey
from ..manifests import ModelsModuleManifest
from ..modeldb import modeldb_token_pricing


##


_BASE_URL = 'https://api.cerebras.ai/v1'

_DEFAULT_HTTP = Model.Http(
    base_url=_BASE_URL,
    extra_headers={
        'User-Agent': 'python-httpx/0.28.1',  # required or it 403's lol
    },
)


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='cerebras',
            id='gpt-oss-120b',
        ),
        name='GPT OSS 120B',
        backend='openai-completions',
        pricing=modeldb_token_pricing('cerebras', 'gpt-oss-120b'),
        http=_DEFAULT_HTTP,
    ),

    Model(
        key=ModelKey(
            provider='cerebras',
            id='qwen-3.8-27b',
        ),
        name='Qwen 3.8 27B',
        backend='openai-completions',
        pricing=modeldb_token_pricing('cerebras', 'qwen-3.8-27b'),
        http=_DEFAULT_HTTP,
    ),

]


# @om-manifest
_MANIFEST = ModelsModuleManifest.of(MODELS)
