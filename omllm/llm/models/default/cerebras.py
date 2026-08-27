import typing as ta

from ...types.models import Model
from ...types.models import ModelKey
from ..modeldb import modeldb_token_pricing


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='cerebras',
            id='gpt-oss-120b',
        ),
        name='GPT OSS 120B',
        backend='openai-completions',
        pricing=modeldb_token_pricing('cerebras', 'gpt-oss-120b'),
        http=Model.Http(
            base_url='https://api.cerebras.ai/v1',
            extra_headers={
                'User-Agent': 'python-httpx/0.28.1',  # required or it 403's lol
            },
        ),
    ),

]
