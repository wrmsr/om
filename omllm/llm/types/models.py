import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from .compat import Compat
from .options import CacheRetention
from .options import Options


CacheControlStyle: ta.TypeAlias = ta.Literal[
    'anthropic',
    'google_implicit',
    'openai_legacy',
    'openai_ttl',

    # Implicit upstream caching behind a load-balancing gateway - no request cache fields, but Options.cache_key is
    # translated to a session affinity header so repeat requests reach the same upstream (and thus its cache).
    'openrouter',
]


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class CacheCapabilities:
    # The provider request shape, including implicit-only providers which expose no request controls.
    control_style: CacheControlStyle

    # Exact retention policies which may be requested through Options.
    retentions: ta.AbstractSet[CacheRetention] = frozenset()

    # Whether Options.cache_key can be translated for this model.
    key: bool = False


##


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True, cache_hash=True)
class ModelKey:
    provider: str
    id: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.provider)
        check.non_empty_str(self.id)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class Model:
    key: ModelKey

    name: str | None = ''

    backend: str

    #

    compat: Compat | None = None

    #

    cache: CacheCapabilities | None = None

    #

    @ta.final
    @dc.dataclass(frozen=True, kw_only=True)
    @dc.extra_class_params(default_repr_fn=lang.opt_repr)
    class Http:
        base_url: str | None = None

        extra_headers: ta.Mapping[str, str] | None = None

    http: Http | None = None

    #

    default_options: Options | None = None
