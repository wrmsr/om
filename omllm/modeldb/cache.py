# ruff: noqa: SLF001
import compression.zstd
import itertools
import threading
import typing as ta

from omcore import check
from omcore import lang
from omcore.formats.json import all as json

from . import consts
from . import types


with lang.auto_proxy_import(globals()):
    from omcore import marshal as msh


Raw: ta.TypeAlias = ta.Mapping[str, ta.Any]


##


class _Cache:
    def __init__(self) -> None:
        super().__init__()

        self._lock = threading.RLock()

        self._resources = lang.get_relative_resources('_cache', globals=globals())

        self._primaries = {
            k
            for fn in self._resources
            if fn.endswith(consts._CACHE_FILE_SUFFIX)
            if (k := lang.must_remove_suffix(fn, consts._CACHE_FILE_SUFFIX)) != consts._OTHER_PROVIDERS_KEY
        }

        self._primary_providers_raw: dict[str, Raw] = {}
        self._other_providers_raw: ta.Mapping[str, Raw] | None = None

        self._providers: dict[str, types.Provider] = {}
        self._provider_models: dict[str, dict[str, types.Model]] = {}

    #

    def _load_raw(self, key: str) -> Raw:
        resource = self._resources[key + consts._CACHE_FILE_SUFFIX]
        return json.loads(compression.zstd.decompress(resource.read_bytes()))  # noqa

    def _get_other_providers_raw(self) -> ta.Mapping[str, Raw]:
        if (opr := self._other_providers_raw) is None:
            opr = check.isinstance(self._load_raw(consts._OTHER_PROVIDERS_KEY), ta.Mapping)
            self._other_providers_raw = opr

        return opr

    def _get_provider_raw(self, name: str) -> Raw:
        if name in self._primaries:
            try:
                return self._primary_providers_raw[name]
            except KeyError:
                pass

            raw = self._load_raw(name)

            self._primary_providers_raw[name] = raw
            return raw

        else:
            opr = self._get_other_providers_raw()
            return opr[name]

    def get_provider_raw(self, name: str) -> Raw:
        try:
            if name in self._primaries:
                return self._primary_providers_raw[name]
            elif (opr := self._other_providers_raw) is not None:
                return opr[name]
        except KeyError:
            pass

        with self._lock:
            return self._get_provider_raw(name)

    def get_provider_model_raw(self, provider_name: str, model_id: str) -> Raw:
        raw_provider = self._get_provider_raw(provider_name)
        return raw_provider.get('models', {})[model_id]

    #

    def _get_provider(self, name: str) -> types.Provider:
        check.not_equal(name, consts._OTHER_PROVIDERS_KEY)

        try:
            return self._providers[name]
        except KeyError:
            pass

        provider = msh.unmarshal(self._get_provider_raw(name), types.Provider)  # type: ignore[call-overload]

        self._providers[name] = provider
        return provider

    def get_provider(self, name: str) -> types.Provider:
        check.not_equal(name, consts._OTHER_PROVIDERS_KEY)

        try:
            return self._providers[name]
        except KeyError:
            pass

        with self._lock:
            return self._get_provider(name)

    def _get_provider_model(self, provider_name: str, model_id: str) -> types.Model:
        check.not_equal(provider_name, consts._OTHER_PROVIDERS_KEY)

        try:
            return self._provider_models[provider_name][model_id]
        except KeyError:
            pass

        try:
            provider = self._providers[provider_name]

        except KeyError:
            raw_model = self.get_provider_model_raw(provider_name, model_id)
            model = msh.unmarshal(raw_model, types.Model)  # type: ignore[call-overload]

        else:
            model = provider.models[model_id]

        self._provider_models.setdefault(provider_name, {})[model_id] = model
        return model

    def get_provider_model(self, provider_name: str, model_id: str) -> types.Model:
        check.not_equal(provider_name, consts._OTHER_PROVIDERS_KEY)

        try:
            return self._provider_models[provider_name][model_id]
        except KeyError:
            pass

        with self._lock:
            return self._get_provider_model(provider_name, model_id)

    #

    @lang.cached_function
    def get_all_provider_names(self) -> ta.Sequence[str]:
        return tuple(itertools.chain(
            self._primaries,
            self._get_other_providers_raw(),
        ))

    @lang.cached_function
    def get_all_provider_names_set(self) -> ta.AbstractSet[str]:
        return frozenset(self.get_all_provider_names())


#


@lang.cached_function(lock=True)
def _cache() -> _Cache:
    return _Cache()


def get_provider_raw(name: str) -> Raw:
    return _cache().get_provider_raw(name)


def get_provider_model_raw(provider_name: str, model_id: str) -> Raw:
    return _cache().get_provider_model_raw(provider_name, model_id)


def get_provider(name: str) -> types.Provider:
    return _cache().get_provider(name)


def get_provider_model(provider_name: str, model_id: str) -> types.Model:
    return _cache().get_provider_model(provider_name, model_id)


def get_all_provider_names() -> ta.Sequence[str]:
    return _cache().get_all_provider_names()


def get_all_provider_names_set() -> ta.AbstractSet[str]:
    return _cache().get_all_provider_names_set()
