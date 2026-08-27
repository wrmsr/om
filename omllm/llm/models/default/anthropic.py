"""
.
https://docs.anthropic.com/en/docs/about-claude/models#model-comparison-table
"""
import typing as ta

from ...types.compat import OpenaiCompat
from ...types.models import CacheCapabilities
from ...types.models import Model
from ...types.models import ModelKey
from ...types.options import CacheRetention
from ...types.options import Options
from ..manifests import ModelsModuleManifest
from ..modeldb import modeldb_token_pricing


##


MODELS: ta.Final[ta.Sequence[Model]] = [

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
        compat=OpenaiCompat(
            max_tokens_field='max_tokens',
        ),
        pricing=modeldb_token_pricing('anthropic', 'claude-sonnet-5'),
        http=Model.Http(
            base_url='https://api.anthropic.com/v1',
            extra_headers={
                'anthropic-version': '2023-06-01',
            },
        ),
        default_options=Options(
            max_tokens=4096,
        ),
    ),

]


# @om-manifest
_MANIFEST = ModelsModuleManifest.of(MODELS)
