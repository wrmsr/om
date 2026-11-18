import sys
import typing as ta

from omcore import collections as col
from omcore import lang
from omcore.manifests.globals import GlobalManifestLoader

from ..types.models import ModelKey
from ..types.models import ModelShortIds
from .manifests import ModelsModuleManifest


##


def _model_keys_by_short_id(
        dct: ta.Mapping[ModelKey, ModelShortIds],
        *,
        platform: str | None = None,
) -> ta.Mapping[str, ModelKey]:
    if platform is None:
        platform = sys.platform

    return col.make_map((
        (n, mk)
        for mk, si in dct.items()
        if (ip := si.include_platforms) is None or platform in ip
        if (ep := si.exclude_platforms) is None or platform not in ep
        for n in [si.short_id, *(si.short_id_aliases or [])]
        if n is not None
    ), strict=True)


##


@lang.cached_function
def model_short_ids_by_model_key() -> ta.Mapping[ModelKey, ModelShortIds]:
    mfs: ta.Sequence[ModelsModuleManifest] = GlobalManifestLoader.load_values(classes=[ModelsModuleManifest])

    return col.make_map((
        (mm.key, si)
        for mf in mfs
        for mm in mf.models
        if (si := mm.short_ids) is not None
    ), strict=True)


@lang.cached_function
def model_keys_by_short_id(
        *,
        platform: str | None = None,
) -> ta.Mapping[str, ModelKey]:
    return _model_keys_by_short_id(
        dct=model_short_ids_by_model_key(),
        platform=platform,
    )
