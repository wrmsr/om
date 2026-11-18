import typing as ta

from omcore import lang

from .... import llm
from ..shortids import model_keys_by_short_id


_CHECKED_PLATFORMS: ta.Final[lang.SequenceNotStr[str]] = [
    'linux',
    'darwin',
]


def test_model_keys():
    mc = llm.provider_model_catalog()
    for platform in _CHECKED_PLATFORMS:
        for mk in model_keys_by_short_id(platform=platform).values():
            assert mk in mc.by_key
