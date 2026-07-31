import typing as ta

from ...types.compat import OpenaiCompat
from ...types.models import Model
from ...types.models import ModelKey


##


DEFAULT_OLLAMA_URL = 'http://localhost:11434/'


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='ollama',
            id='qwen3.5:2b',
        ),
        name='qwen3.5:2b',
        backend='openai-completions',
        compat=OpenaiCompat(
            url_path='/v1/chat/completions',
        ),
        http=Model.Http(
            base_url=DEFAULT_OLLAMA_URL,
        ),
    ),

    Model(
        key=ModelKey(
            provider='ollama',
            id='qwen3.6:27b',
        ),
        name='qwen3.6:27b',
        backend='openai-completions',
        compat=OpenaiCompat(
            url_path='/v1/chat/completions',
        ),
        http=Model.Http(
            base_url=DEFAULT_OLLAMA_URL,
        ),
    ),

]
