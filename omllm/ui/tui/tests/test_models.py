import typing as ta

from omcore import lang

from .... import llm
from ..models import ALL_MODELS
from ..models import models_by_name


_CHECKED_PLATFORMS: ta.Final[lang.SequenceNotStr[str]] = [
    'linux',
    'darwin',
]


def test_checked_platforms() -> None:
    for platform in _CHECKED_PLATFORMS:
        models_by_name(platform=platform)


def test_model_keys():
    mc = llm.default_model_catalog()
    for m in ALL_MODELS:
        assert m.key in mc
