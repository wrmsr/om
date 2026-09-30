import typing as ta

from omcore import lang

from .... import llm
from ..defaults import ALL_DEFAULT_MODELS
from ..defaults import default_models_by_name


_CHECKED_PLATFORMS: ta.Final[lang.SequenceNotStr[str]] = [
    'linux',
    'darwin',
]


def test_checked_platforms() -> None:
    for platform in _CHECKED_PLATFORMS:
        default_models_by_name(platform=platform)


def test_model_keys():
    mc = llm.provider_model_catalog()
    for m in ALL_DEFAULT_MODELS:
        assert m.key in mc
