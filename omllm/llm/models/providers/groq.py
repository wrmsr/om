"""
.
https://console.groq.com/docs/models
"""
import typing as ta

from ....core.apikeys import secret_or_env_var_api_key
from ...types.models import Model
from ...types.models import ModelKey
from ..manifests import ModelsModuleManifest
from ..modeldb import modeldb_model_limits
from ..modeldb import modeldb_token_pricing


##


_API_KEYS = secret_or_env_var_api_key('groq_api_key')


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='groq',
            id='openai/gpt-oss-120b',
        ),
        name='GPT OSS 120B',
        short_ids=Model.ShortIds(
            short_id='groq',
        ),
        backend='openai-completions',
        limits=modeldb_model_limits('groq', 'openai/gpt-oss-120b'),
        pricing=modeldb_token_pricing('groq', 'openai/gpt-oss-120b'),
        http=Model.Http(
            base_url='https://api.groq.com/openai/v1',
            extra_headers={
                'User-Agent': 'python-httpx/0.28.1',  # required or it 403's lol
            },
        ),
        api_keys=_API_KEYS,
    ),

]


# @om-manifest
_MODELS_MANIFEST = ModelsModuleManifest.of(MODELS)
