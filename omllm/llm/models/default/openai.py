import typing as ta

from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ...types.options import CacheRetention


##


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='openai',
            id='gpt-5.4-mini',
        ),
        name='GPT 5.4 Mini',
        backend='openai-completions',
        cache=CacheCapabilities(
            control_style='openai_legacy',
            retentions=frozenset({
                CacheRetention.IN_MEMORY,
                CacheRetention.ONE_DAY,
            }),
            key=True,
        ),
        http=Model.Http(
            base_url='https://api.openai.com/v1',
        ),
    ),

]
