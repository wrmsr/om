import typing as ta

from ...types.models import Model
from ...types.models import ModelKey


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='google',
            id='gemini-3-flash-preview',
        ),
        name='Gemini 3 Flash Preview',
        backend='google-generative',
        http=Model.Http(
            base_url='https://generativelanguage.googleapis.com/v1beta',
        ),
    ),

]
