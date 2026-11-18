import typing as ta

from omcore import lang

from ...types.models import Model
from ..catalog import ModelCatalog
from ..catalog import _models_module_manifests
from ..defaults import DEFAULT_MODEL_SHORT_ID


_CHECKED_PLATFORMS: ta.Final[lang.SequenceNotStr[str]] = [
    'linux',
    'darwin',
]


def test_short_ids():
    for platform in _CHECKED_PLATFORMS:
        mc = ModelCatalog(
            _models_module_manifests(),
            platform=platform,
        )

        de = mc.by_short_id[DEFAULT_MODEL_SHORT_ID]
        assert isinstance(de.model(), Model)
