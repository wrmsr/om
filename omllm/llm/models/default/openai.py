"""
https://developers.openai.com/api/docs/models/all
https://platform.openai.com/docs/models/compare
"""
import typing as ta

from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ...types.options import CacheRetention
from ..modeldb import modeldb_token_pricing


##


_BASE_URL = 'https://api.openai.com/v1'


MODELS: ta.Final[ta.Sequence[Model]] = [

    Model(
        key=ModelKey(
            provider='openai',
            id='gpt-5.6-sol',
        ),
        name='GPT 5.6 Sol',
        backend='openai-completions',
        cache=CacheCapabilities(
            control_style='openai_ttl',
            retentions=frozenset({
                CacheRetention.THIRTY_MINUTES,
            }),
            key=True,
        ),
        pricing=modeldb_token_pricing('openai', 'gpt-5.6-sol'),
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

    Model(
        key=ModelKey(
            provider='openai',
            id='gpt-5.6-terra',
        ),
        name='GPT 5.6 Terra',
        backend='openai-completions',
        cache=CacheCapabilities(
            control_style='openai_ttl',
            retentions=frozenset({
                CacheRetention.THIRTY_MINUTES,
            }),
            key=True,
        ),
        pricing=modeldb_token_pricing('openai', 'gpt-5.6-terra'),
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

    Model(
        key=ModelKey(
            provider='openai',
            id='gpt-5.6-luna',
        ),
        name='GPT 5.6 Luna',
        backend='openai-completions',
        cache=CacheCapabilities(
            control_style='openai_ttl',
            retentions=frozenset({
                CacheRetention.THIRTY_MINUTES,
            }),
            key=True,
        ),
        pricing=modeldb_token_pricing('openai', 'gpt-5.6-luna'),
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

    #

    Model(
        key=ModelKey(
            provider='openai',
            id='gpt-5.4-nano',
        ),
        name='GPT 5.4 Nano',
        backend='openai-completions',
        cache=CacheCapabilities(
            control_style='openai_legacy',
            retentions=frozenset({
                CacheRetention.IN_MEMORY,
                CacheRetention.ONE_DAY,
            }),
            key=True,
        ),
        pricing=modeldb_token_pricing('openai', 'gpt-5.4-nano'),
        http=Model.Http(
            base_url=_BASE_URL,
        ),
    ),

]
