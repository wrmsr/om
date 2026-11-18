"""
.
https://inference-docs.cerebras.ai/models/overview
"""
import typing as ta

from ....core.apikeys import secret_or_env_var_api_key
from ...types.models import Model
from ...types.models import ModelKey
from ..manifests import ModelsModuleManifest
from ..modeldb import modeldb_model_limits
from ..modeldb import modeldb_token_pricing


##


_BASE_URL = 'https://api.cerebras.ai/v1'

_DEFAULT_HTTP = Model.Http(
    base_url=_BASE_URL,
    extra_headers={
        'User-Agent': 'python-httpx/0.28.1',  # required or it 403's lol
    },
)

_API_KEYS = secret_or_env_var_api_key('cerebras_api_key')


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='cerebras',
            id='gpt-oss-120b',
        ),
        name='GPT OSS 120B',
        short_ids=Model.ShortIds(
            short_id='cerebras-gpt',
            short_id_aliases=['cerebras'],
        ),
        backend='openai-completions',
        limits=modeldb_model_limits('cerebras', 'gpt-oss-120b'),
        pricing=modeldb_token_pricing('cerebras', 'gpt-oss-120b'),
        http=_DEFAULT_HTTP,
        api_keys=_API_KEYS,
    ),

    Model(
        key=ModelKey(
            provider='cerebras',
            id='qwen-3.8-27b',
        ),
        name='Qwen 3.8 27B',
        backend='openai-completions',
        limits=modeldb_model_limits('cerebras', 'qwen-3.8-27b'),
        pricing=modeldb_token_pricing('cerebras', 'qwen-3.8-27b'),
        http=_DEFAULT_HTTP,
        api_keys=_API_KEYS,
    ),

]


# @om-manifest
_MODELS_MANIFEST = ModelsModuleManifest.of(MODELS)
