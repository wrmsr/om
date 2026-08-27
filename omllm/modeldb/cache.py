import compression.zstd
import typing as ta

from omcore import lang
from omcore.formats.json import all as json


with lang.auto_proxy_import(globals()):
    from omcore import marshal as msh

    from . import types


##


@lang.cached_function()
def load_providers_raw() -> ta.Mapping[str, ta.Mapping[str, ta.Any]]:
    raw = lang.get_relative_resources(globals=globals())['cache.json.zstd'].read_bytes()
    data = compression.zstd.decompress(raw)
    return json.loads(data)


@lang.cached_function()
def load_providers() -> ta.Mapping[str, types.Provider]:
    return msh.unmarshal(load_providers_raw(), ta.Mapping[str, types.Provider])  # type: ignore[call-overload]


@lang.cached_function()
def load_provider(provider: str) -> types.Provider:
    raw = load_providers_raw()[provider]
    return msh.unmarshal(raw, types.Provider)  # type: ignore[call-overload]


@lang.cached_function()
def load_provider_model(provider: str, model_id: str) -> types.Model:
    raw = load_providers_raw()[provider]['models'][model_id]
    return msh.unmarshal(raw, types.Model)
