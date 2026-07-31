import typing as ta

from ...types.compat import OpenaiCompat
from ...types.models import Model
from ...types.models import ModelKey


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='ollama',
            id='qwen3.6:27b',
        ),
        name='qwen3.6:27b',
        backend='openai-completions',
        compat=OpenaiCompat(
            url_path='/chat',
            no_object_type_checks=True,
        ),
        http=Model.Http(
            base_url='http://localhost:11434/api',
        ),
    ),

]
