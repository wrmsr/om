"""
.
https://console.groq.com/docs/models
"""
import typing as ta

from ...types.models import Model
from ...types.models import ModelKey
from ..modeldb import modeldb_token_pricing


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='groq',
            id='openai/gpt-oss-120b',
        ),
        name='GPT OSS 120B',
        backend='openai-completions',
        pricing=modeldb_token_pricing('groq', 'openai/gpt-oss-120b'),
        http=Model.Http(
            base_url='https://api.groq.com/openai/v1',
            extra_headers={
                'User-Agent': 'python-httpx/0.28.1',  # required or it 403's lol
            },
        ),
    ),

]
