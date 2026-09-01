"""
.
https://platform.claude.com/docs/en/models/overview
"""
import typing as ta

from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ...types.options import CacheRetention
from ...types.options import Options
from ..manifests import ModelsModuleManifest
from ..modeldb import modeldb_token_pricing


##


_BASE_URL = 'https://api.anthropic.com/v1'

_DEFAULT_HTTP = Model.Http(
    base_url=_BASE_URL,
    extra_headers={
        'anthropic-version': '2023-06-01',
    },
)


MODELS: ta.Final[ta.Sequence[Model]] = [
    Model(
        key=ModelKey(
            provider='anthropic',
            id='claude-fable-5.1',
        ),
        name='Claude Fable 5.1',
        backend='anthropic-messages',
        cache=CacheCapabilities(
            control_style='anthropic',
            retentions=frozenset({
                CacheRetention.FIVE_MINUTES,
                CacheRetention.ONE_HOUR,
            }),
        ),
        pricing=modeldb_token_pricing('anthropic', 'claude-fable-5'),
        http=_DEFAULT_HTTP,
        default_options=Options(
            max_tokens=128000,
        ),
    ),

    Model(
        key=ModelKey(
            provider='anthropic',
            id='claude-opus-5',
        ),
        name='Claude Opus 5',
        backend='anthropic-messages',
        cache=CacheCapabilities(
            control_style='anthropic',
            retentions=frozenset({
                CacheRetention.FIVE_MINUTES,
                CacheRetention.ONE_HOUR,
            }),
        ),
        pricing=modeldb_token_pricing('anthropic', 'claude-opus-5'),
        http=_DEFAULT_HTTP,
        default_options=Options(
            max_tokens=128000,
        ),
    ),

    Model(
        key=ModelKey(
            provider='anthropic',
            id='claude-sonnet-5',
        ),
        name='Claude Sonnet 5',
        backend='anthropic-messages',
        cache=CacheCapabilities(
            control_style='anthropic',
            retentions=frozenset({
                CacheRetention.FIVE_MINUTES,
                CacheRetention.ONE_HOUR,
            }),
        ),
        pricing=modeldb_token_pricing('anthropic', 'claude-sonnet-5'),
        http=_DEFAULT_HTTP,
        default_options=Options(
            max_tokens=128000,
        ),
    ),

    Model(
        key=ModelKey(
            provider='anthropic',
            id='claude-haiku-4-5-20251001',
        ),
        name='Claude Haiku 4.5',
        backend='anthropic-messages',
        cache=CacheCapabilities(
            control_style='anthropic',
            retentions=frozenset({
                CacheRetention.FIVE_MINUTES,
                CacheRetention.ONE_HOUR,
            }),
        ),
        pricing=modeldb_token_pricing('anthropic', 'claude-haiku-4-5-20251001'),
        http=_DEFAULT_HTTP,
        default_options=Options(
            max_tokens=64000,
        ),
    ),
]


# @om-manifest
_MANIFEST = ModelsModuleManifest.of(MODELS)
